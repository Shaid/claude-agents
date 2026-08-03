# A whole-file string scan can concatenate two unrelated things across a structural boundary into a fake token

**When it bites:** a plaintext/string search over a whole file or blob
finds a plausible-looking string that's a slight variant of an
already-known naming pattern (a different prefix, an extra character, an
unexpected case) — and you're about to treat it as a genuine, distinct
asset reference before checking what's immediately behind it.

Wizardry 6's DOS/EGA `winit.ovr` appeared to embed the string
`"QMON00.PIC"` — a plausible "Q-prefixed variant" of the corpus's
otherwise-universal `MON%02d.PIC` naming pattern, and different from
anything seen on the Amiga port. It doesn't exist. The file's compiled
code region ends, byte for byte, with a trampoline instruction
(`push cx; jmp word [ptr]`) whose final operand byte is `0x51` — which is
also ASCII `'Q'`. The data pool's genuine, ordinary string
`"MON00.PIC\0"` begins in the very next byte. A naive whole-file
printable-run scan reads across that boundary and reports
`"QMON00.PIC"` as if it were one token, because nothing about a
printable-byte scan knows that a code region ended one byte earlier.

The fix that caught it: once the code/data boundary was independently
known (from an unrelated invariant — here, a header field giving the
exact code-region length), disassembling the few instructions immediately
before the suspicious string's start showed a complete, ordinary
instruction ending exactly at the boundary, with its last byte
coincidentally printable. The "extra" leading character disappeared once
the scan respected the real boundary instead of just following runs of
printable bytes.

Generalizes beyond this one string: any plaintext scan over a
mixed code+data blob (no clean separation announced anywhere) can produce
phantom tokens by gluing together a printable tail byte of code (an
opcode, an operand byte, a padding byte) with the head of a real string
that happens to start right after it — especially likely when the
"discovered" string is *almost* a known pattern with one anomalous leading
character. Before trusting a variant-looking string as a real, distinct
reference: locate the real code/data boundary (a directory/header field,
a size invariant, or a disassembly-confirmed function end) and check
whether the anomalous character falls on the code side of it.
