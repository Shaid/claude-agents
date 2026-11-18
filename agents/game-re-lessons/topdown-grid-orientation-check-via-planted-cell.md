# Check a top-down grid's orientation against the first-person renderer by planting one cell; derive facings by executing the dispatch

**When it bites:** a decoded world grid is drawn "rows down, columns across" and paired with a first-person renderer driven by the game's own scripts/code, with axis names (`x`/`y`) and a facing table hand-derived — possibly inside a transposed or mirrored frame where they stay self-consistent but wrong.

A storage layout says nothing about which axis is east. A transposed read plus swapped global names reads the right cells and still produces a world whose top-down view is the mirror of the 3D view; per-block hand traces of facing arithmetic "verify" inside that same frame.

**Check / fix:**
0. **Read the axes off the code's bounds before naming them.** For each coordinate variable, find its clamp or wrap (`cmp #rows-1`, `max - v - 1`, a modulo): the one bounded by the row count is Y, the one bounded by the stride is X, whatever the global is called. Check the indexing call's argument order against the VM/reference source (`base + accumulator + stride*popped` means accumulator = column). For a width/height header pair, score both orders **per level** with shared-wall reciprocity (`game-re-method/verification-techniques.md`), not as an average.
1. **Execute the facing dispatch** for every raw facing value with an instrumented grid reader that records each cell read. Each live value must scan a wedge straight ahead whose mean lateral offset is exactly 0; the wedge direction gives the facing table directly, and a dead value reads nothing. Commit this as a regression test.
2. **Plant a single non-zero cell** two cells to the display-left of the wedge and see which screen side its sprite lands on (first confirm from source that the projection itself does not flip x). Left-on-right for every facing = the naive drawing is a reflection.
3. Choose transpose vs. rotation/flip with an independent picture of the world — the game's own map screen or manual map.

**Canonical example:** crawl, Ishar 1/2/3 (ALIS). Every facing of all 9 location scripts put the display-left cell on screen right → the stored `row*stride+col` grid is the world transposed; Ishar 1's in-game map and Ishar 2's island map matched the transpose, not its flip. Executing the dispatch gave Ishar 3 a corrected facing table and turned a 0-placement test position into 44–51 placements per facing.

**Variants:**
- Ishar 1 `FORET.bin`: `0x137c` is clamped by `54-v-1` (row count) and `0x137d` by `90-v-1` (stride), the opposite of the globals' names.
- Gold Box Dark Queen variable GEO: an "82.4% average" plane check hid 8/20 transposed levels; per level, swapping width/height took them from 0.09–0.51 to 0.92–1.0.

**History:** 2 instances (crawl/Ishar, crawl/Gold Box Dark Queen), 2026-11-13.
