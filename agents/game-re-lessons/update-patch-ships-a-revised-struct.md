# A post-launch update can ship a revised struct — the "wrong" community template may describe the *other* build, and the two revisions cross-check each other byte-exactly

**When it bites:** a fan/community binary template (010 Editor `.bt`,
QuickBMS script, wiki struct doc) names a fixed-stride record's fields but
its declared order and/or total width don't match the records in front of
you, and you're about to write the template off as "the author guessed" and
re-derive the layout from scratch. Also bites, more generally, any time a
table is stuck **and the title shipped a post-launch update or DLC** — the
update is prior art you haven't read yet.

A community template documents *one build*. Games get patched, and a content
update can force a **struct layout change**: a new field, a widened field, a
reorder. The template's author very likely worked on whichever build they had
— often the final, DLC-complete one, because that's what's still on sale —
while your dump is the launch build, or vice versa. "The template's field
order is wrong" and "the template describes a different revision" produce the
*identical* symptom (right field list, wrong offsets, plausible-looking width
arithmetic that lands a few bytes off), and only one of them is worth acting
on.

**Check for a second copy of the table before doing any statistical
byte-census of the first.** It is cheap, and on the platforms that layer
updates over base content the copy is a plain file:

- **Switch** — the update's romfs is a LayeredFS tree (`patch1/`, `patch2/`,
  `patch3/`, higher layer wins). Loose files there *override* the base game's
  archives, so a table packed inside a base archive routinely reappears as a
  loose named file in a patch layer. See `game-re-tooling/switch.md`.
- **PS4/PS5** — patch PKGs; **PC** — patch archives / loose-file override
  dirs; **any platform with DLC** — the DLC package.

## Two revisions of the same table are a byte-exact oracle for each other

This is the real prize, beyond identifying the format. Adjacent revisions of a
table share almost all their content, so once you can read *either* layout you
can confirm *both*: map every offset of revision A onto its counterpart in
revision B, and require the shared records to agree byte-for-byte. Pair it
with null controls (an identity mapping, an off-by-N mapping) so the score
means something.

Confirmed on Fire Emblem: Three Houses' `Scenario` table (`chimera`, DATA0
index 22). The base archive holds 100 × **40**-byte records; the community
`Scenario.bt`'s field list at its real 1-byte enum widths sums to **46**, and
decoding at the template's declared order was refuted outright (`map` /
`victoryCondition` stuck near 0 across dozens of consecutive records). Two
prior passes concluded the template's *order* was wrong and recovered exactly
one field from a template-blind per-byte census. In fact the v1.1.1 update
ships the same table as a loose `nx/data/fixed_scenario.bin` in every patch
layer — and **patch3 is stride 46 and decodes in the template's declared order
verbatim.** The template had been right the whole time; it documented the
DLC-era build. `46 = 40 + 5 (five character-id fields widened u8 → int16) + 1
(trailing pad)`, and the cause is visible in the data: the DLC characters'
own IDs are 1040-1046, which do not fit in a byte. *A content update forced a
field-width change.*

Censusing the stride-46 records (easy — the template pins them), mapping each
stride-40 column onto its stride-46 counterpart, and diffing two adjacent
patch layers whose shared content should be identical gave **3,480 / 3,480
byte-exact matches across all 87 non-DLC records**, against null controls of
16.8% (identity mapping) and 22.3% (offset+5). One test confirmed both
layouts at once — far stronger, and far cheaper, than the two passes of
statistical byte-census that preceded it.

## Sub-trap: a width change and a reorder can happen together

The obvious bridging hypothesis — "revision B is revision A with those fields
widened **in place**" — was refuted here, and refuted *deceptively*. Under
that reading the record's tail (the five defeat-condition bytes) landed
perfectly, which made the whole mapping look right; every character-id read
was garbage, because the widened fields had also **moved**, to the head of the
record. Three groups of fields were reordered between the two revisions, so
the launch layout could not have been read off the template at any width.

Do not accept a cross-revision mapping validated at one end of the record.
Census the new revision from scratch and check *every* column.

## Free held-out test set

Records the update *populates* and the base build leaves all-zero never fed
your layout derivation, so decoding them is a genuine held-out test. Here 13
DLC records yielded the four DLC-only map-enum entries appearing only on DLC
chapters, and one chapter's victory condition decoding to `Chalice` ("Find the
Chalice") — literally that chapter's real objective.

## Sub-case: when the shift itself (not just the field order) is the unknown, only a semantic check discriminates it

The Scenario case above had two full revisions to diff against each other,
which is the strongest oracle available. A weaker but still-recoverable
shape: only ONE revised copy exists (no side-by-side old/new diff), and the
open question is a small integer shift applied to a run of fields inside an
otherwise-already-decoded record. A coarse "is the resulting byte in a
plausible range" sanity check can fail to discriminate at all — confirmed on
this same project's `PersonData` table (base 76-byte stride → v1.1.1
patch3+/v1.2.0 patch4's 80-byte stride, a widened-DLC-cast case exactly like
Scenario's): every shift value 1 through 4 passed a `<=99`-stat-byte sanity
sweep near-100%, giving zero signal on which was correct. What discriminated
it was checking the shifted fields against SPECIFIC KNOWN REAL VALUES, not
just plausible ranges — decoding at shift=+3 landed Byleth at his
already-known 175/175cm, Edelgard at her real 158/158cm, and Dimitri at his
well-documented 180→188cm post-timeskip growth spurt, while the other three
shift candidates did not reproduce any of these. Whenever a struct-revision
shift is ambiguous and no second revision exists to diff against, spend the
effort finding 2-3 fields with independently-known real-world values (character
stats, canonical measurements, published game facts) rather than trusting a
sanity-range check to narrow it — the range check only rules out impossible
values, it does not find the *correct* one among several plausible ones.

Related: this is also a completeness issue, not only a format one — the base
archive's DLC records were entirely empty, so a base-only extraction would
have silently understated the table. See
`community-template-field-order-wrong-not-just-width.md` (the census fallback
for when there really is only one build), `format-field-width-unexercised-by-first-corpus.md`
and `version-flag-conflates-independent-format-traits.md` (sibling
version-drift traps), and `reference-tool-data-revision-mismatch.md` (the same
build-mismatch problem coming from a reference *tool's* bundled data).
