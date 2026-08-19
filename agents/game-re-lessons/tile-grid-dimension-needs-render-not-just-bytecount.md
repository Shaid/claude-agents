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
`buffer-offset-arithmetic-confirms-partial-image-placement.md` covers a
cheaper code-level shortcut when the loader computes a blit-target offset
before the read — check for that before rendering every candidate by hand.

**A third failure mode beyond "clean render" vs. "pure noise": a wrong
*width* on a flat raw picture (not a tile grid) renders as the same
content visibly repeated in near-identical bands** — recognisable, not
noise, but wrong. Confirmed on Phantasie II's `CROWD.PIC` (11,160 bytes,
several candidate `(width,height,bitplanes)` factorizations, no header
field): decoding at a plausible-looking but wrong width (240 instead of
the correct 320) produced clearly recognisable "crowd of people" content
repeated in 4 near-duplicate horizontal bands — an unrelated width (e.g.
144, 160) instead produces the expected structureless noise. The
repeated-bands look tempts a "the source art really does tile" reading;
don't take that at face value — byte-diff the raw file at the wrong
candidate's row stride (e.g. compare `file[r*stride:(r+1)*stride]` against
`file[(r+n)*stride:(r+n+1)*stride]` for the apparent repeat period `n`)
before concluding the repetition is real content. Zero exact byte matches
across every row pair at that stride means the "bands" are a rendering
artifact of decoding at the wrong stride, not duplicated data — the
correct width (found here by re-deriving from the file's own bitplane
count via `size / bitplaneCount / (width/8)`, testing every integer
`bitplaneCount` divisor rather than assuming it matches sibling files)
produces one clean, non-repeating image instead.

**A second, independent case confirms the "cheap auto-score is not a
substitute for a human look" finding above generalizes beyond tile
adjacency.** Confirmed on Valkyrie Profile 2: Silmeria (PS2,
`~/Development/valkyrie`): once a real raw 8-bit raster image format was
found (character portraits, UI menu screens — see `game-re-corpora/
valkyrie.md`), one real payload size (31 instances on the disc) rendered as
pure noise at every width tried and needed excluding from the pipeline's
output. Two different automated per-image quality scores were tried to
separate "clean real render" from "noise" without a hand-maintained
exclusion list: a row-to-row pixel continuity score (mean abs difference
between adjacent rows) and a byte histogram (zero-byte fraction,
most-common-byte fraction). **Both failed in the same direction as the
tile-adjacency case**: real UI screens with sharp icon art and
content-dependent background darkness scored *worse* (noisier) on both
metrics than the confirmed-garbage samples — the metrics conflated "has
high local contrast" with "is noise," and legitimate game art spans too
wide a range on both axes for a universal threshold. With only ~5-6
known-good vs. 1 known-bad real sample to calibrate against, a
hand-written, commented exclusion of the one specific bad value was more
honest and more correct than a heuristic threshold tuned against too small
a labeled set. General takeaway: don't reach for a generic statistical
image-quality heuristic to auto-gate a small, mixed real/noise sample set —
either render-and-eyeball every candidate (small corpora) or accept a
manually-curated exclusion list with its reasoning documented, rather than
shipping an unreliable auto-filter that *looks* more scalable than a
hardcoded list but silently drops or keeps the wrong ones.
