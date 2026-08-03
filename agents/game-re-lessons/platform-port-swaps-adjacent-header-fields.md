# A "same container, different endianness" port can still swap adjacent same-size header fields — or add a whole sub-region a sibling format doesn't have

**When it bites:** a sibling platform's build of the same game shares a
confirmed-identical container/frame-directory structure (verified via some
structural invariant — expression counts, canvas dimensions, tick counts),
but a downstream decode still produces impossible-looking values or a
byte-count mismatch that's roughly proportional but not exact — and the
current fix attempt is "add an endian option and read the same fields in
the same order, just with the other word width." Also fires across
*sibling games on the same engine* (not just platform ports of one game):
reusing an already-confirmed decoder for "the same format, just a different
title" without re-reading that title's own loader function first.

Confirming a container's *shape* (directory layout, table sizes, byte
offsets of multi-byte fields) is identical across two platform ports does
**not** prove the *field order* inside a small fixed header is identical
too. A straight platform port can swap two adjacent same-width fields
(e.g. two `u8`s) for reasons unrelated to endianness — different struct
packing in the source compiler, or simply an independent reimplementation
of the same asset pipeline — while every multi-byte numeric field elsewhere
in the same container reads correctly under a pure byte-order flip. The
symptom is deceptive: because both misread fields are still "real" data
from the file (not garbage), the wrong reading produces plausible-looking
but arithmetically-impossible values, e.g. a computed pixel index appearing
to exceed what the pixel format's bit depth allows, or a decompressed
payload length that's a similarly-scaled but not-exact multiple of the
expected size — errors that look like a bit-depth or compression bug, not
a field-order bug.

**Disambiguating technique**: when a small header has two same-size fields
whose individual roles are only inferable (not directly labeled by a
symbol table or disassembly), test **both** possible orderings against a
corpus-wide structural invariant — not just the one file under
investigation. Compute an expected payload size from each ordering's
candidate "count"/"dimension" field (e.g. `rowStride(width) × height`) and
compare against the actual decompressed/declared byte length for every
frame in every file of the format. The correct ordering should close
exactly (0 discrepancy) on the overwhelming majority of frames; the wrong
ordering will be off by a scaled, non-constant amount because it's
computing the stride from an unrelated field. A single-file check can be
fooled by coincidence; a corpus-wide exact-match rate (in one confirmed
case: 0% on the wrong ordering, 98.3% on the correct one, with the
remaining 1.7% isolated to one unrelated file) is decisive.

Confirmed on Dune (Cryo Interactive), DOS VGA vs. Amiga: both platforms
share one 4-byte sprite frame header — `[wflags u16][byte][byte]` — but
Amiga orders the two trailing bytes as `[paletteBase][height]` while DOS
orders them `[height][paletteBase]`. Reading DOS with Amiga's field order
(while correctly handling the u16 endianness elsewhere) made a real
`paletteBase` byte look like an impossible height and a real `height` byte
look like an already-masked palette index — producing exactly the
"pixel values look impossible for the bit depth" and "decoded length off
by roughly 2×" symptoms that had independently stalled two earlier
investigation passes. Swapping just those two byte reads (no other change)
took the corpus-wide frame-size match rate from ~0% to 98.3% and fixed
composited character portraits from solid black to correctly-coloured,
recognisable art. A related, compounding trap on the same bug: the source
platform's field also carried a hardware-width bitmask (`& 0x0f`, valid
for Amiga's 32-colour palette) that does not apply on the target platform
(DOS's 256-colour palette needs the full unmasked byte) — when a port
changes address space or resource limits (more palette slots, more memory,
wider registers), check whether a masking/clamping operation tied to the
*source* platform's specific hardware limit was carried over unexamined.

**Second confirmed case — not a field swap, a whole extra sub-region a
sibling *game* on the same engine doesn't have.** Lands of Lore and Eye of
the Beholder (both Westwood "Kyra" engine, `crawl` project) share
byte-identical `.VCN` wall-tileset container framing and the exact same
downstream 8×8/4bpp tile-packing format — confirmed structurally (LCW
wrapper, tile stride, nibble unpacking all matched). A shared decoder
written against EOB's format (`numTiles` u16, then a **fixed** 32-byte
palette-index remap table, then tile data starting at a fixed offset 0x22)
was reused unchanged for LOL's `.VCN` files. It silently decoded garbage
data as "tile pixels" for every LOL file: LOL's real header is
**variable-length** (`numTiles`-sized per-tile shift table, then a fixed
128-byte remap table, then a fixed 384-byte **embedded palette** — a
region EOB's format doesn't have at all — *then* tile data), so the fixed
0x22 offset landed inside LOL's shift/remap/palette region instead of the
real tile data, for every file. This went undetected across an entire
prior session because the *outer* structural invariant (declared
decompressed size == actual decompressed length) still passed — that
invariant only proves the *total* payload length, not that a sub-region
inside it starts where a borrowed parser assumes it does — and because a
greyscale render of the misread bytes still looked like "some texture"
rather than obvious noise (the shift/remap/palette bytes are themselves
smallish structured values, not random). The actual fix required reading
the sibling *game's own* loader function line-by-line
(`LoLEngine::loadLevelGraphics`) rather than trusting that a
structurally-confirmed-identical container framing meant an identical
*internal offset layout* too. Once corrected, two previously-magenta
placeholder palette indices resolved to real, plausible RGB values,
confirming the fix. **Never port a decoder for "the same format" from one
game to a sibling game on the same engine without re-reading that
specific game's own loader function** — matching container/codec framing
is not proof of matching internal header layout, even when both are true
"the same engine" and even when a coarse size-based structural check
keeps passing throughout.

**Third confirmed case — two sibling games on the *same platform* (not a
port at all), same publisher, same console generation.** Final Fantasy V
and VI (both SquareSoft, SNES, `ceres` project) share high-level format
*shape* for two independent structures — an LZSS codec with the same 2KB
ring-buffer/8-token-line design, and a monster-graphics system built from
the same packed-pointer-plus-stencil-trimmed-tiles concept — yet neither
one's low-level bit-packing carries over. LZSS: FFVI's 2-byte header is the
*compressed* length (counted inclusive of itself); FFV's is the
*decompressed* length. FFVI's back-reference token packs a little-endian
16-bit word (offset in the low 11 bits, length in the high 5); FFV packs
the same two values byte-order-reversed (offset low byte first, then a
byte with the offset's high 3 bits and the length in the low 5). Monster
graphics: FFVI's packed graphics-pointer field is little-endian with the
3bpp flag in the second byte's top bit; FFV's is big-endian with the 3bpp
flag in the *first* byte's top bit. Both were caught immediately by
re-deriving each field from that specific game's own disassembly rather
than reusing the sibling game's already-confirmed decoder, and both would
have produced silently-wrong (not obviously-broken) output if reused
unmodified — LZSS would have picked the wrong loop-termination quantity
without erroring, and the graphics pointer would have resolved to a
plausible-looking but wrong offset. **Same publisher + same console
generation + same conceptual format is not evidence of byte-compatible
encoding — it's only evidence the same *engineers* built something with
the same shape.** Budget for full field-by-field re-derivation against
each sibling game's own code, every time, even when the abstract algorithm
description ports over perfectly.
