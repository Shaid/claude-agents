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
title" without re-reading that title's own loader function first. Also
fires when a two-field-swap fix's own verification formula is symmetric in
the two candidate fields (e.g. `width×height`-shaped) — that formula
cannot distinguish "correct order" from "swapped," no matter the corpus
size, and a real bug can hide behind it across a whole later investigation
session that (wrongly) chases a different mechanism entirely.

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

**But check the check itself for symmetry first — some verification
formulas are mathematically incapable of catching this bug at all**, no
matter how large the corpus. If swapping the two candidate fields' values
leaves the formula's result unchanged, the formula can only prove "these
are the right two numbers," never "they're in the right slots." The fifth
confirmed case below is exactly this trap; the general-purpose fix is
scoping the disambiguating byte-accounting check (above) to instances where
the two fields' values actually *differ* — a width×height-style invariant
is only a real test of field order when width ≠ height.

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

**Fourth confirmed case — a *standard external hardware format*, not a
studio-authored one, still gets its field order swapped in one game's
in-house container.** Fire Emblem: Three Houses' `.ktsl2asbin`
(`ktgcadpcm.ts`, `chimera` project) wraps a 96-byte per-channel DSP-info
block that is the *same* physical size as the standard Nintendo GC/Wii
DSP-ADPCM header (`0x60` = 96 bytes) used verbatim elsewhere in the same
engine family (Three Hopes' `asrs-ktsr.ts`, byte-for-byte confirmed
against that standard layout on 14,133/14,133 real channels: `+0x00
numSamples`, `+0x04 numNibbles`). An earlier pass on Three Houses had
those same two `u32` slots backwards — `+0x00` labeled `nibbleCount`
(left unused) and `+0x04` labeled and *used as* `sampleCount` — with a
`floor(streamSize/8)*14` clamp bolted on to stop the resulting over-long
reads from walking into the next voice line's header. The clamp mostly
worked (only a handful of trailing samples per stream were lost), which
is exactly what let the mislabel hide for a whole pass: the decoded audio
sounded fine. Re-verified corpus-wide (all 263 real `.ktsl2asbin`
entries, 14,847 channels) with the same disambiguating technique as
above — compute the exact byte count needed to decode `field(@0)` samples
and compare against the channel's own declared `streamSize` — and it
closed **exactly, 0/14,847 deviations**, while `field(@4)` was larger
than `field(@0)` in **100% of channels**, consistent with `@4` really
being total-nibble-count (which is always >= sample count, since it
includes 2 non-sample header nibbles per 16-nibble frame). Two things
worth carrying forward: (1) even a well-known, publicly-documented
*external* hardware struct (not just a studio's own bespoke format) can
still get its field order flipped by one game's specific encoder/muxer
pass, so "it's a standard format, the layout is known" is not a reason to
skip re-verifying against real bytes; (2) a workaround (the clamp) that
mostly produces correct-*sounding* output is not evidence the underlying
field read is right — it can be silently discarding real, decodable data
every time, and the byte-accounting invariant is what actually catches it
where casual listening/spot-checking would not.

**Fifth confirmed case — the "fix" itself introduced the swap, and its own
verification formula was symmetric and so could never catch it.** Three
Hopes' G1T texture format (`parseG1T` in `g1t.ts`, `chimera` project,
2026-09-06) has an "extra dims" header sub-block for textures whose
dimensions don't fit a packed log2 nibble: two `i32` fields, width then
height. An earlier pass correctly found that `width` was being read from a
constant-marker slot (always decoding as the literal `0x01000000`) and
moved it to the right slot — but swapped `width`'s and `height`'s *labels*
in the process. That fix's own verification — cross-checking the decoded
`width`/`height` against the texture's declared byte span,
`ceil(width/blockWidth) * ceil(height/blockHeight) * bpp` — passed on every
file checked, because the formula is symmetric: `ceil(w/4)*ceil(h/4)`
equals `ceil(h/4)*ceil(w/4)` for every `w,h`, so it validates "two correct
dimension values, in some order" and nothing more. The swap survived
undetected for another investigation session, misdiagnosed as an unknown
GPU texture-swizzle scheme (four independently-shaped decode attempts, all
failed): the underlying textures were never swizzled at all, just read
transposed (a 512×288 image decoded as 288×512). It was found by deriving
the real raster row stride from decoded block content directly — for each
block, which other block's edge best continues it (see
`verification-techniques.md`'s block-adjacency-derived-stride technique) —
which needed no format hypothesis and so was immune to the same blind
spot. A corpus-wide cross-tab confirmed the swap affected exactly the
non-square instances (1,298 of 1,678 extra-dims textures) and was a no-op
on square ones, which is also *why* it hid: every square instance (and
every instance still small enough for the packed-nibble path) looks
correct regardless of which label is on which field.
