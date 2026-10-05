# Merging "read N bytes, no other effect" opcode cases during promotion can silently drop one case's real state mutation

**When it bites:** promoting/porting a bytecode or event-stream
interpreter's opcode dispatch (a music-sequence track format, a script VM,
any tagged-record grammar with many single-purpose control opcodes) and
consolidating several opcodes that all *look* like "consume one operand
byte, do nothing else" into one shared `switch`/`case` branch for brevity —
when one of those opcodes actually mutates a piece of shared interpreter
state that a *later* opcode's own computation depends on (not just a value
the caller reads back). Structural verification (does decoding terminate
cleanly, are byte counts right, does every opcode get consumed) passes
either way, because the bug never desyncs the byte stream — it only
changes computed *values*.

Confirmed on D&D: Shadows over Mystara (CPS2, `kolbold`)'s CPS2 music-track
decoder, ported from vgmtrans's `CPS2TrackV1::readEvent()`: an early draft
merged event `0x09` ("Set Octave", which does
`noteState = (noteState & 0xf8) | operandByte`) into the same case as
`0x06`/`0x07`/`0x0a`-`0x0d` (which really are pure single-byte-consuming
no-ops for this decoder's purposes) — since `0x09`'s own code shape (`read
one operand byte, curOffset++`) looked identical to its neighbors at a
glance. This silently dropped every octave change; every subsequent note's
computed key used the wrong (default) octave. The bug was invisible to
every structural check: 100% of tracks still decoded to a clean terminator
with the identical total note *count* (67,695) either way — the only
observable difference was the corpus-wide note-*key* range (0-48 instead
of the correct 10-99).

**The check that catches this**: after porting an opcode table, verify
actual decoded *values* against an independent implementation or hand
trace for at least one non-trivial input — not just "does it terminate" or
"are the byte counts self-consistent." Before consolidating opcode cases
for brevity, explicitly ask of each one individually: does this write to
any field the interpreter reads *elsewhere*, not just a field the caller
reads back once? A field mutated once and read many times later
(`noteState`/an octave or key-signature register, a running counter, a
loop-nesting flag) is exactly the shape that a "looks like a no-op"
consolidation misses.
