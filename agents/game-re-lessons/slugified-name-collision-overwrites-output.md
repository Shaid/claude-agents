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
