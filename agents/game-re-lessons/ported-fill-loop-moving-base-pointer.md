# Ported fill loop with a moving base pointer: consumption stays exact, content goes wrong

**When it bites:** Porting a C/C++ decoder loop that fills a buffer through a
pointer that advances on a different schedule than the index — e.g. a
column-major fill where `destP[index]` is written with a *moving* `destP`
(base pointer) and a *cycling* `index`. Porting it as "`idx += stride`, reset
`idx` to 0 on wrap" silently overwrites column 0 every wrap. The trap is that
the **byte-consumption count stays exact** (the loop structure is what drives
consumption, and it's unchanged), so "0 remainder" structural checks pass
while the content renders as single-colour/structured-but-wrong garbage.

**The tell:** a decode with perfect consumption invariants (0 remainder, size
words matching, all entries "decoding") whose output is suspiciously uniform
(all pixels one colour, or structure that ignores part of the data). When a
0-remainder decode produces degenerate content, re-audit the *write-address
arithmetic* of the ported loop, not the stream parsing — the C++ original
writes position `base + index` where `base` advances per column; the naive
port writes `index` alone.

**Confirmed on:** MM1 (DOS) `WALLPIX.DTA`/`MONPIX.DTA` (crawl project) —
ScummVM `screen_decoder.cpp` fills a `w/4 × h` 2bpp grid with
`destP[index] = v; index += w/4; if (index >= imgSize) { index = 0; ++destP; ++x; }`.
The first port wrote `grid[idx]` with `idx` reset to 0 per wrap; all 92
entries still consumed their payloads byte-exactly (0 remainder, which looked
like strong verification) but every WALLPIX slice and 68/75 MONPIX portraits
decoded to a single colour. Fix: track `(row, col)` explicitly and write
`grid[row*stride + col]`. After the fix the same consumption invariants held
AND all 75/75 MONPIX images + all 17 wall sets showed multi-colour,
biome-coherent content. See `scripts/mm1lib/dta.py` `decode_screen`.
