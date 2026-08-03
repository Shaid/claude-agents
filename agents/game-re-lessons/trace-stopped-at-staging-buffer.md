# A traced "consumer" that writes a staging buffer is not the consumer

**When it bites:** a routine you (or a prior session) already documented as
"confirmed" ends its cited address range at a `RTS`-less address, or the
documented behaviour is "copies N words into buffer X" and buffer X is not a
hardware register, a DMA source, or anything the doc can name a role for.

## The trap

A prior Wizardry 6 (SNES) session traced the piece blitter at
`0x01E25A`-`0x01E2EB`, wrote up a correct record layout, and concluded the
payload words were "tilemap entries — indices into CHR already resident in
VRAM", destination `$7E:4000`. Everything in that write-up was *true* and
every byte of it verified. It was also the wrong routine boundary: the code
runs to `0x01E3B8`, and `$7E:4000` is a per-piece scratch buffer that is
rewritten from index 0 for every piece.

The 205 bytes after the assumed endpoint held the entire mechanism:

- the words are ROM **tile-pool references** carrying their own 4-bit bank
  field, not VRAM tile numbers;
- placement is `destByte = x*32 + rowTable[y]` into an 18x15 software
  bitmap in a *different* WRAM buffer;
- a parallel occupancy array implements a near-to-far painter's algorithm
  with an opaque-copy path and a per-pixel merge-behind path.

Because the earlier trace stopped at the staging copy, three sessions of
whole-ROM byte censuses went looking for a "dungeon renderer" that was
already sitting 205 bytes past an address the docs called confirmed.

## Why the stopping point looked reasonable

The staging loop ends in a clean nested `DEC`/`BNE` pair that *looks* like
the end of a routine, and the next instruction is `SEP #$20` — a plausible
epilogue. It is actually the prologue of the second phase, which re-banks
`DBR` and starts over with a new loop.

## The rule

Before writing "confirmed" against a routine's address range, **prove where
it ends**: disassemble forward until an actual `RTS`/`RTL`/`RTI`/unconditional
`JMP`, and say so in the doc. If a traced routine's only externally visible
effect is a write to RAM that nothing else in your notes reads, you have
found a stage, not the consumer — keep going, or record the buffer as an
open lead rather than as the answer.

Corollary for re-reading someone else's trace: a cited range whose end
address is *not* a return instruction is the single cheapest thing to
re-check, and it costs one disassembly call.
