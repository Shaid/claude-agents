# A filename slugified from a human-readable label can silently collide

**When it bites:** a pipeline step derives an output filename (or any other
supposedly-unique key) from an in-game display name/label via a
`slugify()`-style normalization (lowercase, strip punctuation, collapse to
hyphens) — for a batch of names that only differ by punctuation or case, not
by an ID.

Confirmed: a script generating one recolored sprite sheet per named
character grouped in-game entity names and slugified them for the output
filename. `"GANDALF"` and `"GANDALF'"` (the White) both slugify to
`gandalf` once the apostrophe is stripped; two structurally distinct
"Southrons" army groups likewise both slugified to `southrons`. Nothing in
the pipeline checked for duplicate output paths, so the second write of
each pair **silently overwrote the first's PNG** — no error, no warning, no
count mismatch anywhere visible short of opening the file and finding the
wrong character's colors in it. Caught only by an explicit post-generation
check: `len(set(output_paths)) == len(entries)`.

**The fix:** whenever a filename/slug is derived from a human-readable label
rather than a value already guaranteed unique (an index, an ID, a database
key), either (a) include the guaranteed-unique discriminator in the slug
too (here: the character's `SAS` index, which is unique by construction
within the grouping), or (b) explicitly assert uniqueness across all
generated output paths right after generation and fail loudly on a
collision, rather than trusting that visually-distinct source strings will
stay distinct after normalization. Do this check by default for any
label-derived batch of filenames — it costs one line and catches a class of
bug that produces no symptom other than quietly-wrong content in a file
that otherwise looks completely valid.

**A second instance, different root cause, same symptom: two different
pipeline *steps* deriving a name from the same source key, not two
different labels colliding after normalization.** Confirmed on NieR:
Automata (PC)'s mesh pipeline (`~/Development/flower`,
`tools/nierautomata/build-assets.ts`): a texture-extraction step and a
mesh-extraction step both independently derive a manifest entry's `name`
from the exact same `(dirName, fileName)` pair of one source `.dtt`
archive entry (e.g. `wd1/g10722.dtt`, which genuinely contains both a real
texture sub-resource and a real mesh sub-resource) via the *same*
`slugName()` helper — with no punctuation/case ambiguity at all, just two
different asset *types* sharing one filename-derived key. The shared
upsert-by-name manifest merge silently dropped whichever entry got pushed
second. Caught only by a smoke-test run showing the manifest's total entry
count hadn't grown after adding a whole new asset type — not by any
per-name uniqueness check, since each *individual* pipeline step's own
`usedNames` collision-avoidance set is local to that step and never sees
the other step's names. **Fix, generalized**: whenever more than one
pipeline step can independently produce a manifest entry from the same
underlying source key (file/entry name, object ID), include the asset
*type* in the derived name (e.g. a `_mesh`/`_texture` suffix) — a
uniqueness check scoped to one step's own `usedNames` set cannot catch a
cross-step collision; the discriminator has to be baked into the name
itself.

**A third instance, different root cause again: naming an output file by
only a source path's *basename*, discarding the directory structure that
was the actual uniqueness source.** Confirmed on Fire Emblem: Engage
(`chimera`, Unity Addressables mesh export): an early version of
`extract_unity_meshes.py` named each bundle's output JSON by
`Path(bundle_path).stem` alone. Checking for real collisions before
trusting this at full-corpus scale (`find ... | xargs -n1 basename | sort
| uniq -d`) found **1,685 duplicate basenames across 24,755 bundle
paths** — many different top-level asset categories each ship their own
`bg.bundle`, `acc.bundle`, etc., distinguished only by their directory
path, which the stem-only key threw away. Caught before any real damage
(checked proactively, not discovered via a missing-output symptom) by
running exactly that dedup-count check against the full file listing
before trusting the naming scheme at scale — the general habit worth
repeating for *any* filename-key scheme on a large corpus, not just this
one. **Fix**: use the full relative path (with directory separators
replaced by a safe delimiter, e.g. `__`) as the naming key whenever a
corpus can plausibly have same-named leaves in different directories —
which is the common case for any per-directory-category asset layout,
not a special case to special-case around.

**A fourth instance, different root cause again: stripping a trailing
"extension" that is really a sequence-number discriminator, not a format
suffix.** Confirmed on Reunion (Amnesty Design, Amiga AGA, `methanoid`
project): an asset-naming helper derived each output name from
`basename(filePath).replace(/\.[^.]+$/, '')` — a completely standard
"strip the extension" idiom, reasonable for the vast majority of the
corpus. But this game's animation-frame files use numeric "extensions" as
their real per-frame discriminator (`ATVEZETO.002`...`ATVEZETO.016`, 15
files; `RESOUNDS.001`...`RESOUNDS.079`, 80 files) — stripping them
collapsed each whole numbered run onto one shared output name, silently
overwriting all but the last file written. Caught the same way as
instance one: comparing the pipeline's own claimed output count ("277
image(s)") against the real on-disk file count (264) and a per-type WAV
count (1 instead of 80) — not by any uniqueness assertion, since none
existed yet. **Fix**: don't assume "the part after the last dot" is a
discardable format extension at all — for a numbered-sequence family it's
load-bearing content. Keep the full basename (replace dots with a safe
delimiter rather than truncating at the first/last one) as the naming key
by default, and only strip a trailing extension when you've confirmed via
the corpus itself (do sibling files share every other extension value, or
is this file's "extension" numeric/ordinal and unique per file?) that it's
safe to discard.

**A fifth instance, different root cause again: naming manifest entries
by a coarse shared category label instead of each source file's own
unique stem, specifically where most instances fall back to a generic
per-item name.** Confirmed on Dragon's Crown (PS3, `vanille` project,
`tools/shared/acb-music.ts`): a stage publishing ~211 CRI ACB audio banks
named each resolved track `${spec.group}_${t.name}`, where `group` is a
coarse category (`bgm`/`narration`/`se`) shared by dozens to hundreds of
banks and `t.name` falls back to a generic per-ACB-relative index
(`waveform_0`, `waveform_1`, ...) whenever the bank's cue graph doesn't
resolve a real name — true for all 203 `se_*.acb` banks in this corpus.
Every one of those banks independently produced tracks named
`se_waveform_0`, `se_waveform_1`, ... — identical names across banks with
completely different real audio content — and the upsert-by-name manifest
merge silently kept only the last-processed bank's tracks under each
colliding name. The bug was doubly hidden: the pipeline's own stdout
correctly reported "12281 tracks" resolved (the per-bank resolution logic
was fine), but only 6421 survived in the actual `manifest.json` — a
plausible-looking, nonzero, *wrong* final count with no error anywhere.
**Fix**: key the manifest name on the source file's own unique filename
stem (`se_enemy103000_v_waveform_0`), not the coarse classification label
alone; keep the coarse label as a separate `group` field for browsing/
filtering. Generalizes to any pipeline stage that upserts many generated
entries by name from multiple source files sharing a naming convention
with a generic, non-unique per-item fallback identifier — audio banks
here, but the same shape applies to any "many small self-similar
containers, each independently falling back to `item_0`/`item_1`-style
names" scenario. Verify by checking the manifest's final per-category
entry count against the pipeline's own reported resolution count exactly,
not just confirming the run exits cleanly.
