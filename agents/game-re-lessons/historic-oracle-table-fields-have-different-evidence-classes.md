# A historical hardcoded oracle table's fields don't all carry the same evidence class

**When it bites:** a from-source-bytes decode of a per-game constant
(a key, a range, a checksum seed) disagrees with one field of an
independent, historical hardcoded reference table for that exact game —
while every *other* field in the same table row matches your decode
exactly. Also worth checking before trusting (or distrusting) any
"old reverse-engineered constant table" as a uniform oracle across all of
its columns.

A hardcoded per-game table frozen from an earlier reverse-engineering era
(before some later discovery — a full key-derivation algorithm, a cipher
break) is not internally uniform in how it was obtained. Some fields in
each row were derived by actually breaking the mechanism (strong,
independent, hard-to-fake evidence); others may have been hand-tuned by
trial and error to "work well enough" for that era's emulation goals
(weaker evidence, and silently stale once the real algorithm is known). A
match on the strong fields does not certify the weak ones, and a mismatch
on a weak field does not impeach the strong ones — treat each field's
provenance separately rather than assuming agreement/disagreement applies
uniformly to the whole row.

Confirmed on Capcom CPS2's per-game battery-backed encryption key table
(`historic-mame`'s `src/mame/machine/cps2crpt.c`, predating the modern
`.key`-file bit-descramble discovery). For D&D: Tower of Doom (`ddtod`,
`kolbold` project), decoding the real `ddtod.key` ROM bytes via the
current, byte-exact `decodeCps2Key20()` (a direct port of current
mamedev/mame's own `init_cps2crypt()`) gave: master key `0x4767fe08,
0x14ca35d9` and watchdog instruction `0C78 1019 4000` — both matching
`historic-mame`'s hardcoded `ddtod` row **exactly**, byte for byte.  But
the same row's `upper` (encrypted address-range boundary) field disagreed:
`0x180000` in the historical table vs. `0x200000` computed directly from
the key bytes via the current driver's own formula. Master key and
watchdog are only obtainable by actually breaking the Feistel cipher —
strong evidence, and their exact match is powerful independent
confirmation the decode is correct. `upper` is exactly the kind of field
that's plausible to approximate by trial-and-error emulation testing
("close enough that the watchdog check still passes") without knowing the
real bit-exact formula — weak evidence, and the one field where the
historical table turned out to be a stale approximation rather than a
competing correct answer. Disassembling the decrypted opcode stream (60+
coherent instructions, exact watchdog opcode recovered) confirmed the
key-derived data is sound; the two `upper` candidates couldn't be
empirically discriminated further within the scope of that pass since
neither the reset vector nor the first startup instructions execute near
the boundary they disagree on — see
`~/Development/kolbold/docs/ddtod/cps2/data-structure.md` § "2.2 The
upper (encrypted-range) discrepancy" for the full writeup, and
`~/Development/kolbold/docs/ddtod/TODO.md`'s `ddtod-encrypted-range-
boundary` for the still-open empirical-discrimination item.

**Fix:** when a from-source decode disagrees with one field of an
otherwise-matching historical/legacy reference table row, don't treat the
whole row as either fully validated or fully suspect. Ask, per field: does
producing this value *require* solving the actual mechanism (cipher,
codec, checksum), or could a plausible value have been reached by
trial-and-error/approximation instead? Fields in the first class are
strong cross-checks; disagreement there is a real red flag worth stopping
for. Fields in the second class are weaker, and a modern from-bytes
computation using a verified-correct, source-ported formula can legitimately
override them — document the disagreement and its reasoning rather than
silently picking one value, and look for an orthogonal way to
discriminate them (disassembly reaching the disputed boundary, a second
independent oracle) as follow-up work rather than escalating it as if the
whole oracle table were now suspect.
