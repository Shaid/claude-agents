# Sibling games in one engine family sharing an asset *format* doesn't mean they share the *container* — or the gameplay math

**When it bites:** a task brief or prior doc says two games are "the same
engine, same file family" (shared G1T/G1M/WTB/etc. asset formats already
solved for one of them) and asks you to check whether a specific *archive/
container* format (LINKDATA, PAK, WAD, ...) is "probably the same, just
unverified" — before you've grepped the second game's actual file tree for
that container's filename/magic. The same caution generalizes one level up,
to *gameplay-math* formulas (damage, hit/crit resolution, any RNG driving
combat): a shared engine and genre predicts nothing about whether two
titles compute combat the same way — verify each title's own disassembly
independently before assuming a sibling's formula transfers.

Chimera (Koei Tecmo Musou engine): the brief assumed Fire Emblem Warriors
(2017) uses the same `LINKDATA_*.BIN` archive layout as Fire Emblem Warriors:
Three Hopes (2022), hedged only as "not yet verified." A recursive filename
search (`find <romfs> -iname '*linkdata*'`) across the entire 2017 base
romfs returned **zero matches** — there is no LINKDATA archive in that
game's data at all. The two games do share the G1T texture format and (by
internal chunk-tag evidence) the G1M model format, and both decode with the
same `g1t.ts`. But the 2017 game stores those G1T-bearing assets as
individual per-character "pack" files scattered directly through the
directory tree, not inside any top-level indexed archive — a completely
different container architecture, not a header variant.

The generalizable point: "same engine family" is real and valuable evidence
for shared *content* formats (texture/model/animation codecs), which is
exactly why cross-referencing sibling projects/games is worth doing first
(see the Prior-art corpora table). It is much weaker evidence for shared
*archive/container* formats, because studios routinely change their asset
*packaging* pipeline between titles/years even when the underlying content
codecs carry over unchanged (they're usually different tools/teams: content
exporters vs. build/packaging scripts). Treat "does the container exist at
all in this game's data" as a five-second, zero-cost check
(`find`/`grep -r` for the expected filename or magic) to run **before**
writing a byte-level comparison plan for "confirm the header matches" — a
plan that's moot if the container isn't present to begin with. If the
premise fails this fast, it usually only strengthens the case for the
content-level formats being shared (which don't depend on any particular
container), so the two aren't wasted work in different directions — you
still know where to point the shared decoder, just via a different content-
discovery route (a magic-byte scan for the content format directly,
bypassing the container).

**Second confirmed instance, gameplay math, same engine family**: Fire
Emblem Warriors (2017) and Three Hopes (2022) share the Koei Tecmo Musou
engine and both have real-time combat, but their damage formulas turned out
to be structurally different — FE Warriors is a classic subtraction
(`max(0, ATK-DEF)`, capped at 999) with a real gameplay LCG RNG wired in (a
2RN-averaged "True Hit" idiom for hit rate, a 1RN roll tripling damage on
crit); Three Hopes is a ratio/divide (`ComputeDamage`) with **no** RNG
anywhere in its damage path (the LCG multiplier constant `0x41C64E6D` is
completely absent from its binary, even split across `movz`/`movk` halves).
Both were independently re-derived from each title's own disassembly rather
than assumed from the other — the right call, since assuming transfer either
direction would have been wrong. See `docs/fe-warriors.md` § "Real-time
combat-resolution math — SOLVED" and `docs/few-threehopes.md`'s sibling
section (chimera project).

**Third confirmed instance, rendering *mechanism*, same developer**:
Millennium 2.2 (Novagen Software, Amiga, `methanoid` project) was
investigated for a Mercenary-style stored-vertex 3D/2D wireframe vector
engine, since Mercenary (the developer's other well-known Amiga title) is
built on exactly that. It doesn't transfer: a whole-file byte-exact scan
for every graphics.library line/polygon-drawing LVO (`Move`, `Draw`,
`AreaMove`, `AreaDraw`, `AreaEnd`, `PolyDraw`, `RectFill`, `InitArea`,
`DrawEllipse`, `AreaEllipse`, `BltPattern`, `ScrollRaster` — offsets derived
from the FD file's `##bias`/stride convention, the same method already used
for `LoadRGB4` elsewhere in that project) found **zero hits** for all of
them, and a raw-longword scan for BLTCON0 (`$DFF040`, the blitter's direct
line-draw-mode register) also found zero hits. This whole-primitive-family
LVO census is a cheap (minutes, not hours), decisive way to settle "does
this game draw vector lines/polygons at all" *before* assuming a sibling
title's well-known rendering architecture carries over — it generalizes the
container/gameplay-math caution above to rendering mechanism claims too.
The real answer here was a different but genuine positive: a runtime
polar-coordinate (sine/cosine lookup table) point-plotter, and a
disassembly-confirmed object-record table (position+size+colour+visibility)
feeding a custom, non-LVO box-fill renderer — real 2D geometric data, just
not a 3D wireframe engine. See `docs/millenium22/amiga/data-structure.md` §
"Vector/geometry investigation".
