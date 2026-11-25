# A shifted opcode table garbles one opcode range while the rest decodes cleanly

**When it bites:** a project-local disassembler (shader ISA, script VM,
custom bytecode) prints arithmetic cleanly but leaves flow-control ops raw /
"unknown", or decodes them into absurd jumps. It is tempting to read this as
"data embedded in code" or "an unsupported encoding" and work around it.

**The trap:** one entry inserted or missing in a hand-typed opcode table
shifts every opcode after it by one. Ops below the shift decode perfectly,
which looks like proof the decoder is sound; ops above it decode as their
neighbour (`end` read as `nop`, `cmp` read as a jump). Control flow becomes
unreadable, and any data-flow reading taken from it is wrong.

**Check / fix:** assert structural invariants a correct table must satisfy:
- every call/if/jmp target (+ length) falls inside the program;
- every program/entry point ends in the terminator op (`end`);
- the same subroutine decodes identically across every variant/program that
  contains it.

Then diff the table against the ISA reference entry by entry around the
first bad opcode. Null control: a one-word-shifted read of the same
subroutine should *fail* the identical-decode check. When the table was
generated from a reference, splice it verbatim
(`hand-transcribed-generated-table-drifts-from-source.md`).

**Canonical example:** lucina/seer PICA200 `shbin` disassembler
(`packages/3ds/src/shbin.ts`): `end` at 0x21 and `cmp` at 0x2d were both off
by one. After the fix a 10-instruction hemisphere-lighting subroutine decoded
identically in 40/40 DefaultShader variants (0/40 for the shifted null) and
0 of 1,000+ flow targets fell out of range, so the vertex-colour math could
be read from code instead of guessed from uniform names.

**History:** 1 instance (lucina, 2026-11).
