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
heuristic's answer is wrong by construction.

**What *does* upgrade a literal-argument census to evidence: how the callers
test the result.** The heuristic isn't useless — it's a hypothesis generator,
and there's a cheap corroboration that turns it into a finding. Valkyrie
Profile (PSX, `valkyrie`): an engine routine documented only as "RNG utility"
(507 modules, 2,658 calls) had no recorded ABI. The nearest-preceding-immediate
census over its `a0` gave a histogram of `2`×341, `10`×236, `100`×212,
`16`×210, `4`×194, `8`×179, `24`×140, `32`×104, `256`×86, `512`×65, `2048`×60
— suggestive of a modulo bound, but by itself exactly the guess this file
warns about. What settled it was a single call site that *consumed* the
result: `a0 = 256` followed immediately by `sltiu $v0,$v0,129`, a ~50/50 gate
that is only meaningful if the return spans `0..255`. Argument shape proposed
`rand() % a0`; the caller's own comparison against a constant pinned the range
and confirmed it. Generally: for an unknown callee, the immediately-following
compare/mask/shift on its return value is often a tighter constraint on its
semantics than anything on the argument side, and it is real dataflow (same
register, adjacent instructions) rather than a lookback guess.

**A bare instruction-word literal-value scan is noisier still than a
nearest-preceding-immediate census, and the fix needs a directional window,
not just a shape filter.** Confirmed on Valkyrie Profile (PSX, `valkyrie`),
4th pass on `vp1psx-slot4807-sacred-phase`: hunting for any compiled
reference to two persistent-flag ids (`0x448`, `0x4ce`) across an 8-overlay
corpus, a first-cut scanner just tested whether an instruction word's low 16
bits equalled the target constant — no opcode-shape filter at all. It
flagged 100+ hits, all coincidental: common round values (`0x400`=1024) and
struct-field offsets (`0x4ce`=1230) turn up constantly in ordinary
coordinate/fixed-point arithmetic and struct-offset immediates, with no
relation to a flag-id argument. Narrowing to the established shape —
`addiu`/`ori` loading an immediate into an argument register — cut this
drastically but still left one false positive: `addiu $v0,$v0,0x400` two
instructions after an unrelated `jal`, where the immediate was post-call
arithmetic on the *previous* call's return value, not argument prep for a
call that hadn't happened yet. A symmetric ±N-instruction adjacency window
around the `jal` cannot tell these apart. **Fix:** require the immediate
load to sit at the call's own delay slot (`jal` at offset −4) or in the 1-2
instructions immediately *before* the `jal` (argument prep happens before a
call, never meaningfully after it for that call) — a `jal` appearing
*before* the immediate load is somebody else's call, not this one's.
Combined with a same-technique win: this pass also independently confirmed
a whole 66-entry data-table's GetFlag/SetFlag argument column by requiring
the identical directional shape (`lhu $a0,OFF($base)` then `jal` within the
same window) rather than any bare-value match, and it correctly returned
zero hits for both target flags — a clean negative, not silence from an
under-filtered scanner. See
`docs/valkyrieprofile/psx/data-structure.md` §§ 20.27-20.28 and
`tools/valkyrieprofile/probe-sacred-phase-worldmap-states8-13.ts` for the
worked scanner (`scanFlagArgSites`).

This is the operand-*value*
sibling of `indexed-operand-needs-base-provenance.md` (which covers
operand-*identity*/base-register provenance for indexed addressing) — same
root fix in both cases: resolve back to the actual instruction that writes
the value/register, proximity in a byte window is not evidence.
