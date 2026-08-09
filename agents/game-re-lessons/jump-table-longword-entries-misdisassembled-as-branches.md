# A jump table's raw absolute-address entries can disassemble as plausible-looking (but wrong) branch instructions

**When it bites:** you're hand-deriving an indirect jump table (`MOVEA.L
table(PC,Dn.W),An ; JMP (An)` or similar absolute-address-per-entry shape,
not a table of PC-relative displacements) from a committed IRA/disassembler
listing, and the listing shows each table slot as a real-looking branch
instruction (`BEQ.S`, `BVC.S`, `BVS.S`, ...) with its own computed target
label — especially if two or more slots show *different* target labels
that you're about to read as "these route to different handlers."

A linear disassembler doesn't know a byte range is a jump table of raw
4-byte absolute addresses rather than executable code — word-aligned data
that happens to start with a byte matching a real opcode (`0x67`=`BEQ`,
`0x68`=`BVC`, `0x69`=`BVS`, etc.) gets disassembled as that instruction,
and the disassembler computes a PC-relative branch-target **label** from
its own address plus the following byte(s) — a label that is completely
meaningless for data being read as an absolute longword via `MOVEA.L`/
indirect JMP, not executed as a branch. The label still *looks* like a
normal, plausible symbol name, which is what makes this dangerous: nothing
about it signals "this is wrong."

Confirmed on Wings (Amiga)'s Mode-B decompression dispatch table
(`LAB_675C`, hunk0 CODE+0x675c, a 16-entry table of raw 4-byte target
addresses read via `MOVEA.L table(PC,D0.W),A0 ; JMP (A0)`): two of the
16 slots showed IRA-generated labels `"BVC.S LAB_6768"` and
`"BVC.S LAB_676C"` — different target names, suggesting two different
handlers — but their raw hex bytes (`68 d8` in both cases) were
byte-identical, and as a real 4-byte absolute address the correct
resolution was the same target (`CODE+0x68d8`) for both table slots. IRA's
displayed labels differed only because it computed each one's *branch*
target relative to its own differing address — a real, working
computation, just applied to the wrong interpretation of the bytes.

**Fix:** for any table read via absolute addressing (not PC-relative
branch/BSR), ignore the disassembler's computed instruction mnemonic and
target label entirely — read the **raw hex bytes** shown after the `;`
comment for each table slot directly, concatenate them per the table's
real entry width, and interpret as the raw value the actual code says it
is (here, a big-endian 32-bit absolute address). Cross-check by comparing
raw bytes across slots before trusting that two different-looking labels
mean two different targets — identical raw bytes always mean identical
targets, regardless of what the disassembler labeled them.
