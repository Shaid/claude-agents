# One bitplane, or any width × depth with the same row stride, renders as plausible art

**When it bites:** a planar resource is decoded as 1bpp (or a low depth) because the render is legible, or because a row-coherence metric peaked at that width. Or the decoded image shows N side-by-side panels or column groups that look like "variants".

One bitplane of a real multi-plane image is itself a clean, coherent 1-bit picture: an outline, a texture, legible letters. And W px × P planes, row-interleaved, has exactly the same row stride as (W·P) px × 1 plane. A row-autocorrelation or "no shear" test can't tell these apart, and the wider reading shows the P planes as P panels side by side. The byte count and BLTSIZE often can't settle depth either. So "it renders cleanly at 1bpp" is the expected result for a wrong decode as well as a right one.

**Check / fix:**
- List every (width, planes, plane order) combination with the observed row stride (W·P/8 bytes) and decode each. Don't stop at the first legible one.
- Score with something that depends on colour, not shape: the number of distinct indices used (a 1bpp reading caps at 2), a **seam/edge-continuity** score between adjacent tiles or sprite rows against a shuffled-position null, cross-title or cross-port glyph identity, or an index-coverage census (max index matches the palette size).
- The tell for a misread plane: "variants" in panels whose count equals a plausible plane count (5, 8), or an "icon" count that clusters near multiples of 7 (mask + 6 planes).
- If tiles carry their own header (height/width/flags), the "8-byte 1bpp tile" may be one plane of a header + P-plane glyph. Check whether `len == header + P × plane` holds for every block.

**Canonical example:** Gold Box (PoR, Curse, Secret, Pools, Amiga). Wall tiles were decoded as header-less 1bpp 8-byte tiles, with renders "confirmed" as crenellation, doors and herringbone. Each glyph is actually an 8-byte header plus 4-6 planes (Curse 1,325/1,325 blocks fit `48 = 8 + 5×8`; PoR 23/23 entries fit `12 + count×16×4`). Seam lift (observed − null)/(1 − null) was 0.48 for the corrected decode against 0.09 for the shipped 1bpp reading. 31/45 PoR universal glyphs matched Curse's at the same index, against 1/122 under the old reading. Every shipped wall texture in four titles was wrong.

**Variants:**
- Reunion (AGA) `STMAPn00.CHR`, "confirmed 1bpp 256 px dither atlases": they are 32 px × 8 planes, the same 32-byte row stride. At 32×8 they show 249 distinct indices and shaded planet sprites; the "8-per-row-group columns" were the 8 planes side by side. The OCS `GR*.CHR` "legible Move/Attack at 320 px × 1 plane" was one plane of a 64 px × 5-plane bank.
- Black Crypt `bcdfb`–`bcdfn` trailing data: "692 standalone 16×20 1bpp icons" were single planes of 7-plane (mask + 6bpp) decorations. The counts clustering near multiples of 7 was the missed tell.

Related: `bitplane-layout-variants.md` (arrangement), `header-shape-ambiguous-pixel-encoding.md` (byte count fixes depth, not arrangement), `narrow-width-masks-a-planar-layout-correction.md`; seam oracle in `game-re-method/verification-techniques.md` § Seam continuity.

**History:** 3 projects (Gold Box ×5 titles, Reunion, Black Crypt).
