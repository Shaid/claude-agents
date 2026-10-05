# An "active" flag shared by several records is not the whole gate — a second field compared against live runtime state can make them mutually-exclusive alternatives, not simultaneous content

**When it bites:** several records in one resource (triggers, sub-objects,
placement entries) all pass an already-confirmed "active/enabled" flag
check simultaneously, a static extractor combines all of them into one
output, and the result looks wrong in a way that suggests overlapping or
duplicated content — especially when the records also carry a second,
small, previously-undecoded or "not needed for static extraction" field
that turns out to be compared against a global variable at runtime.

## What happened

Confirmed on Parasite Eve (PSX, `parasite` project): a tile-scatter
background compositor's trigger records each carried a `flags` byte
(bit 0x2 = active) that a static extractor correctly used to filter which
triggers to render. But one package had **10 simultaneously-active**
triggers, and the extractor combined all of them into a single composited
canvas — producing a visibly broken result (what looked like two
different camera angles of the same room stacked/overlapping in one
image, matching a real gameplay observation of that room shown from two
distinct fixed camera angles).

The triggers also carried a second byte, previously documented only as
"room/camera-angle id (compared at runtime against the current camera
state — not needed for static extraction)" — i.e. already spotted as
*something*, but dismissed as irrelevant to a static dump. A `ghidra-
disasm` trace of the real trigger-walk code found this field is a genuine,
separate gate: the walker reads it and compares it against a plain global
byte (read fresh on every call, not passed as an argument), skipping the
trigger on mismatch **even when its `flags` active bit is set**. In other
words: `flags` active means "this trigger is a candidate," and the second
field is what actually selects *which one* of several simultaneously-
candidate triggers the live game shows at any given moment — they are
mutually-exclusive alternatives (different camera angles of the same
room), not simultaneous content meant to be drawn together.

## The fix / general rule

When a resource's records pass one gate (an active/enabled flag) but a
static extraction combining all of them produces overlapping, duplicated,
or otherwise incoherent output:

1. **Don't stop at the first passing gate.** Check every other
   small/enum-shaped field in the same record — especially one already
   noted as "compared against runtime state, not needed for static
   extraction" — for a second, independent selection mechanism. A field
   dismissed once as "not needed for a static dump" is exactly the kind of
   field that turns out to define *which* static dump is correct.
2. **A discriminator compared against live/global state (not a per-record
   constant, not derivable from the record itself) is the signature of
   mutual exclusivity**, not simultaneity — the game can only ever be in
   one state at a time, so records gated on matching that state represent
   alternatives (camera angles, level-of-detail, animation phase, weather/
   time-of-day variant, dialogue branch), not layers to composite
   together.
3. **The static-extraction fix is to enumerate the discriminator's value
   space and emit one output per distinct value**, not to pick one
   arbitrarily and not to combine them all. Group records by the
   discriminator field first, and treat records sharing a group as the
   ones legitimately meant to composite/combine together (they passed both
   the active flag AND the same discriminator value); records in different
   groups are separate, mutually-exclusive outputs.
4. This generalizes past "camera angle": any "several records are all
   individually active, but the game only shows one set at a time"
   situation — palette/skin variants, LOD chains selected by distance,
   quest-state-gated content — is worth checking for the same shape before
   assuming an "active" flag alone is a complete filter.

See `record-array-alternatives-vs-parts-footprint-test.md` for a related
but structurally different confusion (alternatives vs. spatially-disjoint
*parts* that must ALL be combined to cover a region) — that one is
resolved by a footprint/coverage test on records with no active-flag/
discriminator gate at all; this one is resolved by finding the runtime
selection field and grouping by it.
