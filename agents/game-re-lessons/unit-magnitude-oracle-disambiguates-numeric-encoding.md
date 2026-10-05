# When a numeric field's encoding (fixed-point scale vs. float) is ambiguous, decode both ways and keep whichever gives the physically-expected magnitude

**When it bites:** a binary field is known (from format/context) to hold a
normalized or otherwise magnitude-constrained quantity — a unit vector/
normal, a normalized weight, a quaternion component — but its own numeric
encoding is ambiguous: it could plausibly be a scaled fixed-point integer
(e.g. `int16/4096`) or a plain IEEE float32, and nothing in the local header
declares which. This is common in PS2/PS1-era vector-math register formats
(VU0/VU1 registers, VIF `STROW`/`STCOL`) that are reused generically for both
representations depending on what the encoding CPU code happened to write.

Confirmed on Valkyrie Profile 2 (PS2)'s VIF1 mesh display packets
(`tools/shared/ps2-fps-mesh.ts`, `resolveMaskedConstantNormal()`). A masked
`UNPACK` "1-component normal stream" turns out to encode a genuine constant
per-batch normal via the immediately-preceding `STROW` register's 3 words —
but different batches wrote that register with different encodings (int16-
scaled to match that batch's own position-stream convention, or plain
float32), with no flag anywhere declaring which. The fix: read the same 3
words both as `int32/4096` and as `float32`, compute each candidate's vector
magnitude, and keep whichever interpretation lands in `[0.9, 1.1]` — a
genuine unit normal is guaranteed to have magnitude ~1.0 under the *correct*
reading and, in practice, an implausible magnitude under the wrong one. This
resolved all 5,041 real masked-normal batches on the disc, and the correct
choice per batch was later found to correlate with that batch's own
position-stream encoding kind (useful as a secondary sanity check, not
needed for the decode itself).

**The general technique:** when a field's *encoding* (not its value) is
genuinely ambiguous between two candidates, and the field's *semantic role*
independently constrains its expected magnitude/range (unit length, a
probability/weight in `[0,1]`, a normalized quaternion), decode under every
candidate encoding and pick whichever satisfies the semantic constraint —
don't guess one encoding from format convention alone or hand-wave "probably
float" from a stylistic hunch. This is cheap (no disassembly needed if the
constraint is strong) and self-verifying: run it whole-corpus and require the
correct-encoding rate to be near 100%, not just "found for one sample." It
generalizes past this one field — any per-record scale/format flag that
you'd otherwise need a control-code table or a disassembly trace to resolve
can sometimes be skipped entirely if the decoded quantity's own physical
constraints are already known and discriminating.
