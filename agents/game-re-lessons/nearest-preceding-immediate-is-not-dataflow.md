# "Nearest preceding immediate load" is a guess, not dataflow — table-driven operands defeat it silently

**When it bites:** a byte-pattern census infers an instruction's operand
*value* (a DMA transfer size, a destination address, any register content)
by scanning backward from the instruction for the closest preceding
immediate-load (`LDA #imm`/`MOV reg, imm`/etc.) into the same register,
rather than doing real single-instruction dataflow. This is a fast, useful
triage heuristic — and it silently produces a confident, plausible-looking
**wrong** value whenever the real operand is loaded from a table
(`LDA $table,X`) instead of a literal, because the heuristic just grabs
whatever immediate happens to sit nearest in the lookback window, which may
belong to an unrelated earlier instruction.

Confirmed on Wizardry 6 (SNES): a DMA-size census scanned all 72 `STA
$420B` (MDMAEN) trigger sites for the nearest preceding `LDA #imm16` before
a `STA $43x5`/`$43x6` (DMA size register) write, and flagged two ~35KB
"candidate large transfers" (36223 and 36130 bytes) — numbers plausible
enough to read as a full-screen bitmap upload, exactly the kind of thing
worth chasing for a title-screen search. Hand-disassembling the actual call
site refuted it outright: the real size register was fed by `LDA
$8a8149,X` (an indexed table read), and the heuristic had matched an
unrelated stray `LDA #imm16` a few instructions earlier in the same
60-byte lookback window that belonged to a *different* register load
entirely. The call site turned out to be an already-known, table-driven,
per-call-variable-size DMA dispatcher — no large fixed transfer existed at
all; the two "large size" numbers were pure heuristic noise.

**Fix:** treat any census-derived operand *value* (as opposed to operand
*presence*, e.g. "this instruction form occurs here") as a hypothesis, not
a fact, until the specific instruction immediately feeding the register is
hand-verified. A quick tell that the heuristic has failed: the size/address
"discovered" this way came from a `LDA #imm` several instructions removed
from the target `STA`, with an indexed/table-read (`LDA addr,X`/`,Y`)
sitting *closer* to the target than the immediate the heuristic picked —
if a closer, non-immediate write to the same register exists, the
heuristic's answer is wrong by construction. This is the operand-*value*
sibling of `indexed-operand-needs-base-provenance.md` (which covers
operand-*identity*/base-register provenance for indexed addressing) — same
root fix in both cases: resolve back to the actual instruction that writes
the value/register, proximity in a byte window is not evidence.
