# drakkhen — Drakkhen (Infogrames; Amiga + Atari ST)

**Project root:** `~/Development/drakkhen` · **Full history/evidence:** `game-re-corpora/details/drakkhen.md` (read on demand) · **Open work:** `docs/drakkhen/TODO.md` (single status surface; milestones in `docs/drakkhen/plan.md`)

Only registered id: `drakkhen`/`amiga` (`src/game-id.ts`). ST disks and RAM dumps in `data/drakkhen/atarist/` are reference material. `data/drakkhen/snes/` holds an untouched SNES (USA) zip.

## Games
- Drakkhen (Amiga, original release) — `drakkhen`/`amiga` — containers, codec, sprites, world map, dungeons, script VM, game-data tables, audio samples + `.dum` music all decoded; runtime not started
- Drakkhen (Atari ST, v1.1 disks from the reference viewer) — not registered. It shares the data formats and is used as the oracle
- Drakkhen (SNES) — data present, not investigated

## Solved formats → where documented
Master byte-level spec is the ST doc: `docs/drakkhen/atarist/data-structure.md` (cited by §). The Amiga per-file inventory with corrections is `docs/drakkhen/amiga/data-inventory.md`. All multi-byte values are big-endian.
- `.st` disk + FAT at 0x400 (20 B entries); Amiga `DIR1`/`DIR2` are the same FAT — §1
- `.mc1` multi-block container (`u16 count`, u32 relative offsets at +2, blocks `[u32 packed][u32 unpacked]`+blob) and `.mc0` single-block — §2-3, `src/data/formats/containers.ts`
- Block-chained static-Huffman/raw codec (`Unpacker.cs` port). 154/154 blocks decode to their declared `nbBytesUnpacked` (hard failure in `build-assets`) — §4, `src/data/formats/unpack.ts`
- Sprites: 4bpp, 16-px-interleaved planes, index 0 transparent. Pixel-exact against the viewer's PNGs — §5, `sprite.ts`. Palettes: raw words, ST/STe/Amiga interpretation — §6, `palette.ts`
- World map `ext.mc0` (32×32 zones, ground polygons, hint overlays), rendered 96-97% pixel-exact against the viewer export — §7, `map.ts`, `map-render.ts`. Vector monsters + castles — §8, `vector.ts`
- Dungeons `def.mc1` (6 dungeons, 171 rooms; exit graphs 100% vs viewer pages) — §10, `dungeon.ts`. Dialogue `.txt` — §11, `text.ts`. Script VM `reg.mc1` (149 procedures, strings 120/120) — §12, `script.ts`
- Static tables (60 monsters, 47 items, names, overlays, sky gradient) come from `jdr.am2` itself, not the RAM dumps. Weapons and armour match Kroah's items table exactly — §13, `game-data.ts`
- Audio: `.ins`/`.inm` 8-bit delta sample banks (29 WAVs). `.dum` sequences were decoded from the 68k player in `jdr.am2` (period table 0x1EC6E, duration table 0x1E9A4) — §13b, `audio.ts`
- `.am2` (`jdr.am2` main program, `crea.am2` creatures): custom-prefixed hunk blobs with 68k code at +0x28 — inventory §4

## Engine-family / cross-project links
- Amiga and ST share data-file names and container layouts, so ST tooling decodes Amiga files.
- Oracle: Kroah's Drakkhen RE site (`bringerp.free.fr/RE/Drakkhen/main.php5`). Its Drakkhen Viewer v1.00 C# source (`utility.php5`) is the format spec, and its rendered PNGs and GoJS dungeon/script pages are pixel/graph oracles. Kroah's viewers are also oracles in `crawl` (Bard's Tale) and `nicodemus` (Phantasie III sprites).

## Reusable code in this repo
- `src/data/formats/unpack.ts` — Drakkhen Huffman/raw block codec; `containers.ts` (`.mc0`/`.mc1`)
- `src/data/formats/map-render.ts` — polygon map renderer on `@seer-project/gfx` (`scanlineFillPolygon`, `bresenhamLine`)
- `src/data/formats/script.ts` — dungeon-script VM disassembler; `tools/drakkhen/build-assets.ts` registered as the `buildAssets` hook in `tools/shared/game-config.ts`

## Know before you start
- The viewer's bundled data is **v1.1**: renamed files (`jdr.app`, `garde.tc1`, `res.tc0`, `resid.ech`), a `res` bank layout shifted by one (the original has an extra bank), and different palettes. Our Amiga files are the original release. Check which revision you are looking at before reusing a versioned pointer.
- RAM dumps (`20 Start v11.dmp`, `61 Dungeon-Start v1.1.dmp`) are **1 MB Atari ST** snapshots of v1.1, not Amiga dumps. Extract tables from `jdr.am2`, never from the dumps.
- The sprite palette in the pipeline is a reference-derived constant (v1.1 dump pal1 at 0x2CB6C). The palette embedded in `res.mc0` at +0x20 is a decoy. The original Amiga palette is absent from every shipped file. Its loader (`jdr.am2` 0x18A64) has no in-file callers because dispatch is indirect/relocated. The same blocker affects the `.dum` transpose init (`$3ADC`) — see TODO `palette-source`, `dum-transpose`.
- Old readings of the `.mc1` table were 2 bytes late, and the "ASCII dictionary" in blobs is really Huffman table A. Trust the `> Correction` blocks and the ST master spec.
- `perso`, `activ`, `arme.aju`, `objet.tra` and the full `.am2` layout are never read by the viewer, so there is no oracle for them. Derive them from `jdr.am2` code.
- `.am2` headers are non-standard (table size 0, extra prefix words), so stock hunk loaders may reject them. There is no bootable OS executable in the data set.

## Key lessons
- `reference-tool-data-revision-mismatch.md` — viewer's v1.1 disks: renamed files, shifted `res` banks, different palettes
- `decompressor-port-loop-condition-iteration-shift.md` — `Unpacker.cs` port read one extra byte per block
- `embedded-palette-not-the-installed-palette.md` — `res.mc0` +0x20 palette parses cleanly but doesn't colour sprites
- `palette-storage-quirks.md` — original Amiga sprite palette is absent from every shipped file
- `relocated-base-plus-displacement-hides-call-target.md` — palette loader and `$3ADC` init have no literal in-file callers
- `romhacking-community-tools-first.md` — Kroah's viewer source was the master spec; check it first
- `length-invariant-blind-to-copy-semantics.md` — `nbBytesUnpacked` matches don't prove copy semantics; pixel-diff too
- `step-runs-standalone-but-not-pipeline-registered.md` — `build-assets` only runs via the `game-config.ts` hook

Full list: `details/drakkhen.md` § "Lessons sourced from this corpus (full list)".
