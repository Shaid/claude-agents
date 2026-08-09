# Adding recognition of a new pattern to a resync loop can change the primary record count too, not just add new records

**When it bites:** a word/byte-stream parser already has a confirmed
"skip-one-word-and-retry" resync for records that fail primary validation,
you've just cracked the shape of a second recurring pattern hiding in those
skipped gap words, and you're about to wire its recognition in expecting
the change to be purely additive (same primary records, plus some new
secondary ones).

> **Correction:** this lesson's original worked example called the
> recognized pattern a confirmed "second record type" (an Epic (Amiga)
> `.3D` model "hardpoint" unit, `[value, tag=21, i, j, k]`). A later
> `re-codebreaker` escalation on the *same file* found that reading was
> itself downstream of a wrong premise: the whole region — including every
> "face record" the primary grammar had been matching — is not a data-record
> array at all, but an **executable display-list bytecode** the
> game's own interpreter runs; the "hardpoint tag 21" was opcode 21, a
> backface-facing test, one opcode among 25 in a single real grammar, not a
> second interleaved record type. See `bytecode-residue-recurring-groups.md`
> for that half of the story. The mechanism this file documents — wiring in
> recognition of a new pattern shifts the *primary* count because some
> earlier "successes" were coincidental garbage matches — remains accurate
> as a description of what happened and is worth keeping as its own
> narrower, mechanical lesson.

Confirmed on Epic (Amiga)'s `.3D` model format: the primary parser already
resynced past unrecognized words one at a time, and a 5-word
`[value, tag, i, j, k]` pattern was found recurring in those skipped runs.
Wiring recognition of that pattern into the resync loop (tried after
primary-record validation fails, before the 1-word skip) changed
EPICSHIP.3D's *primary* record count from 574 to 570 — 4 fewer, not the
same 574 plus 11 new records of the other kind. The reason: some of those
original 574 "valid" records were never real — they were coincidental
garbage matches that only validated because the resync had landed on a
mid-pattern byte offset by chance (a small field-value combination that
happened to satisfy every bounds check the primary grammar imposed). Once
the new pattern is recognized and properly consumes its own words, the
cursor no longer lands on those offsets, and the spurious matches disappear.

**The fix:** after adding recognition of a new pattern to a resync loop,
always re-diff the *primary* record count and its full field list against
the pre-change baseline, not just the new pattern's count — a change in the
primary count is expected and correct, not a regression, but only if you
can show (per-record) which primary matches disappeared and that they sat
at byte offsets the new pattern's own span explains. Silently accepting
"more decoded, nothing removed" as the only possible good outcome would
have hidden 4 previously-mis-parsed records as still-confirmed data. This
generalizes beyond this one format: any greedy/resync parser over a stream
with more than one recognized pattern can have earlier passes' "successes"
be coincidental products of a still-incomplete grammar, not independent
ground truth — and, per the correction above, that incompleteness can run
deeper than "a second record type is missing."
