# Two sibling fields that hold equal values in the dominant sub-case can defeat spot-checking — identify the field, then re-verify only against the minority sub-case

**When it bites:** a fixed-stride record has two candidate fields for a
single semantic role (a length, a count, an offset) — often one at a
smaller width/earlier offset and one wider/later — and a hand-picked field
has passed every spot-check so far, in a corpus dominated by one common
parameter value (e.g. most records span a single allocation unit/track/
block). Also bites when a downstream chain/contiguity invariant that
*should* catch a wrong field pick instead looks fine, because the sampled
records never included a multi-unit one.

Confirmed on Midwinter (1) (Amiga, `hunter`): a 16-byte on-demand resource-
table record has a word at `+10` and a longword at `+12`. An earlier pass
documented `+10` as the byte length and `+12` as "an unexplained running
longword," and this held up across many spot-checks — because for every
**single-track** record (`span == 0`, the overwhelming majority of the
table), the two fields are numerically equal by construction (a one-track
resource's length and its "running total" longword coincide). The mistake
only became visible once a resource-chain contiguity check was run across
*all 61* records including multi-track ones: reading `+10` as the length
left both chains full of gaps, while `+12` made all 61 records chain
byte-contiguous with zero gaps. The wrong field had been silently
"verified" the whole time by a corpus that never exercised the case where
the two fields diverge.

**Fix:** when two candidate fields for one semantic role produce identical
values for some subset of records (a common/default parameter value,
`span==0`, `count==1`, a flag defaulting to a fixed state), don't trust a
spot-check drawn from that subset at all — it cannot discriminate the two
candidates by construction. Deliberately sample (or build a whole-corpus
invariant across) the *minority* records where the fields would predict
different values, and let that subset alone decide. This is the field-
*identity* sibling of `format-field-width-unexercised-by-first-corpus.md`
(which covers a *width* passing every check because no value in the first
corpus exceeded it) — same root cause, a corpus that under-exercises the
discriminating case, but here it's *which offset holds the semantic role*
that's ambiguous, not how wide to read one already-agreed offset.
