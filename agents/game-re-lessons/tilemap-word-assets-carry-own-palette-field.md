# Tilemap-word-based asset banks carry their own per-cell palette selector — census it before hunting an external palette

**When it bites:** an asset bank (animation frames, screens, composed art)
whose frame data is **BG tilemap words** (SNES `vhopppcc cccccccc`, or any
platform whose nametable entries embed a palette/attribute field) renders
correctly in greyscale, and the next planned step is locating "its"
palette by tracing CGRAM/CRAM upload code, censusing palette-DMA call
sites, or guessing among boot/screen palettes.

Stop first: the format may already answer the question. Tilemap words name
their own sub-palette per cell, so if those fields are *live* (authored,
not residue), no dedicated palette upload need exist at all — the asset
simply composites against whatever palette rows are already resident when
it's drawn. Two cheap corpus tests distinguish live fields from dead bits:

1. **Variation** — histogram the palette field across every cell in the
   bank. Deliberate multi-value use (Wizardry 6 SNES spell animations:
   7 distinct sub-palettes across 77,056 cells) means authored data; a
   constant value suggests the field is dead and recolouring happens at
   upload.
2. **A designed hole** — check whether the one sub-palette slot that is
   *unstable* at draw time (e.g. a row the engine swaps per-region/
   per-level) is conspicuously absent. W6's spell-anim cells used
   sub-palettes 0,1,3-7 and **never 2** — exactly the row the dungeon
   region-palette swap overwrites. Artists avoiding precisely the
   unstable slot is strong evidence the fields are live and the colour
   source is the resident CGRAM state (there, the boot-time CGRAM shadow
   initialiser in ROM).

Then confirm with one colour composite using each cell's own field — a
coherent render (W6: a gold-and-blue magic casting circle) closes the
question. The prior approach (whole-ROM `STA $ca` palette-dispatch census
plus an escalation's boot-palette guess) had burned parts of two sessions
on a palette upload that doesn't exist.
