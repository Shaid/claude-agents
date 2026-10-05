# "Publish only the busiest track" is a corpus-specific shortcut, not a property of the container shape

**When it bites:** publishing a representative frame/cel/pose from a
multi-track animation or layer structure (several parallel channels per
clip: draw groups, animation tracks, layers) where an already-working
heuristic for one format picks only the single busiest/most-populated track
and ignores the rest — and you're about to reuse that same heuristic
unmodified for a structurally identical sibling format (same container,
same track/clip architecture, ported to a different platform or game). The
result renders without error and looks like *something*, which is exactly
what makes an incomplete result easy to miss without comparing against the
real asset.

## What went wrong

Confirmed on Dragon's Crown (PS3, `vanille`), publishing sprite models from
the newly-decoded `FMBS` format (`tools/shared/fmbp.ts`, `cpk-models.ts`).
The already-working publisher for `FMBP` (Odin Sphere/Grim Grimoire's PS2
sibling, `cvm-models.ts`) picks, for each clip, only the single draw-group
"track" with the most draws — because in that corpus a clip's other tracks
are near-universally placeholder slots pointing at empty (0-part) frames, a
fixed-track-count-per-clip convention with only one real track in use. That
heuristic was reused unmodified for `FMBS`, which shares the exact same
clip → draw-group → draw → frame hierarchy byte-for-byte in role and
position.

It silently under-rendered. `character/Flask00.mbs`'s `IDEL` (idle) clip has
**multiple simultaneously-meaningful tracks** — the glass flask body, a wisp
of rising smoke, drip effects — not one real track plus placeholders.
Picking only the busiest track produced a small, disconnected smoke-wisp
fragment as the published "model," with no error, no empty-render warning,
and no structural invariant it violated (the fragment itself decoded
perfectly cleanly). The bug was only caught by looking at the rendered PNG
directly and noticing it didn't look like the object the filename named —
if it hadn't been visually inspected, "Flask00.png" would have shipped as a
disconnected smoke puff forever.

## The fix, generalized

A cel/pose-selection heuristic derived from one format's *typical content
distribution* (most tracks are placeholders, so the busiest one is safe to
treat as "the real content") is a fact about that corpus, not a guarantee
of the container *format*. A structurally identical sibling format — same
byte layout, same hierarchy, same field roles — can have a genuinely
different content-authoring convention on top of that shared structure
(parallel, all-meaningful tracks instead of one-real-plus-placeholders).
Verify the assumption directly on the new corpus (are the non-busiest
tracks actually near-empty placeholders, or do they carry real independent
content?) before reusing a "pick the best one" heuristic; when tracks
genuinely are independent parallel content — not competing/alternate
choices — the correct move is to **union** every track's contribution into
one composited result, not to pick a winner. This is the same underlying
trap as `header-field-role-not-transitive-across-sibling-format.md` (a
shared container doesn't guarantee a shared inner layout) and
`sibling-format-shares-field-position-not-numeric-scale-convention.md` (nor
a shared numeric convention) — one more axis, generalized: a shared
container also doesn't guarantee a shared *authoring/content convention*
built on top of that layout, and a publishing heuristic tuned to one game's
convention is exactly the kind of assumption that survives silently until
someone looks at the actual picture.
