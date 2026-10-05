# A "first usable/non-empty" fallback heuristic assumes a reserved slot is empty — a sibling format's reserved slot may be real, named, non-empty content instead

**When it bites:** a "pick the best default/representative item" selector
tries an exact-name match first, then falls back to "the first item with any
real content at all" — and a sibling format in the same engine family
reserves that same slot-0 (or otherwise conventionally-first) position for
a *named*, deliberately non-empty placeholder rather than an all-zero one.
Related to, but distinct from, `tile-bank-index-zero-not-universally-a-
placeholder.md` (that one is about byte-range *addressing* arithmetic; this
one is about a *content-emptiness* assumption baked into a fallback
heuristic).

Confirmed on Muramasa: The Demon Blade (Wii, `vanille`)'s `FMBS`
sprite-model animation clips. The idle-clip picker
(`fmbpIdleClipIndex`/`fmbsIdleClipIndex` in `tools/shared/fmbp.ts`) first
tries an exact (case-insensitive) match against a small list of
conventional idle-clip names, then falls back to `firstUsableClip` — the
first clip with any renderable content — on the reasoning that a format's
clip 0 is normally an all-zero/empty placeholder (true for PS2 `FMBP` and
PS3 `FMBS`, both already confirmed). Muramasa's own clip 0 is
conventionally named `DUMMY` and is **not** empty — it has real, renderable
content — so for any model whose actual idle clip wasn't already in the
exact-name list, the fallback silently picked `DUMMY` as "idle" instead.
This didn't crash or throw; it just rendered a plausible-looking but wrong
default frame, the kind of defect only a direct visual inspection catches.

**The fix, generalized:** add a middle fallback tier between "exact name
match" and "first non-empty slot" — here, a substring match (any clip name
*containing* "IDLE") that fires before the last-resort emptiness-based
fallback, catching the sibling title's own directional/suffixed naming
variants (`R_IDLE_A`, `L_IDLE_A`, `IDLE_A_START_A`) without needing to
enumerate every one by exact name. More generally: before trusting a
"first non-empty/usable X" fallback on a new sibling format, check whether
that format's own conventionally-reserved first slot is actually empty —
if it has a real, consistently-named placeholder instead (here, literally
named `DUMMY`), the fallback needs a smarter middle tier, not just a wider
exact-match list.
