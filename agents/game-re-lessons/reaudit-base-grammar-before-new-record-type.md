# When residue survives 2+ new-record-type hypotheses, re-audit the primary grammar's own foundational premises

**When it bites:** a data-record parser leaves unexplained residue, you've
already tried and refined more than one "there's a second record type
hiding in the gaps" theory (partial success, still some residue left over
each time), and you're about to reach for a third variant of the same
move — a third record-type shape, a third tag-byte guess — instead of
questioning the primary grammar itself.

Confirmed on Epic (Amiga)'s `.3D`/`.IGD` model format: three *separately
plausible* premises were each individually reasonable and jointly wrong —
(1) "the vertex count can't be recovered from the file, it must be supplied
externally" (actually the first word of the section body — nobody had
looked there because it read as a header field, not body data), (2) the
vertex table's base offset (off by the exact width of the missing count
field, `0x30` vs. the correct `body+2`), and (3) "what follows vertices is
an array of variable-length face records" (it's an opcode-driven display-
list bytecode; a face-record grammar happened to *almost* fit because two
of its opcodes carry `opcode+1` vertex indices, mimicking the old
`edges`/`index[n+1]` shape closely enough to pass validation most of the
time). Two full rounds of "maybe there's a second record type in the gaps"
(a plausible-but-incomplete hardpoint-chain reading, then a refined resync)
each recovered more of the residue without ever reaching zero, because the
real defect wasn't a missing record type at all — it was in premises (1)
and (2), upstream of where the record-type hunt was even looking. Only
disassembling the game's own loading/compile-pass code (not attempted for
this specific question across a dozen-plus prior static-analysis passes)
settled all three at once.

**The fix:** after a second record-type hypothesis still leaves residue,
stop iterating on record-type shape and instead re-derive, from scratch,
the primary grammar's own foundational claims — where does the count/length
live (check the field immediately preceding the array, not just a header
region), what is the true base offset the array starts from, and is the
record shape itself confirmed against an independent oracle (disassembly,
a working reference implementation) or just "parses without crashing on
the two files you have." A residue that partially yields to each new
record-type theory but never reaches zero is itself evidence the model is
incomplete at a level *below* record typing, not evidence you haven't found
enough record types yet. This is the process-discipline half of
`bytecode-residue-recurring-groups.md`'s structural tell — use both
together: the recurring-groups pattern tells you residue might be a
program; this lesson tells you when to stop patching the grammar and start
re-deriving it.
