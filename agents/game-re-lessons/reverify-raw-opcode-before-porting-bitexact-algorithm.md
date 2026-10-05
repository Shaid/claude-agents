# A prior pass's disassembly-derived pseudocode for a bit-exact algorithm (RNG/checksum/hash) can be wrong with zero symptom once ported

**When it bites:** you're about to port an already-"confirmed" disassembly
citation for an RNG, checksum, hash, or other small bit-manipulation
routine into a decoder/generator — especially one documented in a prior
session's prose (`roxr.l #1` vs `lsr.l #8`, "returns bits 1..15" vs "bits
8..22", rotate vs shift, signed vs unsigned shift) rather than a byte
dump you can re-check yourself right now.

Powermonger (Amiga, `RUN_PROG`): the project's own docs described the
master RNG's output step as `roxr.l #1,d0 ; and.l #$7FFF,d0` ("returns
bits 1..15"), presented as confirmed. Direct re-disassembly of the exact
bytes (`e0 88 02 80 00 00 7f ff`) showed this is actually plain
`lsr.l #8,d0` followed by `andi.l #$7FFF,d0` — a logical shift by 8, not a
1-bit rotate, returning bits 8..22 instead. Nothing about the wrong
version would have failed loudly if ported as-is: an LCG-style RNG built
from the wrong bit-slice is still deterministic, still produces
well-distributed-looking 15-bit values, still passes every "looks like a
working RNG" sanity check — the only way to catch the error is comparing
against the real opcode bytes (or an independent oracle), never by
observing the port's own behavior.

**Fix:** before porting any bit-exact algorithm (RNG, checksum, hash,
compression bit-reader) from a prior citation, re-disassemble the exact
address range yourself and read the raw opcode bytes directly (a `hexdump`
of the instruction, not just the mnemonic another tool printed) — don't
carry forward a textual description across sessions without re-verifying
it once against ground truth. This class of bug is invisible precisely
*because* the output still looks plausible; structural sanity checks
(determinism, boundedness, distribution) cannot catch it, only re-reading
the bytes or an independent side-by-side oracle (a second implementation,
a live capture) can.

**When a doc's own hedge says "the textbook shift/constant doesn't quite
match, exact value not fully re-derived" — don't trust the textbook table,
re-execute the compiled arithmetic instead.** Confirmed on Valkyrie Profile
(PSX, `valkyrie`): battle-logic.md carried an open hedge on a periodic
turn-counter check reading "`0x66666667` is the canonical `/10` magic
constant, but the shift amount used (`1`) doesn't match the textbook `/10`
or `/5` shift — exact modulus not fully re-derived, likely 5 or 10." The
doc's own memory of "what shift `/5` vs `/10` should use" was the error, not
the code: `0x66666667 = round(2^33/5) = 1717986919` is in fact the standard
signed-divide-by-**5** magic constant, and the `sra`-by-1 the code uses is
exactly right for it. This was settled not by looking up a corrected
textbook table but by writing a ~15-line simulator that re-executes the
literal MIPS sequence bit-for-bit (`mult` as a 64-bit BigInt product, `mfhi`
as the signed high word, the `sra`+sign-bit-subtract exactly as encoded) over
a range of concrete inputs (turn 0-199), diffing against `turn % 5` (0
deviations) with a negative control against `turn % 10` (20/200 real
disagreements, proving the check discriminates). **Fix, generalized:** a
"doesn't match the textbook shift/constant" hedge is a signal to stop
consulting remembered magic-constant/shift-amount tables entirely and
instead numerically re-derive the divisor by executing the *compiled*
instruction sequence over concrete inputs — this is strictly stronger than
re-reading opcode mnemonics alone (which only proves the *sequence* is
transcribed correctly, not what modulus it actually implements), and always
pair the positive check with a negative-control candidate modulus so the
check can fail if it's wrong.

**A passing numeric check can still hide the same class of error.** Writing
a from-scratch verify script for VP1's `rcos` table (`valkyrie`, PSX), a
first draft read the table with a signed 16-bit accessor, when the real
instructions are all `lhu` (unsigned) — the code applies the sign itself
via an explicit negate on two of the four quadrant branches, never by
reading a raw negative bit pattern. The script still passed a whole-domain
check (4096/4096 correct) on the first try, purely because this particular
table's real content never exceeds magnitude 4096 (well under the 0x8000
sign-bit threshold where signed and unsigned reads diverge) — the check
validated the *formula*, not the *read width/signedness choice* the port
also needs to get right for a table with larger magnitudes. Caught only by
rereading the literal opcode (`lhu` vs `lh`) rather than trusting the
passing numeric result. **A verification check that agrees with a wrong
implementation detail is not evidence for that detail** unless the test
data actually exercises the value range where the wrong choice would
diverge from the right one — for a signed/unsigned read specifically, that
means checking the table's own values span (or is forced to span) both
sides of the sign-bit threshold, not just checking that the final formula
comes out right on the values the table happens to contain.
