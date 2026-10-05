# A single gfx ROM region can be decoded at multiple, disjoint tile granularities for different layers

**When it bites:** a tilemap/sprite word format's per-layer tile-code field
is confirmed (from source or disassembly), one layer's gfx atlas is already
built and shipped at one tile size, and a *different* layer's real tile-code
values (found via disassembly or live data) don't fall in that atlas's
addressable range — or a pixel-render attempt for that other layer looks
wrong/out-of-range despite the word format itself being correct.

Many arcade/console video drivers declare more than one decode of the
*identical* raw gfx ROM region at different tile widths, one per hardware
layer that needs it — not because the ROM data differs, but because a
smaller "font"/text layer addresses the same bytes at a finer granularity
than a sprite layer does. MAME's own `GFXDECODE_START` macro makes this
explicit: CPS1's `gfx_cps1` declares **four** `GFXDECODE_ENTRY` lines all
pointing at the same `"gfx"` region — `cps1_layout8x8`/`cps1_layout8x8_2`
(scroll1, the text/background layer), `cps1_layout16x16` (sprites/scroll2),
`cps1_layout32x32` (scroll3) — each with a different `charincrement` (bytes
consumed per tile-index step: 64 bytes for the 8x8 layouts vs. 128 bytes for
16x16). Because charincrement differs, tile-index numbering is **disjoint
across layers**: tile code N under the 8x8 decode is a completely different
physical byte range than tile code N under the 16x16 decode.

Confirmed on Knights of the Round (CPS1): a real, disassembly-confirmed
scroll1 text-render routine writes tile codes like `0x8800+char` into
scroll1 tilemap RAM (the word *format* — code/attr, confirmed from
`get_tile0_info()` — was correctly decoded). But the project's already-
shipped 32,768-tile pixel atlas was built via only the 16x16
`cps1_layout16x16` gfx_layout (used for sprites/scroll2). Those `0x88xx`
codes are simply unaddressable there — under the 8x8 layout's 64-byte
charincrement they land in a completely different, ~65,536-tile-per-gfxset
address space carved from the identical ROM bytes. This is not a decode bug
in the shipped atlas; it's a missing *second* decode pass for the other
layer's declared tile size.

**Fix:** before assuming one already-shipped tile atlas covers every
tilemap/sprite layer's content, check the driver source's own gfx-decode
declaration (`GFXDECODE_START`/`GFXDECODE_ENTRY` or the equivalent for a
non-MAME engine) for how many distinct layout entries reference the same
raw region, and at what tile size/charincrement each. Treat "this layer's
tile codes don't fit the atlas I already built" as evidence of a missing
decode pass for that layer's own declared granularity, not evidence the
word-format decode is wrong.
