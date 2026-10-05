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

**EOB2's own Amiga port solved (2026-09-02, previously untouched/
deferred):** confirmed a *non-uniform* hybrid, not the naive "EOB1-Amiga
encoding + EOB2-DOS mechanism" pattern predicted going in — `.VCN`/`.CPS`/
`ITEM.DAT`/`ITEMTYPE.DAT` are exactly that hybrid (EOB1-Amiga's own
big-endian/planar encoding, wrapped in EOB2's own LCW-compressed
container/header shape; `ITEM.DAT`/`ITEMTYPE.DAT` share DOS's exact record
layout and counts but every multi-byte field is big-endian, see
`endian-swap-needs-matching-field-width.md`), but `.VMP` instead matches
EOB2 *DOS*'s own little-endian `330+N*431` convention, directly
contradicting EOB1 Amiga's own documented big-endian `.VMP` — see
`port-wide-byte-order-convention-not-uniform-across-formats.md`, sourced
from here. Also found `TEXT.CPS`/`TEXT2.CPS`/`TEXT4.CPS` are not images at
all despite the shared `.CPS` bitmap extension — they LCW-decompress
**md5-identical** to EOB2 DOS's own real `TEXT.DAT` (see
`familiar-extension-not-proof-of-standard-format.md`'s newest instance),
and `.DEC`/`.DCR` are literally md5-byte-identical files to DOS's own
copies (forced-LE reads, matching the already-confirmed EOB1 convention).
All 16 levels export and render real first-person dungeon views (wall
geometry, wall decorations, and the LEVEL10-14 mezz+azure
palette-override bundle all confirmed), wired into the walker as a new
`eotb2amiga` GameId reusing the DOS renderer/loader code completely
unmodified. See `docs/eotb2/amiga/data-structure.md`.

## Pool of Radiance (SSI Gold Box engine, Amiga, `data/poolofradiance/amiga/`)

First of 4 sibling Gold Box titles staged in this repo. `.dax` container
**CONFIRMED** (2-byte BE `headerSize` + N×10-byte BE directory entries
`[u16 indexID][u32 dataOffset][u16 compressedLength][u16
decompressedLength]` + concatenated compressed blocks; 843/843 entries,
23/23 files, zero-deviation offset chaining and exact file-size closure).
Decompression codec **CONFIRMED**: a custom backward-reading (BE longwords
popped from the stream's end), checksum-verified LZ77 variant — **not** real
ByteKiller despite the source wiki's own "ByteKiller 2.0" label (checked
against `ancient`'s actual `ByteKillerDecompressor`: 0/843 pass its header/
checksum validation); ground truth was the same wiki's attached
`pooldata.py` script instead, a register-level 68000 transliteration. Wall
renderer (`walldef.dax` + `8x8d.dax`) **CONFIRMED** structurally: 156-byte
wall slices, 10 view sub-arrays each (geometry table ported from Gold Box
Explorer's DOS-side `DaxWallDefFile.cs` despite that tool's own container/
codec being unrelated — see `cross-platform-decode-oracles.md`), cross-
checked via 3 independent ID-arithmetic predictions against `8x8d.dax`'s own
directory. **This answers the corpus-wide "is Gold Box's first-person view a
static picture library?" hypothesis in `docs/walker-map-format-future-
decision.md`: REFUTED** — it's a true per-depth composited tile render like
every other game in this repo, just at finer 8×8-tile granularity; 105
rendered wall-view PNGs are real visual evidence (a door/torch feature
reused identically across two wallset ids; a distinct plain masonry texture
elsewhere). `pic.dax`/`cpic.dax` (the alternative "static picture" candidate)
are a clean **negative finding**: 0/59, 0/118 entries pass even Gold Box
Explorer's coarse EGA/VGA picture-block dimension checks — real content
format still open. `dungcom.dax` decompresses cleanly but is semantically
undecoded. See `docs/poolofradiance/amiga/data-structure.md` and
`docs/poolofradiance/TODO.md`.

### Sibling titles (Curse of the Azure Bonds, Secret of the Silver Blades, Pools of Darkness) — a genuinely different, uncompressed container ("GLIB")

Opened from raw, un-renamed floppy dumps in a later pass
(`data/curseoftheazurebonds/amiga/`, `data/secretofthesilverblades/amiga/`,
`data/poolsofdarkness/amiga/`). Same engine family and near-identical
filenames-with-different-extensions (`.TLB`/`.GLB` vs. PoR's `.dax`) turned
out to mean a **different container, not a renamed one**: magic `"GLIB"` +
u32 BE `totalSize` + u16 BE `blockCount` + u16 BE `flags` + a 4-byte ASCII
content-type tag + a cumulative u32 BE absolute-offset block table — no
compression at all (a block's length is implicit from consecutive offsets,
unlike `.dax`'s explicit per-entry compressed/decompressed length fields).
Confirmed corpus-wide: 65/72 real `.GLB`/`.TLB` files across the three
titles chain with zero deviation; the other 7 are floppy-dump truncation
(confirmed via cross-title decode of the same base filename in a different,
healthy disk image — see `docs/goldbox-glib-format.md` §3 and
`flags-field-correlation-false-lead-vs-declared-size-check.md` for a false
lead ruled out along the way). Shared implementation:
`tools/shared/goldbox-glib.ts` (container), `tools/shared/
goldbox-walltiles.ts` (tile bank + wall-slice re-exports).

**PoR's `walldef.dax` geometry transfers byte-for-byte unchanged inside the
new container** — the 156-byte wall-slice / 10-view-sub-array layout and the
`10*wallId+n` multi-wallset composite-id convention both reused/reproduced
with zero modification across all three titles (Curse, Secret independently
re-derive the composite arithmetic from their own tile-bank index tables).
Pools of Darkness (1991, the latest of the four) shows a real format
**simplification**: it packs a wall's whole wallset set into ONE outer
directory entry with a plain 1:1 index, no composite ids needed — same
underlying 156-byte geometry, simpler addressing. Expect this same GLIB
container + 156-byte geometry (and possibly the later-title simplification)
in any further Gold Box title added to this corpus (Krynn/Buck Rogers
spinoffs).

**The "per-wall-id nested tile bank" sub-format is SOLVED** (2026-08-30,
`re-codebreaker`, then independently re-verified and integrated same
session): the byte-identical boilerplate nested-container header per entry
(three different game-specific constants across the three titles) was not
inert boilerplate — the nested payload is **compressed**, and the header
describes the container *after* decompression. Compression method is the
high byte of the container's `flags` word (`0`=stored, `3`=10-bit LZW,
`5`=byte-oriented LZ77 — both codecs traced in the games' own 68000
loaders, `tools/shared/goldbox-glib-codecs.ts`). Verified independently (not
just trusted from the escalation): 329 nested `"TILE"` sub-containers
corpus-wide, 0 decode errors, every one a well-formed GLIB body; a
byte-exact cross-title oracle (Secret's compressed id-202 bank matches
Curse's stored copy, differing only in the expected compression-method
header byte). This overturns
`identical-nested-header-across-varying-allocations-is-inert-boilerplate.md`
— see that file for the corrected lesson.

Now wired into all three extractors and rendered end to end: 90/90 (Curse),
95/95 (Secret), 90/90 (Pools of Darkness) `WALLDEF.GLB` entries produce
real, non-degenerate wall-view PNGs via this semantically-correct pairing
(`walldef2-*.png`, alongside the earlier cross-disk "flat" scheme's
`walldef-*.png`). Integration surfaced one further subtlety: a composite
`10*id+n` id covers a fixed run of **5** raw wall slices (one wallset), not
one slice each; trying the WALLDEF id directly first (before falling back to
composite arithmetic) is what lets one code path cover Curse/Secret's
composite scheme and Pools' own direct-only simplification without
title-specific branching. See `docs/goldbox-glib-format.md` §5/§5.7 and each
title's own `docs/<game>/amiga/data-structure.md` / `TODO.md`.

> **Correction (2026-08-31, `re-oracle` escalation):** the tile-bank index
> unit question above is now CLOSED, not open — a decompiled DOS *Curse of
> the Azure Bonds* source (`simeonpilgrim/coab`) confirmed a WALLDEF tile
> byte indexes one whole 48/56-byte glyph BLOCK, not a single 8x8 tile. The
> same escalation also solved GEO's maze-connectivity grid (see below).

### GEO dungeon/city grid + ECL wallset-slot binding (2026-08-31 / 2026-09-01)

All four titles' `geo.dax`/`GEO.GLB` (16x16-square, 4-plane-per-level maze
grid) is **CONFIRMED** for wall/door connectivity — plane 3 is a 2-bit
wall/door/other code per direction, plane 3's own value labels needed a
correction (0=solid/blocked, not 0=open) found by the same `re-oracle`
escalation above. Planes 0/1 are a level-scoped wall-art TYPE (0-15)
indexing one of 3 runtime wallset slots, not raw texture ids directly. A
real interactive first-person walker (`tools/walker/games-goldbox.ts`,
shared `GameView`) is built on the confirmed grid for all four titles.

**Resolving which real WALLDEF id occupies each of a level's 3 wallset
slots needs that level's own ECL bytecode script** (`LoadWalldef(slot,id)`
at area-setup time) — decoded end to end (container + a 65-opcode VM,
`tools/shared/goldbox-ecl.ts`) and verified via a worklist-based CFG
reachability walk (0 unknown opcodes, 0 desyncs among the visited set).
Resolves per-level for Curse (10/16 levels, 30 slots) and Secret (5/17
levels, 15 slots), but genuinely 0/29 and 0/32 for Pool of Radiance and
Pools of Darkness respectively — for two *different*, independently
disassembly-confirmed reasons (PoR: 3 of 5 header entry-point fields point
outside the level's own ECL block; Pools: every reached call uses a
memory-dereferenced/dynamic operand, not a literal) rather than one shared
explanation, despite both being the same 0/N symptom. A naive linear
byte-scan (not following real GOTO/GOSUB control flow) produced a
false-positive "reachable" hit here that the reachability walker correctly
refuted — see `false-positive-bytecode-hit-without-cfg-reachability.md`.
Full writeup: `docs/goldbox-glib-format.md` §7/§7.4.

### Champions of Krynn + Death Knights of Krynn (Amiga) — a SECOND, genuinely different container family sharing the `.dax`/`.DAX` extension

Staged at `data/ssi/ChampionsOfKrynn/data/` and
`data/ssi/DeathKnightsOfKrynn/data/` (WHDLoad-packaged Amiga installs).
Despite sharing the `.dax`/`.DAX` extension and PoR's own base filenames
(`GEO`, `ECL`, `WALLDEF`, `ITEM`, `MON*`), these two titles' `.DAX` files use
**neither** PoR's own bespoke Amiga codec **nor** the GLIB titles' container
— a third, "DOS DaxFile" format matching CodePlex/GitHub
`simeonpilgrim/goldboxexplorer`'s DOS-side `Common/Plugins/Dax/DaxFile.cs`
exactly: 9-byte **little-endian** directory entries `{id: u8, offset: i32,
rawSize: u16, compressedSize: u16}` (note field order — `rawSize`
*before* `compressedSize`, opposite PoR's own order) + a PackBits-style
byte-oriented RLE codec (signed lead byte: `>=0` copies `n+1` literal
bytes, `<0` repeats one byte `-n` times) — a much simpler, forward-reading
scheme than PoR's backward bit-level LZ77. Found by exhaustively
brute-forcing every plausible directory layout against PoR's own scheme
first (zero matches — the brute force had actually tried a structurally
close shape but always with PoR's field order), then locating the exact
DOS-side reference implementation externally. New shared module:
`tools/shared/goldbox-dosdax.ts`. Independently corroborated by a same-
session `amiga-disasm` subagent's disassembly (real `"WALLDEF"`/`"GEO"`/
`"Unable to load geo in Load3DMap."` strings in the game executable —
`Load3DMap` is the exact DOS-source function name the GLIB doc's own
`re-oracle` escalation already identified).

Downstream formats transfer **unchanged**: GEO (1026-byte entries = 2-byte
prefix + confirmed 1024-byte 4-plane record — Champions' prefix is PoR's own
constant `0x0004`; Death Knights' varies per level but doesn't affect
decoding, confirmed via the wall-adjacency self-consistency oracle,
98.8-100% agreement), ECL (constant `0x8813` 2-byte tag, both titles), and
WALLDEF (exact multiples of 156 bytes). Both titles' **ECL engine revision
is confirmed v1.1** — base `0x8000`, the standard `OPCODE_TABLE`, wallset
load via opcode `0x37` "LOAD PIECES" (the module's own default) — the SAME
revision as Pool of Radiance/Curse/Secret, **not** Pools of Darkness's v1.3
table. Champions of Krynn resolves 15/15 levels; Death Knights resolves
16/19. Getting to that answer for Death Knights needed a real correction:
an unknown-opcode-ratio sweep initially favored the v1.3 table + a
`fill-all-from-second-operand` wallset-load convention (100% resolution,
better aggregate ratio) — but every single level resolved to the identical
degenerate `{127,127,127}`, which turned out to be a scanner desync right
after the wallset-load instruction, confirmed by manually disassembling the
same raw bytes under both configs. See
`uniform-degenerate-hit-value-signals-wrong-decode-config.md` for the
generalized lesson this produced.

Death Knights ships only ONE `walldef1.dax` for its 3 campaign banks (unlike
Champions' 2 separate `WALLDEF1/2.DAX`) — explained structurally, not just
assumed: every entry decompresses to exactly 156*15 bytes (3 bundled
5-slice wallset groups, one per bank), reusing Curse/Secret's own
multi-wallset composite-id arithmetic.

**8x8 tile pixel format**: CONFIRMED for Champions' `8X8D1.DAX` (a DOS-
DaxFile container itself; headerless GLIB-style 8-byte/tile convention,
visually confirmed — a real composited wall view with crenellation border +
door/torch feature). Champions' and Death Knights' separate `*.DAA`/`*.daa`
files (`8X8D0/1/2.DAA`, `8x8d1.daa`, plus most other Amiga-native resources
in both titles — `BIGPIC*.DAA`, `SPRIT*.DAA`, `WILDCOM.daa`, etc.) turned out
to share a THIRD container in this corpus: a BIG-ENDIAN sibling of the "DOS
DaxFile" format above — same 9-byte entry shape and PackBits codec, but all
fields BE and `dataOffset = headerLen` **exactly** (not `+2`) — cracked via
a `re-oracle` escalation after 5 refuted hypotheses (the fix needed BOTH the
endianness AND the offset convention flipped at once; see
`individually-failed-fixes-may-combine-cleanly.md`'s second instance).
`readAmigaDaaDirectory`/`decodeAmigaDaaFile` in `tools/shared/goldbox-
dosdax.ts`. **Death Knights' `8x8d1.daa` payload is now fully SOLVED and
shipped**: 9-byte header + 64-byte embedded palette (all-zero per wall
entry; the real colours live in a "universal" id) + plane-consecutive
bitplane data (`tools/shared/goldbox-daa-tiles.ts`). Its per-wall tile
addressing is a "quarters" scheme not seen elsewhere in this corpus — the
raw WALLDEF byte's own high 2 bits select among 4 sibling `.DAA` entries
(`W`, `W+20`, `W+40`, `W+60`), with **no reserved placeholder at index 0**
(unlike every GLIB-family tile bank in this corpus) — see
`tile-bank-index-zero-not-universally-a-placeholder.md`. 105 real wall-art
PNGs ship (85/105 non-degenerate; the rest are genuine blank filler data
for wall/bank combinations a given campaign never uses, confirmed by
reading the raw all-zero WALLDEF bytes directly, not a decode bug).
Champions' own `8X8D0/1/2.DAA` container is solved the same way (byte-exact,
id 201 a genuine all-zero stub), and its INNER pixel payload — which does
NOT match Death Knights' shape (header offset-2 `tileCount` field reads a
uniform, implausible `1`) — is now ALSO solved (2026-09-02): the real tile
count is a byte at offset 8 (not the offset-2 u16 that plays that role for
Death Knights), `planeCount=4` fixed, and there is NO embedded palette at
all — plane data starts immediately after the 9-byte header (this also
explains the previously-flagged "palette region is always non-zero"
anomaly: it was never a palette, just the first bytes of real plane data).
See `header-field-role-not-transitive-across-sibling-format.md`. A second,
independent fix was needed for the WALLDEF addressing model: a per-wall
composite-id bank (mirroring the GLIB titles' scheme 2) only covered
60/115 view slices; one flat whole-file bank per `8X8D<bank>.DAA` (mirroring
the GLIB titles' own scheme 1) covers all 115/115 with 0 out-of-range
indices — see `locally-indexed-substructures.md`. Both
banks now render 100% of their own wall views (bank 1: 50/50, was 25/50;
bank 2: 65/65, was 10/65 via coincidental id overlap with bank 1's DAX
file). **Colour palette (2026-09-01) is now RENDERED, not just greyscale** —
the `8X8D0/1/2.DAA` format itself has no embedded palette at all, so the
real candidate was found by cross-referencing `DUNGCOM.DAA` (byte-identical
to `BORDER.DAA`, the dungeon-viewport border chrome drawn on the same
screen), whose entries 16-31 exactly reproduce Death Knights' own
independently-confirmed real wall palette from its `DUNGCOM.daa` (same
filename, sibling title) — see `palette-storage-quirks.md`'s new
single-candidate/cross-title-corroboration bullet for the generalized
technique. NOT disassembly-confirmed: an exhaustive `amiga-disasm` pass
found no `LoadRGB4`/`SetRGB4`/hardware `$DFF180`-`$DFF1BE` write/Copper-list
colour block anywhere in the 479,844-byte executable (every candidate
`JSR`/`JMP -192(A6)` site individually traced and debunked via A6
provenance — a second confirmed instance of `lvo-byte-pattern-false-
positive.md`'s exact LoadRGB4(-192, graphics.library)/AllocMem(-198,
exec.library) collision). See `docs/championsofkrynn/amiga/data-
structure.md` §4's 2026-09-01 correction block and
`docs/deathknightsofkrynn/amiga/data-structure.md` §4. Real interactive
walkers built for both titles
(`tools/championsofkrynn/amiga/export-data.ts`,
`tools/deathknightsofkrynn/amiga/export-data.ts`), levels namespaced
`bank*1000 + geoId` across banks in one shared `dungeon/levels-index.json`.

### Gateway to the Savage Frontier + Treasures of the Savage Frontier + The Dark Queen of Krynn (Amiga, 2026-09-01) — three more GLIB titles, one with a genuinely new mechanism

All three are GLIB-container titles (WHDLoad rips under `data/ssi/`),
decoded by extending the existing shared stack — per-title status:

- **Gateway to the Savage Frontier**: the whole format stack (container,
  WALLDEF geometry, both 8x8 tile-bank schemes, GEO's 1024-byte record,
  ECL v1.1 table) transfers **completely unchanged** — 27/27 files,
  30/30 GEO levels, 22/30 ECL levels resolved (0 unknown opcodes
  corpus-wide), walker built.
- **Treasures of the Savage Frontier**: container/GEO/WALLDEF unchanged
  (25/25 files, 41/41 GEO levels — largest in the corpus), but ECL
  needed `OPCODE_TABLE_TREASURE_V13X` (Pools of Darkness's v1.3 table +
  three new 4-operand opcodes `0x42`-`0x44`) on top of a constant 2-byte
  `0x8813` block prefix. Solved via a `re-oracle` escalation whose
  answer was the untested COMBINATION of two individually-failed fixes
  (v1.3 table alone and prefix strip alone had both failed — see
  `individually-failed-fixes-may-combine-cleanly.md`), confirmed by
  headless-Ghidra disassembly of the title's own executable (via a
  Python RELOC32-pre-applying hunk relocator + raw `68000:BE:32` import
  — recipe now in `game-re-tooling/amiga.md`). **The bigger finding**:
  for dungeon geos 16-50 the ECL wallset-slot operands are dead
  DOS-build data — the Amiga exe's `getAreaWallsets` (file+`0x14B24`)
  unconditionally overrides all three slots from a hardcoded per-geo
  table (87/87 values verified in the real `WallDef.glb` directory
  after its hardcoded `15→32` remap); see
  `script-operands-overridden-by-exe-hardcoded-table.md`. Integrated as
  `TREASURE_EXE_WALLSETS` + a `wallsetOverride` hook in
  `tools/shared/goldbox-ecl.ts`/`goldbox-glib-export.ts`; walker built,
  29/41 levels get exe-table art, 24/41 resolve from ECL alone.
  **Wilderness geos 51-62 CONFIRMED (2026-09-01 disassembly) to have no
  wallset table at all** — `getAreaWallsets` range-checks and excludes
  them outright (a 35-entry jump table with no fallback for ids past it).
  A whole-executable string scan for `"Sky.tlb"`/`"wildcom"`/`"randcom"`
  (WITH extension) found zero hits, which turned out to be an incomplete
  search rather than proof no reference exists: **this executable is a
  7-segment `HUNK_OVERLAY`-linked binary** (1 resident root + 6 on-demand
  overlays), and every disassembly pass on it — including the confirmed
  `getAreaWallsets`/`LoadWalldef` call graph — had only ever covered the
  resident root. A raw `HUNK_HEADER`/`HUNK_OVERLAY`/`HUNK_BREAK` magic scan
  found the 6 overlay boundaries in minutes; a bare-basename (no `.tlb`)
  whole-file string search then found `"Sky"`/`"DungCom"`/`"WildCom"`/
  `"RandCom"` (a 4th real file, `dungcom.tlb`, previously uncatalogued)
  sitting inside 2 non-resident overlays — the extension is synthesized at
  runtime by a confirmed generic `sprintf('%s.tlb',name)` helper, so only
  the bare name is ever stored. A follow-up disassembly (2026-09-02) fully
  cracked the dungeon/wilderness SELECTOR inside one overlay: a flag at
  offset `0x80` of the current-area descriptor (the SAME field
  `LoadWalldef` reads) picks "DungCom" vs "WildCom" (plus always
  "RandCom"), independently re-verified byte-exact. The actual registration
  call resolves through a small-data trampoline slot whose on-disk bytes
  are a literal unpatched `JMP.L $0` — the real callee is itself
  overlay-resident, patched in only by AmigaOS's overlay manager at
  runtime, which is a genuine static-analysis dead end (no public
  `HUNK_OVERLAY` record spec found) rather than an incomplete trace. See
  `amiga-overlay-segment-defeats-resident-only-trace.md` and
  `docs/treasureofthesavagefrontier/amiga/data-structure.md` §4's
  correction block. What overlay rendering technique actually produces
  (first-person walls vs. a scrolling overworld) remains open, blocked on
  either the overlay manager's private patch mechanism or a live capture.
- **The Dark Queen of Krynn**: container confirmed (23/23), GEO's
  variable-size record shape cracked, ECL resolves clean `LOAD PIECES`
  slot ids. The WALLDEF-shaped wall-art compositing table is now
  CONFIRMED ABSENT, settled by disassembly, after two false-positive
  detours: an initial "no wall-art format exists" negative was overturned
  on re-verification (a `find -iname '*wall*'` search had missed the
  `8X8DB/8X8DC.TLB` tile banks), then a follow-up candidate at
  CODE+0x4206a (believed a 3-slot wallset loader) was itself
  self-corrected by the tracing `amiga-disasm` subagent on its own
  follow-up trace — the 3 "slot" globals are the party's own
  (facing,X,Y) map position, and the function is a topview redraw with
  exactly 3 internal callers, not a wallset loader. This title renders
  via overhead/topview (`TOPVIEW.TLB`, built from `8X8DB`/`8X8DC`) and
  static `PICA`/`PICB`/`PICC`/`BIGPIC` picture banks instead of
  first-person wall compositing. See
  `docs/darkqueenofkrynn/amiga/data-structure.md` §3.

Full evidence: `docs/goldbox-glib-format.md` §7.4's coverage table +
each title's `docs/<game>/amiga/data-structure.md` and `TODO.md`.

## Elvira: Mistress of the Dark / Elvira II: The Jaws of Cerberus / Waxworks (Amiga, AGOS engine)

First AGOS-engine (Adventure Soft/Horrorsoft) titles in this corpus, first
contact 2026-09-02. `data/elvira/amiga/`, `data/elvira2/amiga/`,
`data/waxworks/amiga/` (relocated from `data/_unexplored_/{Elvira,Elvira2,Waxworks}`).

- **Container**: "old bundle" `.pkd`/`.out` resource files, `simon_decr` — a
  backward-reading, bit-oriented LZ77 codec ported bit-for-bit from
  ScummVM's `scummvm-tools/engines/agos/extract_agos.cpp`. Same codec
  across all three games, byte-exact-clean-decode (zero errors) against
  every real file: 130/130 Elvira 1, 200/200 Elvira 2, 298/298 Waxworks.
  This refuted a prior `docs/_unexplored_/probe-recon.md` triage
  hypothesis ("Elvira 2's `.pkd` has a different header, likely a later
  packer revision") — the apparent header difference was just normal
  LZ77 compressed-content variance at the stream's start, not a second
  container format; corrected in place with a `> **Correction:**` block.
  Filenames: `%.2d%d.pkd` (Elvira 1/2, 2-digit zone) vs `%.3d%d.pkd`
  (Waxworks, 3-digit zone); type 1/2 = graphics/palette resources, type 3
  (`.out`) = sound effects (confirmed NOT `simon_decr`-compressed — throws
  a decode error when run through the codec; still undecoded).
- **Picture codec**: AGOS "VC10" planar-to-chunky Amiga bitmap format
  (`res_ami.cpp`'s `convertAmigaImage`/`convertCompressedImage`/
  `uncompressPlane`/`bitplaneToChunky`), with two genuinely different
  pixel-layout branches gated by a per-image flag: compressed images store
  planes as column-major 16px-wide vertical strips needing RLE +
  reassembly; uncompressed images store plane words INTERLEAVED per
  source position, read plain row-major — the two branches do NOT share a
  layout, a first-draft assumption that had to be corrected against the
  source before shipping.
- **Palette**: Amiga 12-bit RGB words scaled by `nibble*32` (truncating —
  NOT the more common `nibble*17` bit-replication scale). Cross-verified
  via two INDEPENDENT live ScummVM code paths using the identical formula:
  `vga_e2.cpp`'s `setPaletteSlot()` (the real, gameplay-invoked VC opcode
  46/47/48 handler) and `debug.cpp`'s debug-only `palLoad()`.
- **Result**: 5,745 pictures decoded and rendered total (1,124 Elvira 1
  across 62/65 zones, 2,303 Elvira 2 across 93/100 zones, 2,318 Waxworks
  across 126/156 zones), visually confirmed as coherent, thematically
  correct scenes (garden/courtyard, werewolf creature, Egyptian tomb,
  dungeon walls). Elvira 2 also ships 4 plain IFF `ILBM` dungeon-map files
  directly in a `Pics/` directory, decoded byte-exact via a new generic
  `tools/shared/ilbm.ts` (composes `@seer-project/iff`'s
  `parseIff`/`findChunk`/`decodeByteRun1` with `tools/shared/amiga-planar.ts`) —
  reusable beyond AGOS for any project with plain ILBM/PBM assets.
- **Shared decoder**: `tools/shared/agos-vga.ts` (`simonDecr`, palette load,
  anim-table parse, VC10 image decode) + `tools/shared/agos-vga-export.ts`
  (per-zone export orchestration, atlas packing). Per-game wrappers:
  `tools/elvira/amiga/export-data.ts`, `tools/elvira2/amiga/export-data.ts`,
  `tools/waxworks/amiga/export-data.ts`.
- **Still open** (see each game's `docs/<game>/TODO.md`): `.out`/`.OUT`
  sound-effect resources (not `simon_decr`-compressed, format unknown);
  `vga1`'s non-palette content (object defs, room text, VC opcode
  scripts); `*tune` music files; Waxworks' `text01`-`text25`/
  `tables01`-`16`/`xtable01`-`04` file family (likely dialogue/narration
  tables — the single biggest remaining lead across all three games); a
  handful of misc files (`ICON.DAT`, `menus.dat`, `gameamiga`, `runit`,
  `start`, `stripped.txt`).

Docs: `docs/agos-pkd-format.md` (shared container/codec spec — the
`docs/goldbox-glib-format.md` pattern), `docs/elvira/amiga/data-structure.md`,
`docs/elvira2/amiga/data-structure.md`, `docs/waxworks/amiga/data-structure.md`,
and each game's `docs/<game>/TODO.md`.

## Bard's Tale I / II / III (Interplay, Amiga, WHDLoad dumps)

First-contact investigation, 2026-09-02, `data/_unexplored_/{BardsTaleNTSC,
BardsTale2,BardsTale3}/`. Identity confirmed via each `.slave` file's own
embedded WHDLoad header text (`strings -n 4 *.slave`), not the directory
name — `BardsTaleNTSC` = "The Bard's Tale: Tales of the Unknown" (game 1),
`BardsTale2` = "Bard's Tale 2: The Destiny Knight", `BardsTale3` = "Bard's
Tale 3: Thief of Fate".

**"Animated picture" container (view-window portrait/monster art) SOLVED
and rendered across all 3 titles.** Ground-truth oracle: Kroah's C# "Bard's
Tale Picture Viewer" (`bringerp.free.fr/RE/BardsTale/`) ships a `Files/`
directory that is `cmp`-identical to this project's own corpus files (not
a guessed reimplementation) — its `Huffman.cs`/`RLE.cs`/`Picture_Amiga.cs`
ported line-for-line into `tools/shared/bardstale-codecs.ts`. Both BT1's
`pics` and BT2's `pics` use the same `u32BE[N]`-directory-with-no-sentinel
convention (no count field; the real element count needed empirical
determination) and the same per-record serialized-Huffman-tree scheme, but
diverge downstream: BT1 RLE-decodes the huffman payload straight to a 4bpp
**planar** 112x88 image; BT2 instead runs it through a 4-plane bit
transpose + running XOR delta, converging on the identical planar layout.
BT3's `all.pic` uses a self-describing `u32BE[N+1]` directory (last entry
== file length, an explicit sentinel — unlike BT1/BT2) wrapping a
from-scratch **LZ77+adaptive-Huffman** codec (structurally the classic
Okumura LZHUF/LHarc family: 4096-byte ring buffer, position/length values
split-coded via two hardcoded 256-entry log2-bucket tables), decoding to 4
**chunky** (packed-nibble) 112x88 4bpp sub-frames per picture + an
inter-sub-frame XOR delta — real animation content (visible frame-to-frame
variation, e.g. campfire flame flicker), not 4 copies of one frame. BT3's
palette lives in a *separate* file (`bard3`) resolved via a small 2-hop
id-remap table, unlike BT1/BT2's inline 32-byte header palette.

Real picture counts confirmed **empirically** (sequentially decode index
0, 1, 2, ... until the codec itself throws — a raw directory-offset scan
alone is not decisive with no sentinel, since garbage past the real end
can still look like an in-bounds ascending offset by coincidence): BT1 =
**55** (clean, contiguous, no placeholders), BT2 = **61** real pictures out
of 64 directory slots (3 confirmed genuine placeholder/sentinel records —
`sizeDst=1`, a real deliberate 10-byte record, byte-identical at all 3
occurrences, not corruption), BT3 = **84** (directory has 86 `u32BE`
entries = 85 record spans + 1 sentinel at index 85 — an earlier same-session
pass miscited the sentinel as index 84, corrected after a regression test
caught it; index 84 itself is a real, distinct, addressable 85th record
whose header declares a plausible size matching every real picture's
constant but whose LZ77 stream runs past EOF — open, not yet explained).
All 55+61+336(=84×4) images render as recognizable, non-degenerate
character/monster/scene art (warriors, wizards, dozens of monster types, a
"Garth's" shop sign, matching "Interplay Productions" splash panels in
both BT1 and BT2's picture banks) — this project's usual bar of "renders
recognizably, not just decodes without error," not a pixel-exact oracle
(none was available). Extractors: `tools/bardstale{1,2,3}/amiga/
export-data.ts`. Sourced `undefined-nan-defeats-decrement-loop-termination.md`
(two real infinite-loop bugs while porting the codec: a mis-transcribed
256-entry hardcoded table, and an unbounded allocation from probing
out-of-range picture indices) and `erasable-syntax-only-rejects-parameter-
properties.md` (a TS1294 tsconfig gotcha hit while writing the bit-reader
class). See `docs/bardstale-picture-format.md` (shared container/codec
spec) and each title's `docs/bardstale{1,2,3}/amiga/data-structure.md` +
`docs/bardstale{1,2,3}/TODO.md`.

**Still wide open** (first-contact pass prioritized breadth — one confirmed
asset category per game — over depth): BT3's `.GRP` files (likely
first-person wall/dungeon-view graphics), `maps.hi`/`maps.lo` (same
directory container as `all.pic`, content undecoded), `monsterh`/
`monsterl` (same container; an earlier raw-planar/chunky hypothesis, tried
*before* the LZHUF codec was known, failed a `seer-probe gfx` sweep — not
yet re-attempted with the correct codec), 4 real IFF ILBM screens
(confirmed via container triage, trivially decodable with
`@seer-project/iff`, not yet done), and each game's audio/instrument files
(`chant`/`drums`/`harp`/`panflu`/`trumpet` — thematically the bard-song
mechanic, not yet investigated) and 68k executables (undisassembled). BT2
additionally has an unexplored second picture-like file, `wpics`.

## Dungeon Master / Dungeon Master II: Skullkeep / Chaos Strikes Back (FTL Games, Amiga)

First-contact investigation, 2026-09-02, `data/_unexplored_/{DungeonMaster,
DungeonMaster2,ChaosStrikesBack}/`. Shared container/codec/dungeon formats
documented once in `docs/dungeonmaster-format.md` (the middilgard-style
"one doc for a container shared by several games" convention); per-game
docs (`docs/dungeonmaster/`, `docs/dungeonmaster2/`, `docs/chaosstrikesback/`,
each with `amiga/data-structure.md` + `TODO.md`) cover what's specific.
Shared code: `tools/shared/dungeonmaster-{container,codec,dungeon,render}.ts`,
`tools/shared/amiga-player4x.ts`. Extractors: `tools/dungeonmaster/amiga/`,
`tools/dungeonmaster2/amiga/`, `tools/chaosstrikesback/amiga/export-data.ts`.

**Data-file container** (`GRAPHICS.DAT`/`ANIM.DAT`/`HCSB.DAT`/...): three
signature variants confirmed across the family — `DMCSB1` (rare),
`DMCSB2` (`0x8001` signature; both DM1 and CSB's real corpus files, NOT
`DMCSB1` as first assumed by community-doc-version analogy — a real
mid-session correction, caught only because a byte-exact regression test
failed, not by inspection), and `DMII` (`0x8005`, DM2). Item directory +
size/offset table shape otherwise shared.

**`IMG1`/`IMG2` pixel codec** (DM1, CSB): 4bpp nibble-RLE, no local
palette — straightforward, matches the primary "dmweb" Dungeon Master
Encyclopaedia community docs directly.

**`IMG3`/`IMG4` pixel codec** (DM2 only) — a real correction over naive
sibling-decoder reuse, not a straightforward port: DM2's `GRAPHICS.DAT`
shares DM1/CSB's exact container and the `IMGx` codec-naming family, which
looked like license to reuse the `IMG1` decoder unchanged. That produced
visual garbage. The primary "dmweb" docs' own per-file item-type table for
this exact file flags ~4,521/4,630 items `RAW1` ("not yet decoded") — the
most-authoritative source had no answer for this file specifically. A
**secondary** fan-analysis source ("Dungeon Master II Data Files Notes")
named the real codec: `IMG3`(LE)/`IMG4`(BE), a 6-nibble local-palette
prefix + a different control-nibble grammar (bit 3 = single/multi run,
bits 2-0 = a colour selector meaning local-palette-index / copy-from-
line-above / absolute-colour-via-extra-nibble, none of which `IMG1` has).
Implemented as `decodeImg4()`; **2,237/2,263 (98.9%)** of plausible-header
items decode to >=95%-filled pixel buffers with 0 exceptions, rendering
real multi-language status-bar UI text (`HEALTH/STAMINA/MANA`,
`GEZOND/KRAFT/MANA`, `SANTE/VIGUEUR/MANA`, ...) plus weapon/wall-texture
art. Sourced `sequel-shares-codec-family-name-not-byte-grammar.md`. **Open**:
the remaining `IMG7`/`IMG8` differential/overlay sub-format (~11% of
image-shaped items, a cross-image compositing mechanism the fan source
itself hedges on).

**Dungeon file format** (`DUNGEON.DAT`, all 3 games): 44-byte header,
16-byte per-map definitions, column-major square grid; `0x8104`
Huffman-style compression confirmed and decoded (DM1/CSB use it, DM2's
corpus copy is uncompressed). DM2's grid is the first corpus file to
exercise the DM2-only square type `empty` (type 7) as real, non-degenerate
data. CSB's dungeon data is embedded inside a saved-game file rather than
shipped standalone — located via a structural-invariant scan
(`docs/dungeonmaster-format.md` § "Locating CSB's dungeon inside a
saved-game file").

**CSB's 3 ADF disk images** mounted as real AmigaDOS filesystems (not just
raw-byte scanned) — this pass found and fixed a real bug in the shared
upstream `@seer-project/amiga` package's extension-block-chain-following
logic along the way (affects any Amiga project using that package for
files needing more than one extension block).

**`P41A` module packer, DM2's `music/*.MOD` (x10)** — despite the
extension, real bytes show every file is `P41A`-signed ("The Player 4.1A"
by Jarno Paananen/"Guru", never released as a standalone tool but
licensed/leaked to game studios; a real proprietary-Amiga-tracker-packer
class, not specific to this engine). Found via `libxmp`'s ProWizard
multi-format module-unpacker collection (`src/loaders/prowizard/p40.c`'s
`depack_p4x()`) — no dedicated fan tool exists for this packer by name, but
a general-purpose collection built to cover the long tail of obscure
tracker packers had it. Ported faithfully, statement-by-statement, into
`tools/shared/amiga-player4x.ts` (preserving the reference's exact
`for`/`continue`/`break` loop shapes rather than manually flattening to
`while`, sidestepping the classic C-port iteration-shift trap by
construction — see `decompressor-port-loop-condition-iteration-shift.md`'s
avoidance note). Verified against all 10 real files: 0 decode exceptions,
byte-exact re-encoded-size self-consistency against a standard `M.K.`-
tagged ProTracker output, and a quantitative RMS + lag-1 sample-
autocorrelation "real audio vs. decode-bug" check (29/30 samples strongly
self-correlated, `r1` in `[0.57, 0.99]`; the one exception has a
non-degenerate amplitude range consistent with a percussive/noise
instrument). Not verified by ear (no audio player in this environment).
Sourced `romhacking-community-tools-first.md`'s ProWizard subsection.

**Open**: the Amiga palette for all three games (all `IMGx` output ships
as greyscale-ramp placeholder over confirmed-real pixel indices — several
scene-dependent palette table names are known leads, none located yet),
DM2's `IMG7`/`IMG8` sub-format, DM2's `sample_palette.IFF` (a real ILBM,
not yet opened), and per-map object/door/teleporter/creature/text/sensor
lists in the dungeon file (container shape not yet extended to parse
them). See each game's `docs/<game>/TODO.md` for the current status
table.

## Corpora-index row text formerly inline in `game-re.md`

Moved verbatim from the always-loaded agent prompt during the 2026-10 restructure.

| `~/Development/crawl` | Black Crypt, Eye of the Beholder 1-3, Lands of Lore, Dungeon Hack, Might & Magic I/II/III, Wizardry 6, the original 4 SSI Gold Box titles (Amiga: Pool of Radiance, Curse of the Azure Bonds, Secret of the Silver Blades, Pools of Darkness — GLIB/`.dax` container+codec, GEO maze grid, and ECL bytecode wallset-slot binding all cracked, shared interactive walker built) plus Champions of Krynn + Death Knights of Krynn (Amiga; a SECOND, genuinely different "DOS DaxFile" container+codec — 9-byte LE directory entries, PackBits-style RLE, matches `simeonpilgrim/goldboxexplorer`'s DOS-side `DaxFile.cs` exactly, NOT Pool of Radiance's own bespoke Amiga codec despite sharing the `.dax`/`.DAX` extension and base filenames; `tools/shared/goldbox-dosdax.ts`. GEO/ECL/WALLDEF downstream formats transfer unchanged; both titles' ECL engine revision confirmed v1.1/base-0x8000/opcode-0x37, same as PoR/Curse/Secret — an initial ratio-driven "needs Pools' v1.3 table" hypothesis for Death Knights was refuted by manual disassembly, see `uniform-degenerate-hit-value-signals-wrong-decode-config.md`. Real interactive walkers built for both, 2-3 campaign banks namespaced `bank*1000+geoId`; wall-art PNGs render for ALL of Champions (115/115 across both banks) and ALL of Death Knights (105 PNGs, a BIG-ENDIAN "Amiga DAA" sibling container cracked via `re-oracle` — see `individually-failed-fixes-may-combine-cleanly.md`'s 2nd instance and `tile-bank-index-zero-not-universally-a-placeholder.md`) — Champions' own `8X8D0/1/2.DAA` pixel payload and colour palette are both now solved too (palette RENDERED via cross-title corroboration against DKK's own `DUNGCOM.daa`, not disassembly-confirmed — see `palette-storage-quirks.md`), plus Gateway to the Savage Frontier + Treasures of the Savage Frontier + The Dark Queen of Krynn (GLIB again; Gateway's whole format stack transfers unchanged, but Treasures needed a new opcode table — Pools' v1.3 + 3 new opcodes + a 2-byte block prefix, the answer being the untested COMBINATION of two individually-failed fixes, see `individually-failed-fixes-may-combine-cleanly.md` — and its ECL wallset operands turned out to be dead DOS-build data unconditionally overridden by a table hardcoded in the Amiga executable, see `script-operands-overridden-by-exe-hardcoded-table.md`; Treasures' wilderness geos 51-62 confirmed to have no wallset table at all, a separate overland renderer not yet traced; Dark Queen's WALLDEF-equivalent compositing table now confirmed absent by disassembly — this title renders via topview/static-picture banks instead), Ishar 1-3 + Crystals of Arborea (Amiga AGA, Silmarils ALIS container/codec; a `re-oracle` escalation found the first-person view has NO static terrain/geometry data at all — each location's own compiled ALIS bytecode script IS the renderer, executed live against the world's `.FIC` region grid — and a follow-up session built a scoped bytecode disassembler+interpreter, `tools/shared/alis-{disasm,interp}.ts`, verified 256/256 instructions against a hand-checked reference disassembly, and rendered real, position/facing-responsive first-person frames end-to-end for SIX location scripts total, wired into both titles' walkers behind a `KeyC` cycle toggle: Ishar 1's `FORET`/`VILLAGE`/`PLAINE`/`RAMPART.bin` (forest/village/plains/fortress, against region `CONT1` — except `RAMPART`, whose real cell cluster is `CONT3`/`CONT4`) and Crystals' `ARBRE`/`NPLAINE`/`PLAGES`/`CAVINT.bin` (forest/plain/beach/cave, against a genuinely N-ary `INIT.FIC` local-scene array rather than a `CONT*.FIC` world grid). Each script beyond the first was found the same way: disassemble that script's OWN `cswitch1`/`cswitch2` cell-value dispatch to get its real accepted value set, then scan the real grid/array for matching cells — never guess a shared test position. `CAVINT.bin` needed a real correction: a prior pass's untested "maybe it reads the indoor Z=1 sub-layer" guess had been marked INCONCLUSIVE after rendering blank at a position borrowed from `ARBRE`'s own (Z=0, outdoor) cluster — disassembling `CAVINT`'s own dispatch and finding its value alphabet exists ONLY in `INIT.FIC`'s Z=1 sub-array (zero matches at Z=0) confirmed the layer guess was right all along; only the borrowed test position was wrong (see `hypothesis-tested-with-mismatched-input-looks-refuted.md`). `TEMPLE.bin` (Ishar 1) remains INCONCLUSIVE; Ishar 2/3 not attempted), plus Elvira: Mistress of the Dark + Elvira II: The Jaws of Cerberus + Waxworks (Amiga, first AGOS-engine title in this corpus — Adventure Soft/Horrorsoft's `simon_decr` backward-reading bit-oriented LZ77 "old bundle" container, ported from ScummVM's `extract_agos.cpp` and confirmed byte-exact-clean-decode across all 628 real `.pkd` files in all three games with ONE shared decoder — refuting a prior probe-recon "Elvira 2 uses a different container" hypothesis, which was just normal compressed-content variance; the VC10 planar-to-chunky picture codec and an unusual `nibble*32` Amiga-palette scale, cross-verified via two independent ScummVM code paths, are also solved and shared; 5,745 pictures rendered across the three games, `docs/agos-pkd-format.md`), plus Bard's Tale I/II/III (Amiga — the "animated picture" (portrait/monster art) container across all 3 titles cracked via a byte-exact oracle, Kroah's C# Picture Viewer, whose bundled `Files/` dir is cmp-identical to this project's own corpus files; BT1/BT2 = per-file-serialized Huffman tree + RLE or bit-transpose+XOR, 4bpp planar 112x88; BT3 = a from-scratch Okumura LZHUF/LHarc-family LZ77+adaptive-Huffman codec, 4 chunky sub-frames + inter-frame XOR delta, palette resolved via a separate file's 2-hop id-remap table. Real picture counts confirmed empirically (55/61+3 placeholders/84), 336+ images rendered and visually confirmed non-degenerate. Sourced `undefined-nan-defeats-decrement-loop-termination.md` and `erasable-syntax-only-rejects-parameter-properties.md`. See `docs/bardstale-picture-format.md`), plus Dungeon Master + Dungeon Master II: Skullkeep + Chaos Strikes Back (Amiga, FTL Games — first-contact pass: shared DMCSB1/DMCSB2/DMII data-file container, `IMG1`/`IMG2` 4bpp nibble-RLE pixel codec (no local palette, DM1/CSB), the 44-byte-header/16-byte-per-map/column-major-square dungeon grid format, and `0x8104` Huffman-style dungeon compression all cracked and documented once in `docs/dungeonmaster-format.md`; CSB's 3 ADF disk images mounted as real AmigaDOS filesystems (fixing a real upstream `@seer-project/amiga` extension-block-chain bug along the way) and its dungeon-embedded-in-savegame location technique solved. DM2 needed real correction over naive sibling-decoder reuse: `GRAPHICS.DAT` is NOT `IMG1` despite sharing the container and the `IMGx` naming family — it's `IMG3`/`IMG4` (6-nibble local palette, different control-nibble grammar), named by a secondary fan-analysis source after the primary "dmweb" community docs' own item-type table flagged ~4,521/4,630 items `RAW1` ("not yet decoded") for this exact file (98.9% of image-shaped items now decode clean; see `sequel-shares-codec-family-name-not-byte-grammar.md`, sourced from here). DM2's `music/*.MOD` (x10) are also NOT standard ProTracker despite the extension — all `P41A`-signed ("The Player 4.1A," a proprietary Amiga module packer never released standalone), decoded via a faithful TypeScript port of libxmp's ProWizard `depack_p4x()` (`tools/shared/amiga-player4x.ts`), verified via RMS+lag-1-autocorrelation audio-quality check against all 10 real files (see `romhacking-community-tools-first.md`'s ProWizard subsection, sourced from here). Open: DM2's `IMG7`/`IMG8` differential/overlay image sub-format (~11%) and the Amiga palette for all three titles (`docs/dungeonmaster2/TODO.md`) | `game-re-corpora/crawl.md` |
