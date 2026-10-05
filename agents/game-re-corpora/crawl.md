# crawl — dungeon crawlers: Black Crypt, EOB1-3, LoL, Dungeon Hack, M&M 1-3, Wizardry 6, SSI Gold Box, Ishar/Crystals, AGOS, Bard's Tale, Dungeon Master

**Project root:** `~/Development/crawl` · **Full history/evidence:** `game-re-corpora/details/crawl.md` (read on demand) · **Open work:** `docs/<game>/TODO.md` per game

## Games
- Black Crypt (Amiga; DOS demo) — formats solved; DOS full-game restoration Phases 1B-4 open
- Might & Magic I (DOS EGA) — maze/gfx/tables/misc solved; `.OVR` code semantics open
- Might & Magic II/III (Amiga+DOS) — not summarized in details; see `docs/mm2/`, `docs/mm3/`
- Wizardry 6 (Amiga/DOS EGA/SNES) — merged from old `sorcery` repo; see `docs/wizardry6/`
- EOB1/EOB2/Lands of Lore (DOS VGA; EOB1+EOB2 Amiga) — formats confirmed; mostly pipeline wiring left
- Eye of the Beholder III (DOS) — AESOP/16; 265/312 bitmaps coloured, rest open
- Dungeon Hack (DOS) — AESOP/16, source-verified; per-sprite palette choice open
- Gold Box (Amiga): Pool of Radiance, Curse, Secret, Pools of Darkness, Champions/Death Knights/Dark Queen of Krynn, Gateway/Treasures of the Savage Frontier — containers, GEO, ECL, wall art solved; walkers built
- Ishar 1-3 + Crystals of Arborea (Amiga AGA) — ALIS scripts render 6 locations; Ishar 2/3 first-person not attempted
- Elvira 1/2 + Waxworks (Amiga, AGOS) — 5,745 pictures rendered; sound/text open
- Bard's Tale I-III (Amiga) — picture banks rendered; walls/maps/audio open
- Dungeon Master / DM2 / Chaos Strikes Back (Amiga) — container/IMG/dungeon solved; palette + IMG7/8 open

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
- AGOS: ScummVM `extract_agos.cpp`/`res_ami.cpp`. Bard's Tale: Kroah's viewer (its `Files/` are cmp-identical to the corpus). DM: dmweb docs + "DM II Data Files Notes"; libxmp ProWizard `p40.c`
- Black Crypt DOS `crypt.exe` embeds Amiga `bcdft` item-name block verbatim

## Reusable code in this repo
- `tools/shared/goldbox-{glib,glib-codecs,dosdax,daa-tiles,walltiles,geo,ecl,glib-export}.ts` — whole Gold Box stack
- `tools/shared/alis-{disasm,interp}.ts`, `ishar-*.ts`, `silmarils-unpack.ts` — Silmarils ALIS
- `tools/shared/agos-vga.ts`, `bardstale-codecs.ts`, `dungeonmaster-*.ts`, `amiga-player4x.ts` (P41A)
- `tools/shared/ilbm.ts` (generic IFF ILBM/PBM), `amiga-planar.ts`
- `scripts/kyralib/`, `scripts/eotb3lib/`, `scripts/dungeonhacklib/`, `scripts/mm1lib/`, `scripts/m68k_emu.py`
- `tools/walker/` — shared Dungeon Walker (`GameView`; `games-mm.ts`, `games-goldbox.ts`)

## Know before you start
- Same extension ≠ same format: PoR `.dax` vs Krynn DOS-DaxFile `.DAX` vs GLIB `.GLB/.TLB`; EOB1 vs EOB2 `.EGA`; EOB2-Amiga `TEXT*.CPS` are text; DM2 `IMGx` and `.MOD` (P41A). See `familiar-extension-not-proof-of-standard-format.md`, `sequel-shares-codec-family-name-not-byte-grammar.md`
- Per-port byte order is not uniform (EOB2 Amiga `.VMP` is LE while EOB1 Amiga's is BE) — `port-wide-byte-order-convention-not-uniform-across-formats.md`
- Black Crypt Amiga overlays with "no known loader": check in-exe chunk directories first
- Gold Box ECL: use the CFG reachability walker, not linear scans. A uniform degenerate result such as `{127,127,127}` means the decode config is wrong. Treasures' wallsets come from an exe-hardcoded table, and its overlays need `HUNK_OVERLAY` scanning
- ALIS: find each script's own `cswitch` value set, then scan the grid. Never reuse another script's test position
- MM page-0 wall codes are 2=door, 3=torch (earlier prose had them swapped). Overland code 3 is border

## Lessons sourced from this corpus
`narrow-opcode-form-census-false-negative.md`, `unbounded-appended-data-boundary.md`, `fixed-stride-record-count-unverified.md`, `generic-bucket-hides-real-content.md`, `hypothesis-space-flip-before-per-value-table.md`, `cross-platform-decode-oracles.md`, `script-files-may-be-native-code-bound-to-fixed-memory-map.md`, `romhacking-community-tools-first.md`, `nested-header-same-named-size-field.md`, `format-field-width-unexercised-by-first-corpus.md`, `classifier-clean-corpus-not-proof-for-sibling-game.md`, `palette-storage-quirks.md`, `oversized-flat-file-may-be-disc-image.md`, `record-stride-guess-vs-recount-fields.md`, `platform-port-swaps-adjacent-header-fields.md`, `plausible-filename-hypothesis-unchecked-against-source.md`, `endian-swap-needs-matching-field-width.md`, `port-wide-byte-order-convention-not-uniform-across-formats.md`, `familiar-extension-not-proof-of-standard-format.md`, `flags-field-correlation-false-lead-vs-declared-size-check.md`, `identical-nested-header-across-varying-allocations-is-inert-boilerplate.md`, `false-positive-bytecode-hit-without-cfg-reachability.md`, `uniform-degenerate-hit-value-signals-wrong-decode-config.md`, `individually-failed-fixes-may-combine-cleanly.md`, `tile-bank-index-zero-not-universally-a-placeholder.md`, `header-field-role-not-transitive-across-sibling-format.md`, `locally-indexed-substructures.md`, `lvo-byte-pattern-false-positive.md`, `script-operands-overridden-by-exe-hardcoded-table.md`, `amiga-overlay-segment-defeats-resident-only-trace.md`, `hypothesis-tested-with-mismatched-input-looks-refuted.md`, `undefined-nan-defeats-decrement-loop-termination.md`, `erasable-syntax-only-rejects-parameter-properties.md`, `sequel-shares-codec-family-name-not-byte-grammar.md`, `decompressor-port-loop-condition-iteration-shift.md`
