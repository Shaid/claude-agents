# A structural recipe can re-match itself a few bytes inside its own real hit — sort and greedily dedup by non-overlap

**When it bites:** A structural/recipe-based scan for a repeating record type
(e.g. "find a relocated longword pointing at a known record, back up by a
fixed header size, validate a count field plus N consecutive relocated
descriptor slots") returns more hits than expected, and a look at the extra
ones shows each is a tiny, otherwise-valid-looking `n=0`-or-similar match
whose start offset lands a handful of bytes *inside* an already-accepted,
larger real match — not scattered randomly through the file, and not an
obviously-different unrelated resource type.

## What went wrong

Desert Strike's per-entity-type "template" array (`tools/desertstrike/
mission-bank.ts`, `findMissionBankTemplates`) is found by scanning a hunk's
own `HUNK_RELOC32` self-relocation table for a relocated slot at
`offset+0x3A` pointing at a valid record, then validating a plausible
sub-object count and N consecutive relocated descriptor pointers starting
there. Applied naively (as literally described by an earlier session's own
prose), this recipe over-counted: real templates themselves contain
internal relocated pointer fields (`+0x1E`/`+0x22`/`+0x26`/`+0x3A[i]`), and
one of those fields can *itself* satisfy the exact same recipe re-anchored
at that field's own position — producing a spurious `n=0` "ghost" template
wholly contained inside the real template's own byte range (e.g. a false
hit at `0x206dc`, nested a few bytes inside the real player template's
confirmed start at `0x206d4`).

This is a different shape from two already-documented related pitfalls:
`shared-header-template-cross-resource-false-positive.md` covers a
generic-shaped record header matching an *unrelated* resource type
elsewhere in the file, and `overlapping-strict-matches-both-verify.md`
covers two independently-valid, non-nested candidate placements that both
genuinely decode as real content (a true ambiguity, left open). Here the
false hit isn't a different resource, and it isn't independently valid on
its own merits — it exists *only* because the recipe is self-referential
(the record type's own internal fields have the same shape the recipe
searches for), and it is always strictly nested inside a real hit, never
free-standing.

## The fix

Collect every raw candidate the recipe matches (don't reject any yet), sort
them by start offset, then walk left to right accepting a candidate only if
its start offset is at or past the previous *accepted* candidate's end.
This deterministically discards every nested ghost (since a nested match's
start always falls strictly before its container's end) while keeping every
real, non-overlapping record — no count threshold, size heuristic, or
manual exclusion list needed. Verified on this corpus: raw recipe hits of
66/66/71/64 per mission bank collapsed to a clean, non-overlapping 61/62/66/59
that reproduced every previously hand-found example exactly.

This generalizes to any self-referential structural recipe over a
relocation/pointer table — a record format whose own internal fields have
the same on-disk shape as the record header itself is a plausible source of
this exact ghost pattern, and the same sort-then-greedy-non-overlap
resolution applies regardless of the specific field layout.
