# crawl — dungeon crawlers: Black Crypt, EOB1-3, LoL, Dungeon Hack, M&M 1-3, Wizardry 6, SSI Gold Box, Ishar/Crystals, AGOS, Bard's Tale, Dungeon Master

**Project root:** `~/Development/crawl` · **Full history/evidence:** `game-re-corpora/details/crawl.md` (read on demand) · **Open work:** `docs/<game>/TODO.md` per game

## Games
- Black Crypt (Amiga; DOS demo) — formats solved; DOS full-game restoration Phases 1B-4 open
- Might & Magic I (DOS EGA) — maze/gfx/tables solved; `.OVR` handlers run under an overlay executor (event census, text pointers only)
- Might & Magic II/III (Amiga+DOS) — see `docs/mm2/`, `docs/mm3/` (MM2 ported from Vairn/MM2 format docs)
- Wizardry 6 (Amiga/DOS EGA/SNES) — merged from old `sorcery` repo; see `docs/wizardry6/`; corpus summary is `game-re-corpora/sorcery.md`
- EOB1/EOB2/Lands of Lore (DOS VGA; EOB1+EOB2 Amiga) — formats confirmed; mostly pipeline wiring left
- Eye of the Beholder III (DOS) — AESOP/16; 265 or 279/312 bitmaps coloured (sources disagree)
- Dungeon Hack (DOS) — AESOP/16, source-verified; per-sprite palette choice open
- Gold Box (Amiga): Pool of Radiance, Curse, Secret, Pools of Darkness, Champions/Death Knights/Dark Queen of Krynn, Gateway/Treasures of the Savage Frontier — containers, GEO, ECL solved; walkers built
- Ishar 1-3 + Crystals of Arborea (Amiga AGA) — ALIS location scripts render first-person for 13 locations across all 4 titles
- Elvira 1/2 + Waxworks (Amiga, AGOS) — 9,308 images (old 5,745 stopped at the first 0×0 entry); `*tune` = ProTracker; `gameamiga` = game database
- Bard's Tale I-III (Amiga) — pictures rendered; walls/maps/audio open
- Dungeon Master / DM2 / Chaos Strikes Back (Amiga) — container/dungeon/IMG1-4 solved; palette + IMG7/8 open

- **Game rules** (Black Crypt musashi; Wizardry 6, MM1 8086, MM2, MM3 Unicorn 68k): single-routine harness with strict read/write-footprint parity + null controls, > 1M vectors (small subsets committed, full sets gitignored); entry point = each `docs/<game>/<platform>/game-rules.md` status block. Remake layer: host + per-title engine contract (`docs/remake-architecture.md`, concept only, no GPL code)

## Solved formats → where documented
- Black Crypt Amiga RLE/planar/EHB, LZ77 via 68k emulation (`tools/bcdft_decompress/`), in-exe chunk directories (3-word records) — `docs/blackcrypt/amiga/data-structure.md`
- BC Amiga `bcdfs` → DOS `maindung.gam` converter, byte-exact (`scripts/bclib/maindung.py`, `scripts/verify_maindung.py`) — `docs/blackcrypt/dos/full-game-restoration-plan.md`
- MM1 `MAZEDATA.DTA` (= MM2 `map.dat` layout), `WALLPIX`/`MONPIX` `.DTA` 2bpp column-major RLE, `ROSTER`/`SCREEN0-9`/`MM.RSM`, ITEMS/MONSTERS in MM.EXE (byte-exact vs ScummVM), `.OVR` = native 8086 code + data (container confirmed) — `docs/mm1/dosega/data-structure.md`; walker `docs/walker-mm.md`
- Westwood Kyra family (PAK, LCW/Format80, CPS, VCN, VMP, MAZ/CMZ, INF, ITEM.DAT 14B/ITEMTYPE 16B, SHP, LoL VCN embedded palette) — `scripts/kyralib/`; `docs/eotb/{dosvga,amiga}/`, `docs/eotb2/{dosvga,amiga}/`, `docs/landsoflore/dosvga/data-structure.md`
- AESOP/16 `EYE.RES`/`HACK.RES` container, GFF, VFX shapes, 5-window DAC palettes, fonts — `docs/eotb3/dosvga/data-structure.md`, `docs/dungeonhack/dosvga/data-structure.md`
- Gold Box: PoR `.dax` (backward LZ77, not ByteKiller); GLIB container + stored/LZW/LZ77 nested tile banks; DOS DaxFile (LE, PackBits) and BE Amiga `.DAA`; 156-byte WALLDEF slices; GEO grid; ECL VM v1.1/v1.3/Treasure tables — `docs/goldbox-glib-format.md`, per-title `docs/<game>/amiga/data-structure.md`
- ALIS container/sprites; first-person view = live location bytecode — `docs/ishar-container-format.md`, `docs/ishar-sprite-format.md`, `docs/ishar*/amigaaga/`, `docs/crystalsofarborea/amiga/`
- AGOS `simon_decr` `.pkd` LZ77 + VC10 pictures, palette `nibble*32` — `docs/agos-pkd-format.md`
- Bard's Tale Huffman/RLE (BT1/2), LZHUF + XOR delta (BT3) — `docs/bardstale-picture-format.md`
- DM DMCSB2/DMII container, IMG1/2 and IMG3/4, dungeon grid + `0x8104` compression, P41A module packer — `docs/dungeonmaster-format.md`

## Engine-family / cross-project links
- EOB3 and Dungeon Hack share AESOP/16 (`scripts/eotb3lib/res.py` unchanged). Oracles: ThirdEye (`psi29a/thirdeye`) plus the original AESOP source and DAESOP (vogons t=20601; grep raw thread HTML, displayed links 404)
- EOB1/EOB2/LoL: ScummVM `engines/kyra/` is a byte-exact oracle (check `/tmp/scummvm` clone first)
- MM1: ScummVM `engines/mm/mm1` + Vairn/MM2 Python tools; MM1 map codec shares `decodeMapCell` with MM2
- Gold Box oracles: `simeonpilgrim/goldboxexplorer` (`DaxFile.cs`), `simeonpilgrim/coab` decompiled DOS source, wiki `pooldata.py`
- AGOS: ScummVM `extract_agos.cpp`/`res_ami.cpp`. Bard's Tale: Kroah's viewer. DM: dmweb docs + "DM II Data Files Notes"; libxmp ProWizard `p40.c`

## Reusable code in this repo
- `tools/shared/goldbox-{glib,glib-codecs,dosdax,daa-tiles,walltiles,geo,ecl,glib-export}.ts` — whole Gold Box stack
- `tools/shared/alis-{disasm,interp}.ts`, `ishar-*.ts`, `silmarils-unpack.ts` — Silmarils ALIS
- `tools/shared/agos-vga.ts`, `bardstale-codecs.ts`, `dungeonmaster-*.ts`, `amiga-player4x.ts`, `ilbm.ts`, `amiga-planar.ts`
- `scripts/kyralib/`, `scripts/eotb3lib/`, `scripts/dungeonhacklib/`, `scripts/mm1lib/`, `scripts/m68k_emu.py`
- `tools/walker/` — shared Dungeon Walker (`GameView`; `games-mm.ts`, `games-goldbox.ts`)

## Know before you start
- Same extension ≠ same format: PoR `.dax` vs Krynn DOS-DaxFile `.DAX` vs GLIB `.GLB/.TLB`; EOB1 vs EOB2 `.EGA`; EOB2-Amiga `TEXT*.CPS` are text; DM2 `IMGx` and `.MOD` (P41A). See `familiar-extension-not-proof-of-standard-format.md`, `sequel-shares-codec-family-name-not-byte-grammar.md`
- Per-port byte order is not uniform (EOB2 Amiga `.VMP` is LE while EOB1 Amiga's is BE) — `port-wide-byte-order-convention-not-uniform-across-formats.md`
- Black Crypt Amiga overlays with "no known loader": check in-exe chunk directories first
- Gold Box ECL: use the CFG reachability walker, not linear scans. A uniform degenerate result such as `{127,127,127}` means the decode config is wrong. Treasures' wallsets come from an exe-hardcoded table, and its overlays need `HUNK_OVERLAY` scanning
- ALIS: find each script's own `cswitch` value set, then scan the grid. Never reuse another script's test position
- ALIS: `cstop` is a per-frame yield, not an end — CFG walks continue past it. `acc OP[opile]` is `popped OP acc`. Stored grids are the world transposed — see `docs/ishar-container-format.md`
- MM page-0 wall codes are 2=door, 3=torch; overland code 3 is border. MM1/MM2 map bits are W,S,E,N (bits 0-1 W … 6-7 N), `0x20` = cell dark
- Walker can-step, start pose and map-edge rules must come from each game's move routine — `walker-movement-rule-must-port-games-move-routine.md`
- Rules harnesses: method in `cpu-emulation-boot-harness.md` (single-routine section); Unicorn needs `ctl_flush_tb()` after setup; never commit retail text or protection content in generated tables/vectors/commit messages

## Key lessons
- `familiar-extension-not-proof-of-standard-format.md`, `sequel-shares-codec-family-name-not-byte-grammar.md`, `port-wide-byte-order-convention-not-uniform-across-formats.md` — see Know before you start
- `false-positive-bytecode-hit-without-cfg-reachability.md`, `uniform-degenerate-hit-value-signals-wrong-decode-config.md` — Gold Box ECL
- `script-operands-overridden-by-exe-hardcoded-table.md` — Treasures wallsets come from an exe-hardcoded table
- `amiga-overlay-segment-defeats-resident-only-trace.md` — Gold Box Amiga exes need `HUNK_OVERLAY` scanning
- `hypothesis-tested-with-mismatched-input-looks-refuted.md` — ALIS: never reuse another script's test position
- `cross-platform-decode-oracles.md` — ScummVM/AESOP/Gold Box sources are byte-exact oracles here

Full list: `details/crawl.md` § "Lessons sourced from this corpus (full list)".
