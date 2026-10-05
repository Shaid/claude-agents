# A confirmed hardware attribute word's spare bits can be repurposed by the game for its own bookkeeping

**When it bites:** a hardware-defined attribute/flag word's bit layout is
confirmed from an authoritative source (chip documentation, an emulator's
own render code) and leaves some bits undocumented/unused by the hardware
itself, and you notice real disassembled code **reading that word back**
(not just constructing and writing it once) — especially followed by a
rotate/shift + mask + jump-table pattern.

A "confirmed format" from hardware documentation only tells you what the
*rendering hardware* consumes from a word; it says nothing about whether
the *game's own code* also uses the same storage for something else. If a
word has bits the renderer never reads, the game author may have quietly
repurposed them as free per-instance storage riding along with data the
hardware already required anyway (no separate allocation needed).

Confirmed on Knights of the Round (CPS1): the scroll-layer tile attribute
word's hardware-consumed bits are 0-8 (palette bank, flip X/Y, priority
group — per MAME's `get_tile1_info()`/`get_tile2_info()`). Real disassembled
game code (maincpu `0x7afc`-`0x7b46`) reads a stored scroll2 attribute word
back, rotates it (`rol.w #6`) and masks it (`andi.w #$3f`) — extracting
exactly bits 10-15, which the hardware's own renderer never consults at
all — then uses the extracted value to index a further jump table. The
game is using spare bits in an otherwise fully hardware-documented word for
its own bookkeeping (a tile-interaction/collision dispatch here), with zero
conflict with the hardware's own interpretation of the same word.

**Fix:** when a confirmed hardware word format leaves bits the
renderer/hardware never reads, don't assume they're simply reserved/unused
padding just because the hardware doesn't care about them. A read-back
(not just a write) of that same word elsewhere in the disassembly — one
you'd otherwise skip past as "already understood, it's just the attribute
word" — is a cheap, strong signal worth a quick trace: it often reveals the
game repurposing exactly the bits the hardware format leaves spare.
