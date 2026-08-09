# Stored tile order for a multi-tile sprite/portrait isn't always raster order

**When it bites:** about to compose a multi-tile sprite, portrait, or
metasprite by laying out consecutively-stored 8x8 (or NxN) tiles left-to-
right/top-to-bottom into the display grid, especially on a console with
hardware OAM/sprite composition (SNES, NES, Genesis) where the original
engine was free to store tiles in whatever order was cheapest to DMA/blit
rather than the order they're displayed in.

Confirmed on Final Fantasy VI (SNES, `ceres` project): 19 character
portraits are stored as 25 uncompressed 4bpp 8x8 tiles per portrait, and a
first-pass render walked those 25 tiles in raw stored order into a 5x5
raster grid. The result was *not* an obvious garbage/noise render — each
individual 8x8 block decoded correctly (right palette, right bit-plane
math, recognisable skin/hair/fabric colour patches) but the blocks landed in
the wrong grid cells, producing a plausible-looking but scrambled, generally
unrecognisable face. This is a more dangerous failure mode than a clean
decode error: a low-confidence pass could plausibly log it as "portrait
graphics decoded, palette/positioning slightly off" and move on, rather than
catching the real bug.

The fix was a **tile-formation/reorder table**: a small, separate table
(25 bytes here, one per display cell, each byte naming which stored-tile
index goes in that cell) that the original engine's own composition code
reads before blitting. It was found in a public disassembly's field-object
code (`everything8215/ff6`, `src/field/obj.asm`, `PortraitTiles`) rather
than derived by trial and error — once applied, all 19 portraits rendered as
immediately recognisable game characters (Terra's green hair, Locke's
bandana, Umaro's white fur, etc), which is the actual confirmation, not the
existence of the table itself.

**The general check:** before trusting a raster-order tile-composition
render as correct, verify it against something you can actually recognise
(a face, a logo, legible text) — don't stop at "the tiles individually
decode to sensible-looking pixel data." If the composed image is
plausible-shaped but not clearly *identifiable*, suspect a missing
formation/reorder table before suspecting the palette or the bitplane
decode. Community disassemblies/reimplementations for the exact game are
the cheapest place to find such a table (see
`romhacking-community-tools-first.md`); absent one, the table can also be
recovered by treating the tile-to-cell mapping as an unknown permutation
and brute-forcing against a known symmetry (e.g. a portrait's likely
bilateral near-symmetry) or a partially-legible feature (an eye, a mouth)
whose expected position is known from the sprite's bounding shape.

**Having "the reader" (Method §2) doesn't make a literal reading of it
safe to skip the render check.** Confirmed a second time on the same
project (FFVI SNES field/overworld sprites, `ceres`): the loader's own DMA
code (`TfrObjGfxSub`) writes 4 of a frame's 6 tiles to one VRAM
destination address and 2 to another, and reading that grouping literally
predicts one tile-to-cell arrangement — but rendering it produced visibly
scrambled output (a torso-coloured patch floating above disconnected
legs), while a plain top-to-bottom, left-to-right raster order of the same
6 tiles (an arrangement the DMA grouping does *not* literally match)
rendered an immediately recognisable standing character on the first try,
and generalised cleanly across 15 different characters with zero further
correction. The DMA code wasn't wrong or fake — its address-level VRAM
write pattern almost certainly reflects a hardware tile-numbering
convention (OAM 16x16 sprite tile-index arithmetic) that a flat pixel
decode doesn't need to model to reproduce the final image; but *reading
that grouping as "this is the display order"* was the wrong inference.
The lesson generalises past the "no documentation" case this file
originally described: even a **found, real, load-bearing reader** can
mislead about physical tile arrangement if its address pattern encodes a
hardware addressing convention rather than a display-order convention —
the render comparison is what actually adjudicates, every time, not the
mere existence or absence of a plausible-looking reader.

**Third confirmed instance, same routine, a different downstream
question.** The same `TfrObjGfxSub` DMA-destination grouping misled a
*second*, independent decision in a later `ceres` session: which raster
tiles belong to which of two h-flip attribute tables (`TopSpriteHFlip`/
`BtmSpriteHFlip`) governing mirrored left/right-facing sprite frames. A
literal reading again grouped tiles `[0,1,4,5]` (skipping the middle
raster row) as one flip-controlled unit and `[2,3]` as the other — the
*exact same* wrong grouping the frame-composition case above already
rejected. Rather than re-running a render-and-eyeball comparison (some
candidate frames have identical top/bottom flip values, so a render
can't distinguish the hypotheses there), this session settled it with a
**geometric argument** instead: a real SNES 16x16 OAM sprite is always
built from two *spatially adjacent* tile rows, and the confirmed §13.1
raster layout places the DMA-literal grouping's two "top" rows one full
tile-row apart on screen (y=0 and y=16, skipping y=8) — a physically
impossible shape for one 16x16 hardware sprite. That alone rules the
DMA-literal grouping out, independent of any render. The correct split
(rows 0-1 = "top" 16x16 entity, row 2 = "bottom" 16x8 entity) was then
confirmed byte-exact: applying it made a right-facing render exactly
equal (0/1536 RGBA byte mismatches, 15/15 objects) to a naive whole-image
mirror of the left-facing render — see
`verification-techniques.md`'s whole-image-mirror-invariant entry.
**Once one routine's address-level grouping is shown to encode hardware/
VRAM addressing rather than display semantics, treat it as unreliable for
*every* downstream question it touches, not just the one that first
caught it** — check geometric/physical plausibility (can this literal
grouping even correspond to real contiguous hardware sprite geometry?)
before trusting it again for a different purpose.
