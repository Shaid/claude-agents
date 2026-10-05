# When a fan template's field *order* won't fit, first ask which build it describes — then fall back to a template-blind per-byte census

**When it bites:** a fan/community 010-Editor-style binary template names a
fixed-stride record's fields, its declared total width doesn't match the
corpus's confirmed record stride, and after correcting known width-guessing
bugs (a 2-byte enum that's really 1 byte, a trailing block the build doesn't
carry) the width still doesn't land — or it lands, but decoding real data at
the template's field *positions* produces implausible output (a location/type
ID stuck at 0 for dozens of consecutive records; a small-enum field mostly out
of range).

Correcting field *widths* against a template is a different, weaker fix than
correcting field *order*. A template's field list can have every individual
width right and still declare them in a sequence that doesn't match your
bytes, so summing widths in the declared order can converge on a plausible
total while every field still reads from the wrong offset.

## First: is the template describing a different build?

> **Correction.** This file previously concluded, from the worked example
> below, that the template's declared *order* was simply wrong ("the author
> guessed"). That diagnosis was later disproven. The template's order was
> exactly right — for the game's **post-update** build, which uses a wider
> record than the launch build the analysis was run against. A revised struct
> in an update produces the identical symptom this file's hook describes.
> **Check for a second copy of the table in the game's update/DLC content
> before concluding anything about the template's ordering** — see
> `update-patch-ships-a-revised-struct.md`, which also covers the
> cross-revision byte-exact diff that finally settled the case.

## Fallback, when there genuinely is only one build

The census below is still the right move when no second revision exists, and
it is what produced the one field that survived the correction above.

Don't keep re-guessing at the template's ordering. Census **every byte
offset** of the confirmed fixed stride across the **whole corpus**,
independent of any template, for two cheap statistical signatures: a
monotonically non-decreasing (ideally exactly +1-per-record) run, and a
small-distinct-value-count column. A real semantic field — a story-chapter
number, a level index, a type enum — leaves one of these; padding reads as
constant zero; hashes, pointers and scratch values show neither. Once an
anchor is found, its *position* is ground truth, and it usually gives a second
oracle free: if its value range or special-case values are documented anywhere
— even in the same untrustworthy template's prose comments — a match there
confirms the anchor.

Confirmed on Fire Emblem: Three Houses' `Scenario` table (DATA0 index 22,
100 × 40-byte records, `chimera`). A per-byte-offset census across all 100
records × 40 offsets found offset 5 running `0,1,2,...,22` in exact story
order across the first 31 records (FE3H's real 22-chapter main story), then
long constant runs of `23`, then `24`, then `25` — matching the template's own
field comment ("23=Paralogue, 24=Aux battle, 25=DLC Para/Aux") byte-for-byte.
Three independent confirmations landed on one offset at once: monotonic
chapter progression, the real chapter count, and the template's documented
special values. This is a stronger version of the animation-keyframe monotonic
oracle in Method §4 — same signature, applied corpus-wide as a *field-locating*
search over every byte offset of an unfamiliar record.

**Know what this technique does and doesn't buy.** On the case above it
correctly located one field across two passes, and it cannot in principle
recover a field's *identity* — only its shape. The cross-revision diff that
became available once the update's copy of the table was read resolved the
entire 40-byte record in a single test. Census when you must; look for a
second encoding of the same content first.
