# Cleanly-parsing script operands can be vestigial — the port's executable overrides them from a hardcoded table

**When it bites:** a bytecode/script decode is structurally flawless (0
unknown opcodes, 0 desyncs, operands in-range with plausible sentinels),
yet the decoded parameter values resolve only partially or inconsistently
against the real resource directory — and you're about to explain the
misses as a decode error, a second id space, or corpus damage.

Parsing an instruction's operands answers "what does the script say". It
does not answer "what does the engine do with what the script says" — and
a platform port is free to ignore the script entirely. Ports routinely
ship the script corpus byte-identical from the lead SKU (usually DOS) and
patch behavior in the *engine*, so operand values that were live on the
original platform can be stale, dead data on the port you're decoding.

Confirmed on Treasures of the Savage Frontier (Amiga, SSI Gold Box,
`crawl` project): the ECL bytecode's area-setup opcodes (`0x21` LOAD
FILES, `0x42` LOAD AREA) carry per-level wallset-slot operands that parse
perfectly — but the Amiga executable's `getAreaWallsets`
(`ECLTABLE`-side handler chain, Treasure exe file+`0x14B24`) checks the
geo id and, for every dungeon geo 16-50, **unconditionally overwrites all
three wallset slots from a 35-entry jump table hardcoded in the
executable** (file+`0x14D78`) before `LoadWalldef` ever sees a value. The
ECL operands are DOS-build leftovers; at least one was provably wrong
against its own level's GEO wall-type needs. The overriding table, not
the bytecode, verified 87/87 slot values inside the real `WallDef.glb`
directory (after the handler's own hardcoded id remap `15→32`), with a
slot-needs cross-check from the level grids passing where the raw ECL
operands had failed it.

The tell and the fix:

- **Tell:** a 0-error stream walk plus partial/inconsistent resolution of
  the *values* against the resource directory. Perfect syntax + broken
  semantics means the consumer isn't consuming what you think.
- **Fix:** trace the opcode's handler **past the operand read** to the
  actual resource-load call, watching for (a) an id-range gate keyed by
  the same id the script passes, (b) a table lookup replacing the operand
  registers, and (c) small hardcoded remaps (`15→32`-style) near the
  loader. On the engine's original platform the same handler may use the
  operands directly — so a sibling-port reference implementation "using
  the operands" is not evidence your port does.

Sibling failure modes, related but distinct:
`partial-resolution-rate-is-noise.md` (partial rate = a missing
*transform* on the data — here the data is not transformed but discarded
outright); `embedded-palette-not-the-installed-palette.md` (the same
parsed-is-not-installed principle for palettes);
`reference-tool-field-never-consumed-by-its-own-importer.md` (a reference
tool's parser reading a field its own importer never uses).
