# A record field's correlation with already-confirmed stats can refute an "item/name-table index" hypothesis that in-range values alone can't

**When it bites:** a record field decodes to values that always fall inside
a plausible name/item-table's index range (0 out-of-range across the whole
corpus) but the resolved names "skew" oddly — e.g. a monster's supposed
"weapon" index keeps resolving to shield/armor names instead of weapons —
and you're deciding whether to keep chasing a different index base/offset
for the same field, or reconsider what kind of field it is at all.

"Always in range" is a weak positive on its own: for a byte field with a
small effective range (say 2-90), a wide item catalog (e.g. 181 entries)
will make almost *any* byte value land in-range by chance, so "0
out-of-range" doesn't distinguish "this is really an index into that
table" from "this is some other kind of byte that happens not to exceed
the table's size."

**The stronger, cheap test:** compute Pearson correlation between the
suspect field and any *already-confirmed* stat fields in the same record
(HP, attack, level, etc.), across the whole corpus. An index into a
name/item catalog has no principled reason to track a creature's/item's
power level — catalog position is arbitrary with respect to gameplay
strength. A raw combat stat *does* track power, and correlates with other
power-scaling stats almost by definition (stronger monsters get higher
values across the board).

Confirmed on Phantasie III (Amiga, `nicodemus`): `monsinfo.dat`'s
`Weapon`/`Armor` byte fields were long assumed to index the confirmed
181-entry item-name table (reference-source field names literally said
"Weapon"/"Armor"), but resolved names skewed toward shields for weak
early monsters. Correlating those two fields against the independently-
confirmed `attackRaw` and `hp` fields across all 80 monster records gave
r = 0.77-0.96 for every cross-pair (and the fields also grew
near-monotonically with monster tier, `2` at a weak monster up to `90` at
the final boss) — while a same-record field known to be a genuinely
different, independent stat (`defense`) correlated at r = -0.05 with the
same fields, showing the high correlations weren't just "everything in
this record correlates with everything else." This flipped the
conclusion from "the item-table index lookup must have the wrong
base/offset" to "these aren't item-table indices at all — they're raw
combat-power stats," resolving a discrepancy that two earlier passes
(direct-index and different-item-table-region hypotheses) couldn't
explain.

**General rule:** when a field's resolved values against a name/lookup
table are *always in range but thematically off* for a nontrivial
fraction of the corpus, don't just keep adjusting the index/offset —
correlate the raw field against every already-confirmed same-record stat
first. A near-zero correlation with unrelated stats and high correlation
with only truly independent fields supports "this really is an index";
strong correlation with general power/tier indicators across multiple
independent stat pairs supports "this is a stat, not an index" and should
redirect the investigation instead of prolonging it.
