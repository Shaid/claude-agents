# CPS2 (and similar) decrypt input must be the raw ROM dump, not the loader's byteswapped region

**When it bites:** a byte-exact-verified cipher/decrypt port (confirmed
correct via table transcription, or byte-identical against a trusted
reference tool) produces a nonsense result on real data — specifically a
CPU reset vector, jump table, or other address-shaped field whose top
byte(s) fall outside the platform's real address space — and you're about
to suspect the cipher itself, the key, or the encrypted-range bounds.

## What went wrong

CPS2's 68000 program ROMs are dumped as raw chip files and loaded into
MAME's "maincpu" memory region via `ROM_LOAD16_WORD_SWAP` — a per-16-bit-
word byteswap applied at load time (confirmed against `src/emu/romentry.h`
and `romload.cpp`'s `read_rom_data()`). It's natural to assume the CPS2
decryption cipher (a Feistel network keyed off the ciphertext word) should
be fed that same, correctly-loaded "maincpu" region — after all, that's
what the real 68000 core reads from at runtime.

It is not. MAME's real `cps2_decrypt()` (`src/mame/capcom/cps2.cpp`) is
handed `memregion("maincpu")->base()` **cast to `uint16_t*`** — i.e. it
reads each source word via a *native* host 16-bit load (little-endian on
x86) from a region whose bytes the loader stored in **big-endian** order.
Reading big-endian-stored bytes through a little-endian load reverses them
a second time, which exactly cancels the loader's own swap back out. The
net effect: the cipher actually consumes the **original, un-swapped dump
byte order**, not the loader's logical big-endian region.

Confirmed by direct experiment on D&D: Shadows over Mystara (ddsom, CPS2):
decrypting the swapped region gave `SP=0xfc601869` (top byte far outside
the 24-bit address space — implausible); decrypting the raw, un-swapped
concatenation of the same files gave `SP=0x00ff0e66, PC=0x00000350` — a
plausible work-RAM stack pointer and ROM entry point, further confirmed by
60+ consecutive valid, coherent 68000 instructions disassembling at that PC
(including the exact watchdog instruction independently decoded from the
key file). Cross-checked byte-identical against radare2's own `cps2` muta
plugin (`r2 -c "woD cps2 <key>"`) on the same raw input.

## The fix / the generalizable lesson

When a MAME-sourced (or similarly-modeled) decrypt/transform function's
*real* C++ implementation reads its input through a raw pointer cast
(`(uint16_t*)region->base()`, or equivalent) rather than through the
region's own typed/endian-aware accessor, the cast's host-native byte order
can silently interact with — and partially or fully cancel — a loader-time
byteswap that was applied for a *different* consumer (the CPU core's normal
memory access). Don't assume "the cipher operates on the same bytes the
CPU sees" — trace (or test) whether the specific function you're porting
uses a raw/native-typed pointer into an already-transformed region. When in
doubt, empirically test both the swapped and un-swapped input against a
structural oracle (an address-shaped field's plausible byte pattern) rather
than assuming the "obviously correct" already-assembled region is what the
reference function actually consumes.
