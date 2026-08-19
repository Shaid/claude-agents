# An always-full-run pipeline's upsert-by-name manifest merge accumulates stale entries forever, unbounded

**When it bites:** a `finalizeManifest`-style step does an upsert-by-name
merge against whatever `manifest.json` is already on disk, and the producer
function it follows (texture/mesh/audio pass, etc.) always runs as one
complete, all-or-nothing invocation — no scoped/partial-rerun mode, no
resumed-from-disk items relying on the merge to survive, no second
independent tool populating entries this step doesn't know about. Also when
it bites the other way: a sibling asset-type stage's manifest entries
(mesh/audio/etc) vanish after a pipeline run, especially a pure no-op
resume with 0 newly-visited files — see the type-filtered-merge variant
below.

Confirmed on Drakengard 2 (PS2, `flower` project,
`tools/shared/cavia-pipeline.ts`): rebuilding the pipeline after an
unrelated shared-code fix changed the container-walk order (a `\0V3a`
decompression wrapper wired into `walkCaviaContainer`) produced a manifest
with **23,449** texture entries even though the run's own log reported
decoding exactly **12,348**. The old `manifest.json` (8 days older, built
before the container-walk-order change) had ~11,000 texture entries whose
names — derived positionally/sequentially from container-walk order — no
longer matched anything the current code produces. Because the merge only
*adds* entries under names it doesn't already have, and never prunes
entries the current run didn't touch, those orphaned old-scheme names just
piled up forever, doubling the manifest with dead rows pointing at content
that may not even exist on disk anymore. This is a **different** failure
mode from `content-addressed-manifest-merge-needs-source-precedence.md`
(two *concurrent* sources overwriting each other under a shared name) — this
is a *temporal* staleness bug: one source, merging against its own past.

**The fix, and the audit method that finds every instance of it**: grep the
codebase for the upsert-by-name idiom (`new Map(existing...)`,
`byName.set(...)`, `Map<string, ManifestEntry>`) and, for each hit, ask two
structural questions about the producer function that feeds it — not "does
it have an env var" (several genuinely-safe pipelines have env vars for
unrelated reasons, like a `LIMIT`/`maxNewTextures` truncation knob that's
just a smaller/faster dev run, not a scoped rerun):

1. **Does the producer always accumulate one complete run's worth of
   entries into a single local array before ever calling finalize** — no
   per-invocation truncation that leaves permanent gaps in what this
   invocation's array covers?
2. **Does anything else legitimately populate `manifest.json` entries that
   THIS invocation's local array will never contain** — a separate
   independent tool/pipeline (e.g. a Python FMV extractor promoting `video`
   entries a TS texture/mesh/audio pass never reproduces), a genuinely
   skippable sibling content-type stage (env-var-gated, e.g.
   `NIERAUTOMATA_SKIP_TEXTURES` for an audio-only re-run that must not drop
   the texture entries from a prior full run), or a resumed/already-on-disk
   item whose producer *deliberately* skips re-pushing it to the in-memory
   array (trusting the merge to keep it, for a memory-bounded multi-process
   batched-rerun workflow)?

**A third, opposite-looking failure mode shares this same root cause and
audit method: a merge that correctly recognizes question 2 is "yes" can
still be mis-scoped, silently dropping the very sibling-stage entries it
exists to protect — on every single run, including a pure no-op resume with
zero newly-visited files.** Confirmed twice independently in the same
session (Chimera project, both hit by different concurrent agents): a
texture stage's merge read `manifest.json` and kept only `prior.filter(e =>
e.type === 'texture')` before appending its own new entries, then
unconditionally `writeJson`'d that filtered set at the end — regardless of
whether the run found any new files to process. Once a sibling mesh stage
was wired to run after it in the same pipeline invocation (`buildAssets()`
then `buildMeshes()` against one shared `manifest.json` — see
`docs/fe-warriors.md`/`docs/fe-threehouses.md`), the very next pipeline run
(a full no-op resume, 0 new files either stage) silently deleted every
`type: 'mesh'` entry the prior run had written, because the texture stage's
filter never preserved them. This is easy to miss precisely because "0 new
files visited" reads as "nothing happened, safe" — the unconditional final
write still fires and still narrows the kept set. The fix is the same
upsert-by-name pattern as the correct instances in the main lesson above,
just applied without a type filter: `if (e.type !== 'texture' ||
!priorNames.has(e.name)) keep it`. Verify by running the *documented*
multi-stage entrypoint (not each stage's own standalone script) two or
three times in a row on an already-fully-extracted corpus and confirming
every stage's entry count is unchanged after each run — a single run
finishing "clean" proves nothing, since the bug only shows up on the
*second* run once the first run's own write has already narrowed the set.

If (2) is **no** for every real caller, the merge is pure liability — always
overwrite with a fresh, non-merging `writeJson(manifestPath, manifest)`
using the run's own complete array, no disk read at all. If (2) is **yes**
for any real reason, the merge must stay (and ideally gets a doc comment
naming *why*, so the next audit doesn't misclassify it) — an unconditional
"just always fresh-write" sweep would be exactly as wrong as the original
bug, just in the opposite direction: it would silently delete the very
entries the merge exists to protect. On this audit (12 files with the
identical merge idiom), 6 were the genuine bug and got fresh-written; 3
(Drakengard 3's own pre-existing, correct implementation aside) needed the
merge kept for three different concrete reasons matching each branch of
question 2 above — confirmed for one of them (a Chaos Legion rebuild) by
checking that its 17 externally-produced `video` manifest entries survived
a TS-only pipeline rerun byte-for-byte via the merge, while every entry
type the TS step *does* produce matched its own log-reported count exactly
with zero excess. Verify the fix the same way in general: after a real
full-corpus rebuild, `manifest.json`'s per-type entry counts must equal
exactly what the run's own console log reported decoding — any excess is
this bug (or its opposite).
