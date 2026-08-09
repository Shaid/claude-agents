# A packed argument's sub-fields can have correct bit boundaries but swapped semantic roles

**When it bites:** a multi-field packed instruction argument (a VM opcode's
operand, a packed struct word) is already split at the right bit positions
— each sub-field's width and offset match every real instruction that reads
it — but decoding a real, live sequence with those role labels produces
output that never changes or doesn't make behavioural sense (e.g. "the
same sprite frame redrawn six times with only a duration field changing"
for something that's supposed to be an animation).

Correct bit-slicing is not the same claim as correct role-assignment. A
prior pass can get every subfield's width and position exactly right (each
one really does occupy those bits, confirmed by tracing the instruction
that extracts it) and still swap which *named* role two adjacent subfields
play — especially when both subfields are plausible-sounding for either
role (a "delay before next frame" and "which frame to show" are both small
integers packed into an opcode argument; either one *could* be labeled
"wake-frame" without an obvious contradiction from the decoder code alone).

Confirmed on Spirit of Excalibur's FSME bytecode VM (`middilgard` project):
a months-old, previously-"confirmed" doc described `_Anim_Draw`'s packed
12-bit argument as "bits 5-11 → wake-frame; bits 0-4 → hold duration". The
bit boundaries were exactly right (traced correctly, `LSR.L #5` / `AND
#$7f` and `AND #$1f` respectively, matching real instructions in
`_Anim_Draw` itself) — but the two roles were inverted. Re-decoding a real
walk-cycle script under the doc's stated roles produced arg sequence
`0x100,0x101,0x102,...,0x106` reading as "frame 8 (constant), hold
0,1,2,3,4,5,6" — the same static pose redrawn with an incrementing
duration, which is not how any real animation looks. Swapping the roles
(bits 0-4 = frame index, bits 5-11 = timing delay) on the exact same data
produced "frame 0,1,2,3,4,5, each held ~8 ticks" — a textbook walk cycle.
The correction was only found by tracing a *second*, downstream consumer
function (`_DoFrmlScript`) that actually uses the field to address a
sprite frame table directly (multiplying it by the frame-table's byte
stride) — the original decoder function (`_Anim_Draw` itself) only ever
*stores* the two sub-fields into two separate object fields, giving no
internal evidence of which one is "the important one" without following
where each stored field gets read next.

**Fix:** when a packed field's bit *boundaries* are independently
confirmed (real extraction instructions match) but its *role labeling* is
inferred rather than directly cited to a consumer, don't stop at the
opcode's own decode function — trace at least one place downstream that
*reads* each stored sub-field for its stated purpose. And treat a decoded
semantic output that never varies, or that repeats a static value while
only a "duration"-labeled field changes, as a strong tell that two
role-adjacent fields are swapped — re-derive from a real consumer rather
than re-reading the same decoder more carefully.
