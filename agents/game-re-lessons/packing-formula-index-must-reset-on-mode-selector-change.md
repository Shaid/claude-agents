# A doc's own worked packing/index formula can silently assume one global counter when the real counter resets on a mode/page/bank switch

**When it bites:** a format doc's own worked example/formula for a
repeating placement or index scheme (column-major tile packing, a running
index into a shared buffer/bank/table) is applied literally — with ONE
counter across the whole record/stream — as part of a from-scratch
re-derivation (a fresh audit, a from-scratch port, an independent
cross-check script), and the result is a reproducible, non-random mismatch
confined to records that switch mode/page/bank/channel partway through.
Before treating this as a doc bug, a decoder bug, or a new pixel-layout
hypothesis, check whether a SIBLING field in the same record's own field
table already says the value is scoped to "the current" mode/page/bank —
that sibling prose is very often the pre-existing, already-written answer
to the ambiguity the summary formula glossed over.

Confirmed on Valkyrie Profile (PSX, `~/Development/valkyrie`), round 217
(the campaign's 18th rigor spot-audit): `data-structure.md` § 12.6
documents a tile-composited sprite format's "Tile-store packing" section
with a single global formula for a running tile index `n`:
`u = 16*floor(n/perColumn), v = 16*(n mod perColumn)`, and an already-
published whole-corpus verification table claiming "20,928/20,928, zero
deviations" — a claim that had never actually been re-derived by a
committed script, only cited from a one-time escalation probe. The first
literal, from-scratch application of that exact formula (one running
counter per resource) produced 3,312/20,928 mismatches — 43/256 resources
on both discs, identical failure set — and every failure was a
multi-texture-page resource, with the mismatch landing exactly at the
first tile after a `tpage` switch (`u` resetting to 0 there instead of
continuing to climb). The doc's OWN tile-record field table already said
`u` is "Texture U within the **current** texture page" — the scoping
answer was sitting right there, just never connected to the packing
formula's own worked example. Rescoping the running index to reset per
distinct `tpage` value made the formula hold with 0 deviations on both
discs, with no change to the shipped decoder at all (it never used the
simplified `n`-indexed formula — only the doc's own explanatory prose was
ambiguous about scope).

**Fix, generalized:** when a doc's own worked index/packing formula fails
a literal, corpus-wide re-derivation, first check (a) whether the
mismatching population is exactly "records with a mid-record mode/bank/
page/channel change" and (b) whether an adjacent field in the SAME record
already has more specific prose ("within the current X", "since the last
X switch") that a summary formula glossed over. If both hold, the fix is
almost always "reset the counter on every change of the selector field X,"
not a new geometry/layout hypothesis. Also record explicitly when the
corpus can't discriminate two equally-fitting reset rules — e.g. "resets
on every DISTINCT value of X" vs. "resets on every CONTIGUOUS RUN of the
same X value" are different rules in general (a record that revisits an
earlier X value would tell them apart), but if no record in the corpus
ever revisits a value, the two framings are indistinguishable there and
neither should be shipped as "the" ground truth over the other.
