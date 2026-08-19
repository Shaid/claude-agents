# crawl — Black Crypt, Eye of the Beholder 1-3, Lands of Lore

**Project root:** `~/Development/crawl`

Amiga RLE + planar sprites, EHB palettes, per-level sprite stores, LZ77-via-emulation (`tools/bcdft_decompress/`), Westwood CPS/VCN/MAZ/INF. Black Crypt's in-executable **chunk directories** (3-word size/compressed/slot records, zero-terminated) proved to be the load mechanism for every multi-payload overlay in the game — worth checking first whenever an Amiga overlay has "no known loader". Sourced `narrow-opcode-form-census-false-negative.md`, `unbounded-appended-data-boundary.md`, `fixed-stride-record-count-unverified.md`, `generic-bucket-hides-real-content.md`. See `docs/blackcrypt/amiga/data-structure.md`

**Black Crypt DOS/Windows demo (`data/blackcrypt/dosvga/`)** — a 1995
Rick Johnson/Activision port containing 1 of 13 dungeon maps plus a
full-game-sized `crypt.exe`. A restoration feasibility investigation
(`docs/blackcrypt/dos/full-game-restoration-plan.md`) found the demo's
map-switch code was only a 12-byte stub removed from an otherwise-intact,
fully parameterized subsystem (Phase 1A, closed via `re-codebreaker`), and
built a byte-exact Amiga `bcdfs` → DOS `maindung.gam` converter (Phase 2,
`scripts/bclib/maindung.py` + `scripts/verify_maindung.py`, verified
15,099/15,099 B zero deviation, full 13-map output 171,005 B). The
20-byte item/monster/structure record's byte-swap turned out
itemType-*independent* — a single global positional composition, not a
per-itemType lookup table as first framed — found by testing "one rule
consistent with every observed type" instead of building a per-type table;
see `hypothesis-space-flip-before-per-value-table.md`. `crypt.exe` also
turned out to embed Amiga `bcdft`'s item-name string block verbatim
byte-for-byte, needing no reference remap — see
`cross-platform-decode-oracles.md`'s addendum. Remaining open in that
plan: 1B/1C/1D (gfxNumber resolver, Wine viability, art scoping) and
Phases 3-4 (resource injection, code patch) — see
`docs/blackcrypt/TODO.md`.

## Might & Magic I (DOS/EGA, `data/mm1/dosega/`, GOG)

**MM1 maze geometry is SOLVED** (2026-08-13 pass): `MAZEDATA.DTA` = 55 ×
512-byte screens, **byte-identical layout to MM2 `map.dat`** (two 256-byte
pages: page 0 four 2-bit N/E/S/W wall codes `0` open/`1` wall/`2` torch/`3`
door, page 1 `(dark<<1)|wall` per direction + `0x80` event flag) — the MM1
codec (`tools/mm1/map.ts`) literally shares `decodeMapCell` with the MM2 one.
Screen names from MM.EXE's null-terminated slug table at **file offset
`0x10C07`** (55 slugs); each slug names a companion `*.OVR` map-script
overlay (55 files in the GOG dir — set-equality is the independent
cross-check). Verified three ways: TS round-trip byte-exact vs disk, TS
decode byte-exact vs Vairn/MM2's independent Python decoder (`mm1_maps.py`,
byte-identical page output), and slug table byte-exact vs MM.EXE. Ground
truth: **Vairn/MM2's dedicated MM1 section** (docs 50-52/22-24 +
`tools/mm1_*.py` + an interactive 3D maze walker) and ScummVM
`engines/mm/mm1`. Caveat: overland sectors (14-33) still use MapWalls
page-0 encoding; code `3` there means border/edge, not door. See
`docs/mm1/dosega/data-structure.md`.

**MM1 graphics are SOLVED** (2026-08-14 pass): `WALLPIX.DTA` (17 wall sets ×
12 frustum slices — 4 left + 4 right + 4 front, fixed sizes 16-176 px wide)
and `MONPIX.DTA` (75 monster portraits, 104×96) share one container + codec:
`.DTA` = `u16LE` index size + `u32LE` offset table (+sentinel) + payloads,
each entry prefixed by its own `u16LE` size word; the image format is an RLE
stream (`0x7B` run marker) filling a `w/4 × h` grid of 2bpp cells
**column-major** (`col + row*stride`, NOT a cycling `idx += stride` — porting
it the naive way consumes the stream exactly with 0 remainder yet renders
single-colour garbage), expanded MSB-first through a per-entry 4-index remap
(WALLPIX `TILE_COLORS[entry]` nibbles; MONPIX `PALETTE[imgNum]` u16 nibbles)
into the standard 16-colour EGA palette. Ported from ScummVM
`engines/mm/mm1` (`gfx/dta.cpp` + `screen_decoder.cpp` + `maps/maps.cpp`
`loadTile` + `data/monsters.cpp` `getMonsterImage`); monster names from
ScummVM's static `monsters.txt` (195 monsters, last field = `_imgNum`; ~69
distinct images shared; all aquatic monsters use imgNum 75 which has NO
MONPIX entry — they get no portrait). Verified: 92/92 entries 0-remainder
decode, size words 92/92, symmetric-vs-horizon L/R patterns, biome-coherent
colours. `scripts/mm1lib/` + `scripts/extract_mm1_gfx.py`. Still open:
`ROSTER.DTA`/`GACARD.DTA`/`SCREEN0-9`/`MM.RSM`, items/monsters/spells
tables, `*.OVR` event bytecode (ScummVM `maps/map00-55.cpp` are its
hand-translated scripts).

**MM1 misc data is SOLVED/documented** (2026-08-14 pass): `ROSTER.DTA` =
18 × 127-byte character records + 18 town bytes (2304 B exact; layout from
ScummVM `data/roster.cpp` + `character.cpp`; decoded record 0 = "CRAG THE
HACK", the canonical starter party — roster file doubles as a verification
oracle: names/classes/HP/gold match the known MM1 party). `SCREEN0-9` = 10
title screens (u16LE size word + the same 2bpp RLE ScreenDecoder at 320×200,
_indexes (0,2,4,15), screen 2 uses (0,3,5,15)). `MM.RSM` = the game's
**overlay-loader symbol table** — 22 named internal routines (`readmaze_`,
`readrost_`, `readwall_`, `readmon_`, `readscr_`, `ovloader_`, `Bpcomand`…)
each followed by a 4-byte address field (seg-byte, 0x28, u16LE offset);
address encoding open. `GACARD.DTA` = 1 byte copy-protection card state.
`scripts/extract_mm1_misc.py`. Still open: items/monsters/spells tables,
`*.OVR` event bytecode (ScummVM `maps/map00-55.cpp` are its hand-translated
scripts; MM.RSM is the head start), live-capture oracle.

**MM1 data tables are SOLVED** (2026-08-14 pass): items and monsters are
embedded in **MM.EXE**, not .dat files. ITEMS at file offset `0x19B2A`, 255
× 24-byte records (14-char name + disablements, constBonus id/value,
tempBonus id/value-or-spellId, maxCharges, cost `u16` **big-endian** —
the one BE field in an otherwise-LE table, reads as ×256 under LE —
damage, AC_Dmg; categories 1-60 weapon/61-85 missile/86-120 two-handed/
121-155 armor/156-170 shield/171-255 special). MONSTERS at `0x1B312`, 195 ×
32-byte records with a **15-byte** name field (15th byte = last letter for
15-char names, else pad — a 14-byte assumption shifts every stat) + count,
fleeThreshold, HP, AC, damage, attacks, speed, experience `u16LE`, loot,
resistUndead, resistances, bonusOnTouch, specialAbility, specialThreshold,
counterFlags, imgNum (→ MONPIX portrait). Both verified **byte-exact
255/255 and 195/195** against ScummVM's static transcriptions
(`devtools/create_mm/files/mm1/items.txt`/`monsters.txt`). SPELLS have **no
binary table** — spells are code + combat-effect strings in the exe string
pool (~0x12580-0x12780); SP cost = spell level (formula); the canonical 47
cleric + 47 wizard + 32 monster spell lists are transcribed from ScummVM
(`scripts/mm1lib/mm1_spells.json`). `scripts/extract_mm1_tables.py`. See
docs/mm1/dosega/data-structure.md § Items/Monsters/Spells.

**`.OVR` overlays are SOLVED at the container level** (2026-08-14 pass):
the 55 per-screen "map scripts" are **compiled 8086 code + a data segment**,
not a bytecode. Container verified 55/55 (`14 + code_sz + data_sz == file
size`): 14-byte header (constant entry offset 242, far-data constants
0xF48F/0xC940, code_sz, data_sz, per-file load-segment candidate); code
bound to the game's fixed memory map (MOV AX,0xC940 at entry; references
0xC973/0x3C3A...). Data segment: map id/code byte, WALLPIX area table byte,
3×u16 wall/lane ids (towns→entries 0-2, caves→3-5, overland→6-13; AREAA1 =
6/13/12 = wall07/wall14/wall13, byte-for-byte Vairn doc 24), 4×3-byte event
triples (open), then **387 map text strings** (the real game dialogues).
`scripts/mm1lib/ovr.py` + `scripts/extract_mm1_ovr.py`. Open: code-segment
script semantics (memory-map-bound disassembly; MM.RSM is the loader
oracle) — see `script-files-may-be-native-code-bound-to-fixed-memory-map.md`.

**MM1+MM2 walkers are integrated into the shared Dungeon Walker** (2026-08-14,
`tools/walker/index.html` game dropdown — alongside Black Crypt + Wizardry
6; the old `tools/walker-mm/` page redirects there): `GameView` gained
optional `renderCanvas`/`renderMinimap` hooks (full-colour frustum
renderers bypass the DrawItem composite path), `tools/walker/games-mm.ts`
holds `MM1View`/`MM2View`, and the harness gained per-game asset platforms
+ partial URL params. MM1 renders the **real WALLPIX slices** (per-screen
set from the decoded .OVR selection fields; overland uses its biome art;
**no torch overlay** — the game renders code-3 faces as plain walls, the
reference implementation has no torch art). MM2 renders the authentic
`.32` sheets indoors (town/cave/castle + floor + sky + 3-phase torch
flicker, roof-bit sky switch, cross-screen stepping via attrib
neighbours) and the **outdoor scene on overland** (`tools/walker-mm/
outdoor3d.ts` port: outdoor1-3 horizon lanes + desert/ocean/swamp/tundra
biome decor from terrain ids, `outb.32` terrain minimap, surface byte
0xCC/0x99/0xBB from attrib). Also fixed: the MM renderers now clear the
whole 320x200 harness canvas (stale previous-game pixels below the
208x120 viewport looked like "Black Crypt's floor"), and the page-0
wall-code semantics were corrected to **2=door, 3=torch** (ASM traces +
collision-page statistics; earlier prose had them swapped). See
`docs/walker-mm.md`.

Might & Magic II (Amiga+DOS) and MM3 (Amiga+DOS) integrations also live in
this repo (`docs/mm2/`, `docs/mm3/`) — not yet summarized here.

## eotb3 (Eye of the Beholder III, DOS/Windows, `data/eotb3/dosvga/`)

**Different engine from EOB1/EOB2 — not Kyra, no ScummVM support.** EOB3
runs on **AESOP/16** (John Miles' bytecode VM — the file magic literally
reads `"AESOP/16 V1.00"`, not "AESOP/32" as an earlier internet-research
pass assumed; same engine family as SSI's *Dungeon Hack*). Ground-truth
oracle: **ThirdEye** (`github.com/psi29a/thirdeye`, GPL C++, clone it and
read `apps/thirdeye/resources/*.cpp` + `graphics/*.cpp` directly — see
`romhacking-community-tools-first.md`'s "no test suite" section). Solved,
byte-exact-verified formats (see `docs/eotb3/dosvga/data-structure.md`):

- **`EYE.RES`** — the AESOP/16 resource container (all game assets/bytecode
  in one 6.8 MB file, name-dictionary-indexed). A from-scratch Python parser
  reproduced ThirdEye's independently-derived counts exactly (2449 entries,
  20 directory blocks, 2444 named resources) — strong container-format
  confirmation.
- **CPS** (Westwood LCW/Format80, same family as Dune II/Kyra-era titles) —
  still used for `CHARGEN/*.CPS` backdrops despite EOB3's otherwise
  different engine.
- **GFF/"GFFI"** (Miles Design cutscene container: `INTRO/DARK/FINALE/
  LICH.GFF`) with 3 bitmap sub-encodings: an "old format" row/span scanline
  RLE (cutscene BMP/BMA frames — BMA holds ALL frames in one directory, no
  frame-chaining), an AESOP/16 "1.10" VFX shape table (every `EYE.RES`
  bitmap — 312 resources / 3528 shapes decoded with zero errors), and a
  `CHARGEN/CHARPICS.BMP` portrait directory (90 portraits, byte-exact count
  match to ThirdEye).
- `ITEM.DAT` (434 items, 14-byte EOB1-identical records) / `ITEMTYPE.DAT`
  (64 types, 16-byte records) — found and corrected a 2-byte systematic
  offset error in ThirdEye's *own* `docs/item_dat_format.md` by
  cross-checking its cited AD&D 2e values against real bytes.
- **`EYE.RES` bitmap↔palette resolution** — not a static per-resource field
  but 5 fixed windows into the 256-colour VGA DAC
  (`PAL_FIXED`/`PAL_WALLS`/`PAL_M1`/`PAL_M2`/`PAL_OUT`), loaded at runtime
  by bytecode; found by grepping ThirdEye's *runtime* module
  (`apps/thirdeye/runtime/graphics.cpp`'s `kFirstColor[5]` array) rather
  than tracing AESOP bytecode. A bitmap's own stored pixel-value range
  reveals its window with zero bytecode tracing; 265/312 (85%) VFX shape
  resources now resolve to real, visually-confirmed colour (a Wight,
  a lion/dragon/goat Chimera, a marble stairwell — all immediately
  recognizable). See `romhacking-community-tools-first.md`'s runtime-module
  addendum.
- `EYE.RES` non-bitmap resource classification (2449 entries, no on-disk
  type tag — AESOP resolves meaning purely by which VM function consumes a
  resource): 749 UI/menu/copy-protection strings (`"S:<text>\0"`
  convention), 116 raw 8-bit unsigned PCM sound effects (8000 Hz mono,
  confirmed against ThirdEye's `sound.cpp`), 14 dungeon-level 32×32
  wall-type maps (byte-exact match to ThirdEye's own level count).

Sourced `nested-header-same-named-size-field.md` and two additions to
`romhacking-community-tools-first.md`: the ThirdEye "no test suite, still
re-verify" case, and its "read the runtime module, not just the format
parser" + "an oracle can support the format without exercising every file"
addenda (also sourced from EOB3/ThirdEye — its cutscene sequencer only
hand-codes `INTRO.GFF`'s playback, nothing for `DARK`/`LICH`/`FINALE.GFF`).
Still open: the remaining 47/312 `EYE.RES` bitmaps (the "outtake" family's
wider DAC placement, a few `PAL_WALLS`-region bitmaps that reuse a
dungeon-theme palette without a matching name), `DARK.GFF`/`LICH.GFF`
colour accuracy (no embedded palette and no oracle — ThirdEye doesn't
sequence these files at all), `SAVEGAME/` extractor (format documented +
spot-verified, not extracted — it's save state, not shipped assets). See
`docs/eotb3/TODO.md`.

## dungeonhack (Dungeon Hack, DreamForge Intertainment/SSI, 1993, DOS/Windows, `data/dungeonhack/dosvga/`)

**Same AESOP/16 engine as EOB3** (`HACK.RES`/`OPEN.RES` share `EYE.RES`'s
exact magic and container layout — `eotb3lib/res.py` works unmodified).
This pass had a much stronger oracle than EOB3's ThirdEye reimplementation:
the actual AESOP interpreter source and an independent decompiler tool,
both publicly released by the original author/community and linked from
`https://www.vogons.org/viewtopic.php?t=20601` (see
`romhacking-community-tools-first.md`'s two new addenda for how these were
found/used — the forum's *displayed* download links 404; the real path
needs grepping the raw thread HTML). Confirmed, source-verified this pass:

- Container format (`RTRES.H`'s `RF_file_hdr`/`RF_entry_hdr`/`OD_block`
  structs match byte-for-byte) and a `.TBL` sidecar pair (a flat directory-
  index cache DAESOP's own docs confirm "the Dungeon Hack engine needs").
- "Old format" row/span-RLE bitmaps (EOB3 §4.1) used **directly** in the
  main container (not GFF-wrapped like EOB3) for full-screen art and
  wall/decoration LOD sprite sets — found and fixed a latent
  u16-vs-u32 field-width bug in the shared decoder this exposed (see
  `format-field-width-unexercised-by-first-corpus.md`), and found a
  classifier false-positive this format-usage difference caused against a
  heuristic that was clean on EOB3 (see
  `classifier-clean-corpus-not-proof-for-sibling-game.md`).
- Palette resources' previously-"unexplained" trailing bytes are real
  per-colour brightness/fade tables (`DEFS.H`'s `PAL_HDR` struct confirms
  it exactly) — retroactively also explains EOB3's own palette resources'
  trailing bytes, see `palette-storage-quirks.md`'s new addendum.
- A new proportional-width font resource format (left open by the EOB3
  pass under the same resource names) — cracked from scratch, then
  independently corroborated field-for-field against DAESOP's own
  `convert.c`/`.h` source.
- The same 5-window runtime DAC-region colour mechanism as EOB3, confirmed
  directly from source (`GRAPHICS.C`'s `first_color[5]`/`num_colors[5]`/
  `fade_tables`) rather than inferred from a reimplementation — as a bonus
  this also explains EOB3's own still-open "outtake" 80-colour palette
  mystery (a 5th DAC region, same base as the wall window but spanning the
  full wall+monster range).
- `MAZE.EXE` identified via `strings` alone as "Random Dungeon Generator
  v1.0/386" by Event Horizon Software Inc — a separate procedural-dungeon-
  generator process `HACK.BAT` launches mid-game, not part of AESOP.EXE.

Extractors: `scripts/extract_dungeonhack_res.py`,
`scripts/dungeonhacklib/`. See `docs/dungeonhack/dosvga/data-structure.md`
for full evidence, `docs/dungeonhack/TODO.md` for what's still open
(mostly: which of several same-shaped candidate palettes applies to a
given wall/decoration sprite — needs a bytecode trace, out of scope so far).

## EOB1, EOB2, Lands of Lore — Westwood "Kyra" engine, DOS/VGA

**One shared library (`scripts/kyralib/`) covers all three** — ScummVM's
`engines/kyra/` source (fetched via `raw.githubusercontent.com/scummvm/
scummvm/master/...`, no clone needed for the specific files used) is a
byte-exact oracle for the whole family: PAK container (`ResLoaderPak`,
`resource/resource_intern.cpp`), the shared bitmap header + LCW/"Format80"
decompression (`Screen::loadBitmap`/`decodeFrame4`, `graphics/screen.cpp`),
and VGA palette decode (`Palette::loadVGAPalette` + the `(v<<2)|(v&3)`
6-to-8-bit expansion) are verbatim-identical across EOB1, EOB2, and Lands
of Lore. Only 2 small deltas needed per game: EOB2 has one file using
`compType 3` (simple RLE, `decodeFrame3`) that EOB1 doesn't; LOL wraps its
`.VMP` (viewport tile-index map) and level-grid file (`.CMZ`, but it's
byte-for-byte the same 32×32×4-wall-byte grid EOB calls `.MAZ`) in an
extra outer LCW layer that EOB's raw versions of those files don't have,
and introduces one genuinely new format, `.SHP` (multi-frame shape/sprite
container: `u16` count + `u32[count+1]` offset table + per-shape header
with an optional runtime colour-remap table — ported from
`Screen_v2::getPtrToShape` + `Screen::drawShape`'s scanline decoder).
Ground truth for all three: known title/logo screens (EOB1's, EOB2's
"Legend of Darkmoon", LOL's) render byte-exact-recognisable through the
full PAK→LCW→palette pipeline.

Sourced `oversized-flat-file-may-be-disc-image.md` (LOL's `GAME.DAT` is a
raw ISO 9660 image, not a data file — see there).

**Second pass (2026-08-02) closed nearly every item the first pass left
open, by reading `engines/kyra/` more deeply rather than re-deriving from
scratch** — cloned to `/tmp/scummvm` (check for this clone before
re-fetching). Confirmed and closed, all byte-exact or source-cited:
EOB1's `EYE.PAK` (engine explicitly skips it, `resource.cpp:153`, no
fallback loader anywhere — genuinely unused); EOB1/EOB2 `.INF` level-config
records (LCW-compressed like `.CPS`, not raw — full record walk including
a bytecode event-script region ported from `EoBInfProcessor`); EOB1/EOB2
`ITEM.DAT`/`ITEMTYPE.DAT` (14-byte/16-byte records, not the
previously-guessed 15 — see `record-stride-guess-vs-recount-fields.md`)
and EOB2 `TEXT.DAT` (offset-table + string-pool); `.EGA` render-mode files
(EOB1: same LCW bitmap container as `.CPS`, EGA-hardware-index palette;
EOB2: *not* graphics at all, 768-byte VGA-style alternate palettes — same
extension, two different formats per game, confirmed from
`screen_eob.cpp`'s `cpsExt[]` table); EOB2 `.DCR`/`.DEC` (9/9 and 6/6
files byte-exact, zero residue); EOB2's missing `AZURE.VCN` (confirmed by
exhaustively decoding all 16 levels' `.INF` wall-set-stem fields — Azure
genuinely never referenced, not a naming mismatch); the EOB1/EOB2 Amiga
port question (ScummVM has full first-class Amiga support — see
`romhacking-community-tools-first.md`'s detection-tables addendum) letting
Amiga VCN palette (5 colours, `(nibble*0x3F)/0xF` scaling, not the
previously-guessed 32-colour 8-bit-RGB), VCN "decompression" (there is
none — raw tile read), `.DEC` (same format as DOS), `.DCR` (EOB1 never
uses it — `hasDecorations` hardcoded false), and `EOBDATA.SAV` (full
record layout + a working platform-autodetection heuristic) all close
too. **LOL's turn resolved the big one**: the wall/monster
`RGB(255,0,255)` "runtime palette patch" mystery was a **misread offset,
not a missing patch** — LOL's `.VCN` embeds its own 384-byte/128-colour
palette after a per-tile shift table + 128-byte remap table, a
variable-length header the previously-shared EOB `.VCN` parser (fixed
34-byte header) silently misread for months — see
`platform-port-swaps-adjacent-header-fields.md`'s second case. Also
closed: LOL `.TLK` files are ordinary Kyra PAKs of `.VOC` speech clips,
not CD-audio blobs (see `plausible-filename-hypothesis-unchecked-against-source.md`);
LOL `.WLL` is the wall-type-parameter table (EOB's `<WALLSET>.DAT`
analogue), 12-byte records, confirmed byte-exact. See
`docs/eotb/dosvga/data-structure.md`, `docs/eotb/amiga/data-structure.md`,
`docs/eotb2/dosvga/data-structure.md`, `docs/landsoflore/dosvga/
data-structure.md` for full evidence; each game's `docs/<game>/TODO.md`
for what's still open (now mostly pipeline-wiring — format confirmed,
extractor not yet updated — rather than format-unknown).
