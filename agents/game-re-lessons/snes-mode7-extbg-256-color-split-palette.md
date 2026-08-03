# SNES Mode 7 "EXTBG" 256-colour overworld: pixel nibble + per-tile palette nibble, concatenated BG+sprite CGRAM halves

**When it bites:** decoding a SNES Mode 7 overworld/world-map layer (as
opposed to ordinary Mode 0-6 BG tiles) where the tile pixel data is
ordinary 4bpp (16 colours) but the visible in-game map clearly shows far
more than 16 distinct colours at once, or a palette lookup against just
one 128-colour CGRAM half produces garbled/wrong colour on an otherwise
structurally-clean tile decode.

Several SNES RPGs' Mode 7 world maps use a classic "EXTBG" trick to get
256 effective colours out of 4bpp (16-colour) tile graphics: each tile
still stores ordinary 4-bit pixel values, but a **separate per-tile
palette-select nibble** (not per-pixel, not per-meta-tile-quadrant like an
ordinary BG tilemap word's palette field) picks which of 16 "rows" of 16
colours that whole tile's pixels read from. The final 8-bit colour index
written to VRAM is `(paletteNibble << 4) | pixelValue` — confirmable
directly from the transfer routine that combines the two right before the
VRAM write, if source is available.

Because the resulting index is a full 8 bits (0-255), the palette it
indexes into must supply the **entire** 256-colour CGRAM — not just the
128-colour BG half that suffices for every other (non-Mode-7) tile format
in the same game. Two separately-labelled, otherwise-unrelated-looking
128-colour palette tables (one conventionally used for BG layers, one for
sprites) can be the **concatenation** that forms this full palette, with
nothing in the ROM's own data explicitly declaring that relationship.

Confirmed on FFVI (SNES, `ceres` project): `TfrWorldMapGfx`
(`src/world/tfr_gfx.asm`) explicitly computes `(nibble<<4)|pixelValue`
before writing to VRAM. Neither `World{1,2}BGPal` nor `World{1,2}SpritePal`
alone (256 bytes/128 colours each) is large enough to cover the full
8-bit range; concatenating them (BG half = colours 0-127, Sprite half =
colours 128-255) produced an unmistakable, correctly (non-garbled)
coloured render of both World of Balance and World of Ruin, closing the
question. This wasn't documented anywhere in that project's community
reference material — it had to be inferred from the index bit-width and
confirmed purely by render correctness.

**Fix:** for any SNES Mode 7 overworld layer, check whether the pixel
format is plain 4bpp *and* the visible map has clearly more than 16
colours on screen — if so, look for a routine that combines the tile's
raw pixel nibble with a second, tile-level (not per-pixel) nibble from a
nearby table before the VRAM write, and if found, try the full-CGRAM
palette (both halves concatenated) rather than assuming just one half
applies as it would for the rest of the game's non-Mode-7 graphics.
