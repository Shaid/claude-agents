# A record "signature" derived from one reference instance can bake in a field that's real per-record data, not a magic constant

**When it bites:** a multi-field detection/signature check (2-3 header
constants that must all match exactly to classify a blob as "type X") passes
for only a modest slice of a much larger population of structurally-similar
candidate records, especially when that population lives in an already-solved
self-describing container (a directory with per-slot counts/offsets) so the
"missing" records aren't hidden — they're sitting right there, just rejected
by the signature check.

A signature check is usually derived by hex-dumping one confirmed-good
instance, noticing 2-3 fields that look like fixed small constants, and
writing `field_a === X && field_b === Y && field_c === Z`. This conflates two
different kinds of evidence: fields that really are format-wide magic
constants (a version tag, a fixed sentinel byte), and fields that just
*happened* to hold that value in the one instance examined — because the
sample was small, or because that instance's real per-record data (a bone
count, a variant id, a small enum) coincidentally matched a "nice" number.

Confirmed on Parasite Eve (PSX)'s actor-package chunk3 slot-2 sub-resources
(`tools/shared/psx-actor-model.ts`, `hasModelSignature()`): the existing
model-detection check required `h[12]===31 && h[15]===1 && h[17]===255`,
shipping 136/136 models against that gate. A census of the same slot-2
population found 878 total sub-resources; 742 of the 742 non-matching records
independently satisfied both *other* fields (`h[15]===1 && h[17]===255`) and
every downstream structural invariant already used to validate real models
(the bone-chain `translationZ === -parent.boneLength` relationship, the
`(0x80,0x80,0x80)` neutral-tint sentinel scoping, a UV tail anchored to the
declared model size) — with zero deviations across a 4-sample spot-check where
`h[12]` was patched to `31` and the real parser (`tryParseModel`) was run
unmodified. `h[12]` was never a magic constant at all; it's real per-model
data (most likely a bone/part count), and the original signature only
"worked" because the reference instance it was derived from happened to have
`h[12] == 31`.

**The fix, generalizable:** when a signature check rejects far more
candidates than a corpus-wide structural census suggests should exist (or
rejects candidates that otherwise sit in a self-describing container's own
declared slot), test the signature's constant fields **one at a time** by
relaxing (or patching, if the field feeds later arithmetic) each field
individually and re-running the full downstream parser/invariant chain on the
previously-rejected population. A field is real load-bearing data — not
magic — if dropping just its equality check alone recovers a large batch of
records that then pass every *other* independent structural check with zero
exceptions. This is the multi-field-signature sibling of
`self-describing-length-field-mistaken-for-corpus-constant.md` (a single
length field mistaken for a corpus-wide constant because a small sample
never exercised its other values) and of
`format-field-width-unexercised-by-first-corpus.md` — the common root is
always the same: a small reference sample cannot distinguish "this field is
always this value" from "this field just happened to be this value in the
examples I checked."
