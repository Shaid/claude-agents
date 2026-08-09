# A prior pass's 1-2 flagged candidate clusters are not the whole unrecognized population — histogram it fresh before re-testing just those

**When it bites:** a task hands you a large "unrecognized"/"unclassified"
population (TOC entries, archive slots, file records with no matched magic)
plus a small number of specific candidate clusters a *prior* pass already
flagged within it (e.g. "these ~8 entries look like a byte-ramp, these ~90
entries look like a count+offset table") — and the instinct is to spend the
whole session re-examining just those flagged clusters with a sharper tool.

Re-testing the flagged clusters is worth doing first (a fresh, independently-
confirmed tool genuinely might crack what an earlier narrower pass missed —
see `repeating-chunk-descriptor-mistaken-for-flat-header.md` for a case where
that alone was the fix). But if it only yields modest progress, the flagged
clusters were very likely found by a **method that was never exhaustive over
the population in the first place** — an entropy/structure census, a visual
skim, or any process that "happens to notice" a couple of clusters is
sampling, not covering the whole leading-byte value space. Confining the next
pass to just those same 2 clusters repeats that same narrow coverage.

Confirmed on Valkyrie Profile 2: Silmeria (PS2, `~/Development/valkyrie`): a
prior pass's entropy/structure census over 2,511 "unrecognized" TOC entries
had flagged exactly 2 candidate families (8 entries, ~90 entries) worth
chasing. Re-examining both made real but modest progress (one resolved to a
recognizable inner tag at a sector-aligned boundary; the other stayed
unidentified and was escalated). But a **five-minute, near-zero-cost
histogram of every unrecognized entry's own leading 4 bytes** — a check the
original census, being entropy/structure-based, never performed — instantly
surfaced a *third* cluster an order of magnitude bigger than either flagged
one: 1,232 of 2,511 entries (49%) sharing one literal leading value, never
previously flagged at all. That cluster turned out to be a real, previously-
unknown container format, decodable with the project's *already-solved*
codec (zero new codec work) — cracking 1,046 TOC entries and yielding 126
new real, visually-verified images in one pass, dwarfing everything the two
originally-flagged clusters together would have unlocked even if fully
solved.

**The generalizable move**: before confining a session to a prior pass's
specific flagged candidates, spend a few minutes running the cheapest
possible discriminating scan over the *entire* unrecognized population from
scratch (a leading-bytes histogram, a size-distribution histogram, a
first-printable-run census — whatever the format family's own §1 triage
techniques suggest) and see whether a bigger, unflagged cluster falls out.
The flagged clusters exist precisely because some earlier method wasn't
exhaustive; a different cheap lens over the *whole* population, not just the
already-flagged subset, is how you find what that method missed.

**Secondary technique from the same investigation**: once inside an
unfamiliar directory/index structure whose per-record type-tag field looks
like ASCII noise at first glance, check whether the tag reads as a
recognizable real word when reversed byte-for-byte. Several independent,
semantically-coherent English words falling out of one uniform reversal
(here: a directory's tags decoded to `ANIM`, `CHAR`, `MAP`, `ICON`, `FACE`
when reversed) is strong confirmation the reversal is real, not a
coincidence — cheap to check, and immediately tells you what each record
category actually contains before decoding a single payload byte.
