# Cross-platform ports are decode oracles — for code too, not just data

**When it bites:** stuck cracking a data format, or stuck tracing a routine's caller in disassembly with no symbols.

Same-game DOS/Windows data often has identical structure with different
endianness or no compression at all — Black Crypt's `bcdfs` (Amiga) vs
`maindung.gam` (DOS); WIME's DOS `GAMI` mirrors Amiga `IMAG`. Decode the easy
platform first, then map back.

Extends to **code**: if a reference disassembly exists for another
platform's build of the same game, byte-pattern-search the target binary for
that routine's own immediate operands (`MOVE.L #imm,Dn` constants are often
near-unique) to find the equivalent routine directly — this sidesteps a
stuck caller-tracing problem entirely. Cracked FE2's savegame cipher this way
after a linear-disassembly caller search had failed.
