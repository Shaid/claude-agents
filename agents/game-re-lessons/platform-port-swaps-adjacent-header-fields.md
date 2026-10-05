# A "same container, different endianness" port can still swap adjacent same-size header fields — or add a whole sub-region a sibling format doesn't have

**When it bites:** you're reusing a confirmed decoder on a port or a sibling game (same engine or publisher) because the container shape matched, and the output has impossible values or a byte count that's off by a rough multiple. Also: a known standard struct (e.g. DSP-ADPCM) wrapped in a game's own container. Also: your field-order check is symmetric (`w×h`-shaped) and so can't detect a swap.

A matching container shape (directory layout, table sizes, multi-byte field offsets) doesn't prove that the field order inside a small header matches, or that the internal sub-region offsets match. Ports swap adjacent same-width fields. Sibling games add variable-length regions. Same-studio formats repack bits differently. Because both misread fields are real data, the result looks like a bit-depth, compression, or swizzle bug, not a field-order bug. Coarse checks such as "total payload length matches" or "the render looks like *some* texture" keep passing.

**Check / fix:**
- Test **both** orderings of any two same-size fields whose roles are only inferred, against a corpus-wide byte-accounting invariant (e.g. `rowStride(w)×h` vs. the actual decompressed length, every frame of every file). The right order closes exactly on almost every frame. The wrong one is off by a scaled, non-constant amount. One file can match by coincidence.
- **Check the check for symmetry.** If swapping the two values leaves the formula unchanged, it proves "right numbers", not "right slots". Restrict the test to instances where the values differ (w≠h), or derive the layout from content instead, e.g. the block-adjacency stride in `game-re-method/verification-techniques.md`.
- When porting a decoder to a sibling *game*, re-read that game's own loader line by line (e.g. `LoLEngine::loadLevelGraphics`). Same engine, same publisher, same console generation, and the same abstract algorithm are evidence of the same engineers, not of byte compatibility.
- Re-verify even "standard" external structs against real bytes. A mostly-working clamp or workaround that hides overruns is not evidence the field read is right.
- Re-check any mask or clamp tied to the source platform's hardware limit (e.g. `& 0x0f` for a 32-colour palette) on a target with wider limits.

**Canonical example:** Dune (Cryo), DOS VGA vs Amiga. Both use the 4-byte sprite header `[wflags u16][byte][byte]`, but Amiga orders the bytes `[paletteBase][height]` and DOS orders them `[height][paletteBase]`. Reading DOS in Amiga order gave "impossible pixel values for the bit depth" and lengths about 2× off, which stalled two earlier passes. Swapping the two byte reads took the corpus-wide frame-size match from ~0% to 98.3% (the remaining 1.7% was one unrelated file). The Amiga `& 0x0f` palette mask also had to be removed for DOS's 256 colours.

**Variants:**
- Lands of Lore vs Eye of the Beholder `.VCN` (Kyra engine, `crawl`): the EOB decoder assumes a fixed 32-byte remap and tiles at 0x22. LOL's header is variable: a `numTiles` shift table, a 128-byte remap, then a 384-byte embedded palette. The 0x22 offset decoded header bytes as tiles for a whole session, while the total-size invariant kept passing.
- FFV vs FFVI (SNES, `ceres`): in the LZSS header, FFVI stores the compressed length and FFV the decompressed length. Back-reference byte order is reversed, and the 3bpp flag sits in a different byte and endianness. Re-derive every field from each game's own disassembly.
- FE: Three Houses `.ktsl2asbin` (`chimera`): the 96-byte DSP-ADPCM block had `+0x00`/`+0x04` swapped (sample vs nibble count), hidden by a `floor(streamSize/8)*14` clamp. Byte accounting closed 0/14,847 deviations on the right order, and `@4 > @0` held in 100% of channels.
- Three Hopes G1T extra-dims (`chimera`): a "fix" swapped the width/height labels. Its `ceil(w/4)*ceil(h/4)` check was symmetric, and the transposed 512×288 textures were chased as a swizzle for a whole session. 1,298 of 1,678 (non-square) textures were affected.

**History:** 5 recorded instances (`wyrm`/Dune, `crawl`, `ceres`, `chimera` ×2). Full log in `_archive/platform-port-swaps-adjacent-header-fields.md`.
