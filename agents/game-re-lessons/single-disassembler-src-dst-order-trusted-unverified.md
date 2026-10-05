# A copy-direction finding (which address is source, which is destination) needs a second, independent disassembler before it's trusted

**When it bites:** a critical conclusion depends on which of two operands in
a `MOVE`-shaped instruction is the source and which is the destination —
e.g. classifying a `move.b (a1)+,(a0)+`-style copy loop as "restores A from
B" vs. "commits B into A" — especially on an ISA (68000/Motorola syntax,
among others) whose assembly convention writes `src, dst` rather than the
more familiar `dst, src`, making it easy to misremember or hand-derive the
wrong direction even when the disassembly text itself is correct.

The risk isn't that the disassembler is wrong — it's that a *reader*
transposes the two operands while reasoning about the output, or that an
existing doc's claim about the direction was itself inferred from
structural/arithmetic evidence (address ranges, byte counts matching a
known figure) rather than from an actually-disassembled copy loop, and
nobody re-derived it from the real instruction once the loop was finally
found.

Confirmed on Deuteros (Amiga, `methanoid` project): an existing doc
described a `$66000`<->`$13006` data mirror as one-directional
(`$66000 -> $13006`, a "restore"), based entirely on address-range and
byte-count arithmetic — no disassembled copy loop had ever actually been
cited. A follow-up session found and disassembled a second, previously
undocumented copy loop, `move.b (a1)+,(a0)+` with `a1=$13006` (via `movea.l
#$13006,a1`) and `a0=$66000` (via `lea.l $66000.l,a0`) — the OPPOSITE
direction of the documented one, and (correctly) confirming the two form a
genuine bidirectional mirror pair rather than the single direction
previously assumed. The finding was cross-verified two ways before being
trusted: (a) hand-deriving the raw opcode's bit fields for the `MOVE.B`
encoding (destination register/mode in bits 11-6, source in bits 5-0) to
confirm r2's `src, dst` operand-order convention independently, and (b)
re-disassembling the identical byte span with Python capstone
(`Cs(CS_ARCH_M68K, CS_MODE_BIG_ENDIAN|CS_MODE_M68K_000)`), which agreed with
r2 byte-for-byte on both the operand order and a known-good reference
instruction (`move.l d0,$12fec.l`, whose semantics were already confirmed
against the game's own already-verified behavior).

**Fix:** for any finding where the whole conclusion hinges on which operand
is source vs. destination, don't stop at one disassembler's text output.
Either (a) hand-verify the opcode's bit-field encoding against the ISA's
own manual for at least one instance, or (b) re-disassemble the same bytes
with a second, independently-implemented tool (capstone is a good default
— cheap, scriptable, widely ported) and require both to agree. Also
re-check any existing doc's directional claim for the same red flag: was it
ever actually grounded in a disassembled instruction, or only in
plausible-sounding arithmetic (an address falling in a known range, a byte
count matching a previously-established figure)? Arithmetic can confirm
*that* two addresses are related; only the instruction itself says which
way the data flows.
