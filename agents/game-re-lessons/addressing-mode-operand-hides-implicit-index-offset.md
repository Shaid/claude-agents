# A CPU's indexed-addressing operand byte can itself add to the index register, not just select which dp base to offset

**When it bites:** hand-disassembling (or hand-porting) an indexed-
addressing instruction (`dp+X`-style forms especially — 6502/SPC700-family
CPUs, but the general shape recurs anywhere an addressing mode takes both
an immediate operand byte/extension word *and* an index register) and
computing the effective address from a formula you derived from mnemonic
prose rather than the encoding's own field layout — either treating the
operand byte as if it were always the same as the mnemonic's literal `dp`
in isolation, or extracting a displacement field at the wrong width from
an extension word.

Some indexed-addressing encodings fold an **explicit offset byte, carried
in the instruction's own operand**, into the same addition the index
register participates in — the effective address is `dp + ((operandByte +
X) & 0xFF)`, not `dp + X` with the operand byte serving only as a
mnemonic-display base. Reading the operand byte as a fixed base extended
by the index misses this: if the operand byte is nonzero, the real
destination/source window shifts by exactly that amount from what a naive
"index register alone" reading predicts. Confirmed on SPC700's `MOV
dp+X,A` (opcode `0xD4`): a copy loop with `X` counting down from 16 and
operand byte `0x01` was initially read as writing to dp offsets
`$10`-`$01`, when the real destinations (per `dp + ((1+X)&0xFF)`) are
`$11`-`$02` — a full one-byte-wide shift across the entire 16-byte table
that produced a plausible-looking (all in-range, no crash) but completely
wrong byte dump when inspected at the assumed window.

**Second confirmed case — wrong field width, not wrong semantics** (68k,
Wizardry 6 Amiga): the 68000 *brief extension word* used by
`(d8,PC,Xn)`/`(d8,An,Xn)` modes packs register/size selectors in the
**high** byte and a **signed 8-bit displacement in the low byte** — the
displacement is *not* the whole extension word. Hand-parsing
`MOVE.W (d8,PC,D0.W)` with the full extension word as a u16 displacement
produced a jump-table base of `0x9518` instead of the real `0x9418` —
in-range, structurally plausible garbage targets that cost a debugging
detour before the field-width error was spotted. Same failure shape as the
SPC700 case: the EA lands shifted-but-plausible, so nothing crashes.

**Fix:** before trusting a hand-derived effective-address formula for any
indexed-addressing opcode, re-derive it from the CPU's own real
implementation source (an emulator core, not just mnemonic prose) for that
*specific* opcode, not by generalizing from a similar-looking opcode's
addressing mode in the same family — sibling opcodes sharing a mnemonic
shape (`dp+X` appears on many different real opcodes) do not necessarily
share the same effective-address formula. If a copy/table-walk loop's
output "looks like garbage" or "looks shifted" at the expected memory
window despite otherwise-correct loop bounds/counters, checking the
addressing mode's *exact* effective-address formula (not just re-verifying
the loop's iteration count) is a cheap next step before assuming a deeper
bug.
