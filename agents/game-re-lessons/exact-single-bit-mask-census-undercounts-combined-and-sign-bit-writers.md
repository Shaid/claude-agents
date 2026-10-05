# An exact-match single-bit-mask census (built to avoid containment false positives) creates false NEGATIVES for bits only ever written combined with siblings, or for the sign bit specifically

**When it bites:** a producer/consumer census for one bit of a flags word
requires the instruction's immediate to EXACTLY equal the target bit's mask
(the correct fix for `bitmask-containment-census-false-positive-for-
individual-bit.md`'s over-matching) and reports zero hits for a bit that a
script-facing property table, a community doc, or a sibling census already
proves has a real, heavily-used producer — especially the highest bit
(bit 31, the sign bit) of a word, or any bit whose only known write site
sets it alongside one or more neighbors in a single instruction.

## What happened

Confirmed on Valkyrie Profile (PSX, `valkyrie`, round 17 of the
`vp1psx-scene-script-opcodes` `obj+0xe4`/`obj+0xe8` campaign). A fresh
sibling-bit census (deliberately built to require an exact match between an
`andi`/`ori` immediate and `1<<bit`, precisely to avoid the containment
false positives documented in the sibling lesson above) returned **zero**
hits for `obj+0xe4` bits 18, 23, and 31 — but bits 23 and 31 both have a
real, already-documented, heavily-used script-facing `SETPROP` producer
(`SETPROP` 24 sets bits 19+23 together via one `ori $r,$r,0x880000`;
`SETPROP` 44 sets bit 20 while clearing bits 20+23 together via one
`andi`/`ori` pair on `0x00900000`; `SETPROP` 37, D1=217 immediate-form uses,
sets bit 31 alone). The census's exact-equality requirement — the very fix
that correctly excludes coincidental containment matches — also silently
excludes every LEGITIMATE combined-mask write, because `0x880000 !== 0x800000`
just as surely as `0xf0 !== 0x20` does. Only bit 18 (no `GETPROP`/`SETPROP`
entry anywhere, and 0 hits under every technique) was a genuine, currently-
unexplained gap; bits 23 and 31 were a **census blind spot**, not evidence
of anything about the game.

Bit 31 specifically has a second, independent reason to evade a naive
census: on MIPS, `andi`/`ori`'s immediate field is a 16-bit **zero-extended**
value, so `ori $r,$r,0x80000000` cannot be encoded at all — setting or
testing the sign bit alone requires either a `lui`+`or`/`and` pair (which a
`constRegs`-tracking census CAN catch, if its `lui`-tracking is complete) or
an entirely different, mask-free idiom: `bltz`/`bgez` (branch on sign),
or `sll $r,$r,1 ; srl $r,$r,1` (shift left then logical-shift right by 1,
clearing the sign bit with no mask constant anywhere in the instruction
stream at all). A census keyed purely on `andi`/`ori` immediates, even one
with full `lui`-tracking, has no way to recognize the shift-pair or
branch-on-sign forms; this generalizes to any fixed-immediate-width ISA
(Z80/6502/ARM Thumb narrow immediates have analogous top-bit-unreachable
gaps) whenever the flag of interest sits in the widest meaningfully-tested
bit position.

## Fix

1. **Never report "zero census hits" as a settled negative without first
   checking whether an external oracle (a script property table, a
   community doc, a sibling function) already proves a producer exists.**
   If one does, the finding is "the census has a blind spot for this bit,"
   not "this bit is unused" — write it up as a method gap explicitly (see
   `tracker-prose-is-not-evidence.md`'s discipline applied to your OWN
   tool's output, not just someone else's prose).
2. **Run a second pass with a CONTAINMENT test** (`(imm & mask) === mask`)
   specifically for bits that fail the exact-match pass, and manually
   disassemble every containment hit rather than auto-accepting it — this
   recovers combined-mask writes while still requiring human judgment to
   reject the unrelated coincidental hits the containment file warns about.
   The two techniques are complementary, not substitutes: exact-match for a
   quick, low-noise first pass; containment-plus-manual-review for the
   bits exact-match couldn't explain.
3. **For the sign bit (or any bit an ISA's immediate width can't reach
   directly), extend the census to also recognize `lui`+`or`/`and` pairs
   (track the `lui`-built constant through to the following logical op),
   `bltz`/`bgez`-class sign branches, and shift-pair sign-clear idioms**
   (`sll #1` immediately followed by `srl #1` on the same register) as
   producer/consumer evidence — a plain immediate-only scan is structurally
   blind to all three.

Distinct from the containment file's four false-positive shapes (all about
a census reporting a hit that ISN'T real): this is the mirror-image failure,
where the fix for over-matching removes true positives too. Both files
describe the same underlying tension — a census tuned to avoid one error
class tends to manufacture the other — and should be read together when
building or reviewing any bitmask producer/consumer scan.
