# A documented "entry k of table A <-> record k of table B" pairing is not proof the two tables have equal length — read each table's own self-describing count

**When it bites:** two sibling self-describing tables in the same container
are documented as index-paired (e.g. "hotspot-table entry k belongs to
scene k-1"), and a consumer walks table A only up to table B's own declared
count (or vice versa) instead of table A's own offset-table/length field —
especially when building a *new* downstream consumer (an index, a graph, an
aggregate corpus-wide count) over an already-"confirmed" format whose
original decoder and tests never needed to enumerate every entry of table A
against an independent oracle.

Confirmed on KGB (Amiga, `wyrm`)'s `PAC/*.pac` container. Block 0 (the
hotspot rectangle table) and block 1 (the scene-descriptor table) are
documented as "entry k <-> block-1 scene k-1" — a real, structurally-true
pairing for the common case. But block 0's own self-describing offset table
can run **longer** than block 1's declared `sceneCount` (`chap1.pac`: 56
hotspot-table entries vs. `sceneCount` 49, one of the 7 extra entries
non-empty and real). A first-pass graph-builder iterated hotspots by
looping `sceneIndex` from `0` to `table.sceneCount - 1` and looking up
`pac.hotspots[sceneIndex]` — silently dropping every hotspot-table entry at
or past `sceneCount` across all 8 files, 55 real records total (out of
1751 already corpus-wide-verified as structurally valid rectangles). No
error was raised: the loop bound was simply smaller than the real table, so
the missing entries were never visited, never counted, never flagged.

The bug was only caught because the new consumer needed a **strict
corpus-wide count invariant** to hold (matching an already-published
"1751/1751" figure from the original format doc) — a test that demands an
exact total, not just "decodes without error" or "spot-checks look right,"
is what surfaced the gap. The fix: iterate `pac.hotspots` by its **own**
length (the offset table it was decoded from), and only consult table B's
count to decide *whether an entry has a documented pairing partner* — not
as the loop bound for table A itself.

**Fix, generalized:** when a container ships two or more self-describing
tables (each with its own leading count/offset-table field) that a format
doc documents as index-paired, always iterate *each* table by its own
declared length. Use the other table's count only to classify entries as
"paired" vs. "past the documented pairing range" (which — per this
project's own convention for honest gaps — should be surfaced as a distinct,
explicitly-flagged case rather than silently dropped or silently attached to
the wrong partner). This is a different failure shape from
`self-describing-length-field-mistaken-for-corpus-constant.md` (a single
table's own per-record length field misread as a fixed constant) and from
`sibling-field-values-alias-in-dominant-case.md` (two candidate fields
competing for *one* semantic role) — here there is no ambiguity about which
field holds which table's count; the mistake is using a *different table's*
count as if it bounded *this* table, on the strength of a documented
pairing that was never claimed (or verified) to guarantee equal length.
Building any new derived index/graph/aggregate over an "already solved"
multi-table format is exactly the kind of task that surfaces this — its own
strict corpus-wide count checks exercise a code path the original decoder's
tests never needed.
