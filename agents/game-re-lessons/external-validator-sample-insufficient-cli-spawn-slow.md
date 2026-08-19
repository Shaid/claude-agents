# A handful of samples through an external validator CLI misses corpus-wide edge cases; the CLI is also too slow to run on everything

**When it bites:** using a standard-format's own reference validator (glTF
validator, a PNG/WAV conformance checker, etc.) as a conformance oracle —
see the "standard-codec-delegate-to-trusted-decoder" pattern in the main
Method — against a corpus of hundreds of generated files, via its `npx`/CLI
entrypoint on a handful of hand-picked samples.

## What went wrong

`npx @gltf-transform/cli validate <file>.glb` on 8-10 hand-picked samples
out of a 461-file GLB corpus (Fire Emblem Warriors G1M mesh export) all
passed clean. Running the full 461-file corpus through the same CLI,
one invocation per file, surfaced **3 additional distinct real bugs** that
the small sample had missed entirely: an out-of-bounds joint index on a
handful of small (3-bone) weapon/prop skeletons, a literal `NaN` in one
decoded vertex position, and a zero-length `NORMAL` vector in the same
file. None of these were rare in an absolute sense (each affected file was
visibly different in kind — tiny-skeleton weapon props vs. a full character
model) but they were each confined to a small fraction of the corpus, easy
to miss by chance in any sample under a few dozen files.

Compounding this: spawning the validator CLI once per file pays full
`npm`/`npx` package-resolution overhead every time (~1-2s per file even
though the actual validation work is fast), so a full-corpus sweep this
way is slow enough (minutes, not seconds) that it's tempting to launch it
in the background and move on — which in this session led to several
uncoordinated `&`-backgrounded shell invocations from repeated retries
silently stacking up and running the same 461-file sweep concurrently,
burning CPU for no benefit and producing confusing/empty log output while
alive.

## Second confirmed instance (different exporter, different bug shapes)

Astral Chain (Switch) WMB3→GLB exporter (`wmb-gltf.ts`/`gltf-builder.ts`,
unrelated code to the FE Warriors G1M exporter above, built on a shared
low-level GLB-assembly helper both exporters use): a hand-picked 5-file
sample, and separately a **40-file random sample**, both validated 0
errors. The full 1,815-file corpus surfaced two more distinct real bugs:
(1) `gltf-builder.ts`'s `assembleGLB()` serialized empty `materials`/
`meshes` arrays as `[]` instead of omitting the property — spec-invalid
(`EMPTY_ENTITY`), but only triggered by placeholder/all-empty source files,
so a sample of normal-content files can't find it by chance; (2) a
single-root skeleton (the common case — one root bone, not several) was
never attached to `scene.nodes`, only the multi-root synthesized-wrapper
case was, orphaning every skin's joints from the scene graph
(`NODE_SKIN_NO_SCENE`) despite the mesh/skin nodes themselves being
correctly in the scene — this affected the *majority* of the corpus and a
40-file random sample still didn't happen to reveal it, because the
validator's error report doesn't surface until you actually run it, and no
smaller check (bbox cross-reference, bone-index range check) would have
caught a scene-graph-attachment omission specifically. Confirms this isn't
a one-off risk tied to one team's exporter code — it's a property of
"validate a sample" as a method, independent of which bugs happen to exist
in a given codebase.

## The fix

The CLI (`@gltf-transform/cli`) is usually a thin wrapper around an
importable library that does the real validation in-process — for glTF,
`gltf-validator`'s `validateBytes()` (reachable straight from the npm/npx
package cache, e.g. `~/.npm/_npx/<hash>/node_modules/gltf-validator/
module.mjs`, no separate install needed if the CLI was already run once).
Writing a ~20-line Node script that loops over every file in one long-lived
process and calls the library function directly turned a multi-minute,
process-spawning batch into a few-seconds run, with structured JSON error
output (trivial to grep/aggregate) instead of a colored terminal table
meant for one-file-at-a-time human reading. Apply this pattern to any
standard-format conformance check run at real corpus scale (hundreds+
files): check whether the CLI tool's own `node_modules` exposes a
programmatic entrypoint before accepting "loop a CLI subprocess per file"
as the batch-verification method — and always run the *full* corpus through
whichever method is fast enough to afford it, not a sample, since the
counter-evidence above shows a small sample can pass 100% clean while real,
distinct bugs sit in the untested majority.
