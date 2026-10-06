# nicodemus — Phantasie I/II/III (SSI)

**Project root:** `~/Development/nicodemus` · **Full history/evidence:** `game-re-corpora/details/nicodemus.md` (read on demand) · **Open work:** `docs/phantasie/TODO.md` (one docs dir covers all three games)

## Games
- Phantasie I (Amiga) — `phantasie`/`amiga` — graphics, data tables, dungeons, world map, combat formulas confirmed
- Phantasie II (Atari ST; no Amiga port exists) — `phantasieii`/`atarist` — byte-verified from `.stx`; `.PIC`, world map, combat confirmed
- Phantasie III (Amiga) — `phantasieiii`/`amiga` — overworld, PLN plane maps, music, `.cmp` palettes, combat confirmed
- All three have tested end-to-end pipelines (`tools/phantasie*/`, `supported: true`); dungeon/scripting not yet wired into the runtime engine (`implementation-plan.md` Phase 3).

## Solved formats → where documented
Bare doc names below are in `docs/phantasie/`.
- Dungeon `DNG*`/`MESS*` (P1/P2 33×38 grid; P3 24×30 with embedded messages + opcodes 0x14-0x1B) — confirmed — `docs/phantasie/dungeon-format.md`, `scripting-engine.md`
- Exe tables (monster/race/item/spell names, sprite tables, palettes; P3 races, spells, skill-name strings; skill→record-offset binding is hypothesis) — confirmed — `docs/phantasie/data-tables.md`, `src/assets/formats/exe-data.ts`
- Combat RNG + to-hit/damage formulas, all three games; `GetStat`/`SetStat` statIndex→offset table — confirmed (field English names open) — `scripting-engine.md` §6-§7
- P1/P2 world map `maps.int` + `out*.dat` (one `OutdoorLayout`, only record size/display-list offset differ) — confirmed — `dungeon-format.md` §8, `src/assets/formats/outdoor.ts`
- P3 overworld `Graphics/phantasy.set` (50×75), `LocateSpecial()` hardcoded coords, `D/PLN1/2/4` plane maps — confirmed — `dungeon-format.md` §9.0, `graphics-formats.md` §5, `src/assets/formats/{pln,p3-planes,p3-overworld}.ts`
- P3 `D/M0`/`M1` music (VBlank driver, ProTracker period table) — confirmed — `dungeon-format.md` §9.0.2, `src/assets/formats/music.ts`
- P3 `.cmp` palettes (only `heros.cmp` palette installed for all sprite banks; ramp `34n`, not ST `36.43n`) — confirmed — `graphics-formats.md` §2/§4.5
- P2 `.pat` sprites + `.PIC` screens (ST word-interleaved by 2; palettes from `START.PRG`/`PHANT.PRG`) — confirmed — `graphics-formats.md` §9/§10
- P2 `.stx` (Pasti) extraction, save-vs-template verdicts — `docs/phantasie/stx-extraction.md`

## Engine-family / cross-project links
- P1 and P2 share one dungeon/scripting engine (boolean-flag selected) and combat formula — but **not** the RNG (P1 LCG `*3677+3`; P2 7-word circular-sum buffer). P3 is a distinct engine (LCG `*25173+13849`).
- A third-party fan tool (Windows dungeon/scripting viewer, full C# source) was the primary oracle — fetch to scratch only, never commit or reproduce verbatim. Kroah's sprite-viewer PNGs are a pixel oracle for P3 sprites.
- Scanned 1987 SSI P3 manual in `data/phantasieiii/` — strongest oracle (no text layer).

## Reusable code in this repo
- `src/assets/formats/outdoor.ts` — parameterized P1/P2 world-map decoder
- `www/src/components/DataTable.astro` — generic browsable-table component for any seer `www/` site
- `tools/viewer/map-viewer.ts` — map viewer generalized for mosaic and single-grid maps

## Know before you start
- P2's `PHANT.PRG` offsets from the reference source apply verbatim; P3 Amiga offsets do **not** (different binary) — see `romhacking-community-tools-first.md` "same compiled binary" rule.
- Hunk tracing: P3 file offset = address + `0x28`; ST `.PRG` file offset = 28 + address (Capstone); IRA `-preproc` misclassified P1 hunk 99 as data — see `game-re-tooling/amiga.md`, `game-re-tooling/atari-st.md`.
- `out*.dat` files are live save state rewritten on section exit; `maps.int`/`MAPS.INT` is the pristine master.
- Padding filler byte = `contentLength mod 128` (58/58 files) — gives true read lengths.
- `www/` pages drift from raw docs; update both when a finding changes.

## Key lessons
- `romhacking-community-tools-first.md` — P2 offsets transfer verbatim; P3 Amiga is a different binary
- `hunk-data-shorter-than-declared-is-merged-bss.md` — P3 hunk tracing: DATA hunk shorter than declared
- `save-file-not-asset.md` — `out*.dat` is live save state; `maps.int` is the master
- `padded-file-tail-describes-padding-not-content.md` — filler byte = `contentLength mod 128`; tails describe padding
- `curated-site-page-drifts-from-corrected-raw-docs.md` — `www/` pages drift from raw docs — update both
- `embedded-palette-not-the-installed-palette.md` — P3: only `heros.cmp` palette is installed for all banks
- `reference-tool-incompleteness-mistaken-for-game-ambiguity.md` — fan C# viewer is the main oracle; its gaps aren't the game's
- `scanned-manual-paraphrase-needs-reverify-and-diff.md` — P3 manual has no text layer — diff, don't paraphrase
- `tile-grid-dimension-needs-render-not-just-bytecount.md` — map/plane grids: byte counts admit several dimensions
- `negative-from-addressing-root-not-shapes.md` — zero-hit "no consumer" claims need addressing-root search

Full list: `details/nicodemus.md` § "Lessons sourced from this corpus (full list)".
