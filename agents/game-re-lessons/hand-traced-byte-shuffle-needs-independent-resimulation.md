# A careful hand-trace of a multi-instruction byte-shuffle arithmetic chain still needs an independent from-scratch resimulation before shipping it

**When it bites:** you've disassembled a short subroutine that computes an
address/index/selector through a chain of several small integer ops on a
fixed-width ISA (`ROR`/`ROL`, `ADD.B`/`SUB.B`, `LSL`/`LSR`, `ANDI`, byte
swaps) — the kind of "helper arithmetic" a compiler or hand-written
encoder emits to pack/unpack a bitfield or compute a table index — and
you're about to write up the derived formula as confirmed after tracing
it by hand, instruction by instruction, on paper/in your head. Also fires
for a *branchy* (not purely linear) function on a delay-slot ISA — several
conditional branches plus a loop, not just a straight-line chain — where
the hand-trace's error is in control flow (which register survives to a
given exit point) rather than in the arithmetic itself.

Confirmed on KGB (Amiga, `wyrm`): reverse-engineering a generic
"state-cell accessor" (`LAB_04DA`/`LAB_04DB`) required hand-tracing an
~10-instruction byte-shuffle (`ROR.W #8 ; SUBQ.B #1 ; ADDI.B #$28 ; ROR.W
#8 ; SUBI.B #$fe ; LSL.B #2 ; MOVE.W D0,D7 ; LSR.W #8,D7 ; ADD.B D7,D0 ;
ANDI.W #$00ff`) that computes a field-selector offset from a 16-bit "cell"
input. The hand-trace was done carefully, cross-checked twice, and looked
solid — but it was independently re-verified anyway by writing a ~30-line
Python function that executes the *exact same instruction sequence* one
step at a time (masking to 8/16 bits at every intermediate step, exactly
mirroring each mnemonic) and running it on the real cell values found in
the disassembly. The two agreed exactly for every value tried, which is
what justified shipping the derived byte-level spec (a specific section +
record + field mapping) as *confirmed* rather than *hypothesis*. Had they
disagreed, the bug would almost certainly have been in the hand-trace, not
the simulator — a small transposed step, a forgotten truncation, or a
wrong assumption about which half of a register a `MOVE.B` touches are all
easy to miss when carrying several intermediate byte values across ten
mental steps, and none of them would announce themselves: the wrong
formula would still produce *a* plausible-looking offset, indistinguishable
from the right one without an independent check.

**Fix:** for any multi-step byte-shuffle arithmetic chain (not a single
instruction, and not a named/well-known idiom you can eyeball) that a
finding's whole conclusion depends on, write a tiny throwaway simulator
that executes the disassembly text literally — same instruction order,
same explicit 8/16/32-bit truncation at each step — rather than trusting
mental arithmetic alone, however carefully double-checked. This is cheap
(minutes) relative to the cost of shipping a wrong offset formula into a
format spec that downstream extractors and docs will then build on.

## Second manifestation (2026-09-27, `valkyrie`, VP1 PSX): a branchy control-flow function, not a linear chain

The same fix generalizes past straight-line arithmetic to a **branching**
function whose complexity is in control flow rather than in the number of
ALU steps. `func_0x80013DD0` (a resident PSX pad-poll routine) has a
4-branch dispatch inside a 4-iteration loop with two different exit paths
(one `beq`-gated loop-exhaustion exit, one `j`-gated early-return) — few
enough instructions to look hand-traceable, but with just enough branches
and delay slots that a careful by-eye trace confidently concluded the
function's return value is unconditionally `0`. It isn't (see
`mips-delay-slot-instruction-always-executes.md`'s sixth manifestation for
the exact bug: a loop-exit branch's delay slot unconditionally overwrites
the return register on the way to `jr $ra`). A ~150-line scoped MIPS
interpreter — registers as a plain array, memory as a byte-addressed
`Map`, one `switch` per opcode family, executing the function's *actual*
disc bytes rather than a paraphrase of them — settled it in seconds across
every port/flag combination worth checking, and would have caught the
delay-slot mistake immediately had the hand-trace been trusted and shipped
first.

**Generalized fix:** the resimulation doesn't need to be a full CPU core
(that's Method § 5's "when hand-reimplementation fails, emulate" for
hostile decompressors/whole subsystems) — for a single function under
~100 instructions with no unsupported opcodes, a purpose-built, function-
scoped interpreter (support only the opcodes that function actually uses,
throw on anything else so a gap is loud) is minutes of work and gives an
authoritative answer a hand-trace of branchy delay-slot code cannot
reliably provide, no matter how carefully double-checked. Treat "this
function has 3+ branches and/or a loop" as the same trigger the original
byte-shuffle-chain trigger uses for "more than a couple of ALU steps."
