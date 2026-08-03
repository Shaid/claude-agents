# Multiple (width, height, atlas) triples can all satisfy a tile-grid's byte-count invariant — only a clean render picks the right one

**When it bites:** a compressed/raw tile-index blob's decompressed length
has several plausible factor pairs (and, if paired with more than one
candidate tile atlas, several candidate atlas assignments too), none of
them ruled out by width lists from other games/platforms in the corpus,
and no per-resource dimension field exists in the header or payload.

A byte-count check (`cols * rows === decompressedLength`) is satisfied by
*every* factor pair simultaneously — it cannot be the deciding test by
itself, no matter how "natural" one factor pair looks (round numbers,
close-to-square, or matching another game's fixed convention). When several
candidate tile atlases also exist (one game area's tileset vs. another's),
the true `(cols, rows, atlasId)` triple must be found by rendering **every**
combination and looking for the one with **zero** artifacts — every wrong
guess produces a visible horizontal comb/shear pattern (rows drift out of
phase with the real per-row content) or renders as a fully scrambled
picture, while the correct one renders a recognisable, spatially coherent
scene with no seams.

Confirmed on Warriors of Legend's 5 distinct `PAMM` map regions (`res32/
map2.res`): none of the decompressed sizes (23052, 19320, 19092, 11988,
20910 bytes) matched any Amiga-typical width from the project's existing
`detectMapDimensions()` list, and each had 6-30+ factor-pair candidates.
Rendering every candidate against every one of the 5 candidate 256x256
tile atlases in the file surfaced exactly one clean, coherent result per
map (an overworld coastline, a castle interior, a city, a dungeon, a
farm/vineyard) — every other combination showed comb-striping or scrambled
noise. One region's atlas pairing even broke the "obvious" guess (`PAMM#N`
pairs with `GAMI#(500+N)`, which held for 3 of 5 regions) — the true pairing
for the 4th region was only found by rendering it against *every* candidate
atlas, not assuming ID adjacency.

**A cheap automated shortcut was tried and found unreliable across content
types — still worth trying as a triage aid, never as a substitute for the
full visual check.** A "vertical tile-adjacency coherence" score (fraction
of `grid[y][x] === grid[y+1][x]` pairs, expected to peak at the true height)
correctly favoured the true dimension for organic/terrain content (high
natural self-similarity) but ranked the true dimension for architectural
content (city/dungeon layouts, much less repetitive) far down the list —
confirming the wrong candidate would have shipped if the auto-score alone
had been trusted for those regions. Every top-ranked candidate from such a
heuristic still needs its render checked by eye before being trusted.

**Fix:** when a byte-count check alone can't disambiguate width/height (and
possibly atlas assignment too), render **all** structurally-valid
candidates — not just the numerically "nicest" one, not just the
top-ranked one from a cheap coherence heuristic — and pick the sole result
with no comb/shear artifacts. Related: `header-shape-ambiguous-pixel-encoding.md`
covers the same "byte-count alone is not sufficient" trap for pixel
encodings and decompressor choice; this is the tile-index-array analogue.
