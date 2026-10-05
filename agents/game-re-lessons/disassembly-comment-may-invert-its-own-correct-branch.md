# A reference disassembly's own prose comment can read backwards next to its own correctly-transcribed compare/branch instruction

**When it bites:** a community/reference disassembly project (or a prior
session's own annotation) attaches a natural-language probability/direction
comment to a `cmp`/`bcc`/`bcs`/`beq`/`bne`-shaped conditional-branch
sequence ("3/4 chance to return", "skips if greater", "N% chance to
fire") — before trusting that prose for a roll/gate you're about to port,
re-derive the branch condition yourself from the raw compare+branch
opcodes.

The instruction bytes are the ground truth; a comment sitting next to them
is just someone's after-the-fact paraphrase, and paraphrases of branch
polarity are an easy place for a human (or an AI-assisted annotation pass)
to get the direction backwards while still transcribing the opcodes
themselves correctly — nothing catches this automatically, because the
disassembly still assembles back to identical bytes and the comment isn't
executable. A confirmed instance: FFVI (SNES, `ceres`)'s Black Belt
counterattack roll, `jsr Rand; cmp #$c0; bcs @4cc2`, annotated in
`everything8215/ff6`'s own source as "3/4 chance to return." Direct
instruction semantics say otherwise: `cmp #$c0` sets the carry flag iff
the unsigned comparand is `>= 0xc0`, and `bcs` (branch on carry set)
branches exactly when that carry is set — so the branch-away/return case
is `Rand() >= 0xc0`, which is `64/256` = **1/4** of the value space, the
opposite of what the comment claims. The code was transcribed correctly;
only the comment's stated fraction was inverted.

**Fix:** for any probability, direction, or "which way does this branch
go" claim sourced from a comment (yours, a prior session's, or a
third-party disassembly project's), simulate the compare+branch
instruction pair by hand against the actual opcode/operand bytes before
porting the described behavior — treat the prose as a hypothesis to check,
never as the oracle itself. When the derived semantics disagree with the
comment, trust the instructions: a wrong comment next to right bytes is
far more common than the reverse, since nothing forces a comment to stay
correct after being written, while the bytes are what actually executed on
real hardware. Document the correction explicitly (cite both the raw
instruction sequence and the disagreeing comment) so a later session
doesn't "fix" the port back to match the wrong prose.
