# Drakkhen (Amiga + Atari ST)

Project: `~/Development/drakkhen`. Status: **container formats + codec
cracked and verified** (2026-08-13); deeper asset coverage ongoing.

## Solved formats (spec: `docs/drakkhen/atarist/data-structure.md`)

- **Data files are shared between the Amiga and Atari ST versions** (same
  FAT names, same container layouts). The definitive spec was derived from
  Kroah's Drakkhen Viewer v1.00 **C# source** (an Atari ST tool,
  bringerp.free.fr) — disks `.st`, 1 MB RAM snapshots, ST/STe palette
  lookups — and verified against the flat files in `data/drakkhen/amiga/`.
- **`.mc1` multi-resource container**: `u16 count` @0, `count` u32
  **relative** offsets @2 (`entry[0]=0`), each block `[u32 packed][u32
  unpacked]` + blob; blocks contiguous to EOF. `.mc0` = single-block
  variant (`[u32 packed = len-8][u32 unpacked]` + blob).
- **Codec** (`Unpacker.cs`): block-chained static-Huffman/raw scheme —
  `[b0 = table-entries count][b1 = more-blocks][count LE16]`, 3 tables of
  b0 bytes (table A = output symbol values — the "ASCII dictionary" look),
  then a symbol stream; b0=0 ⇒ raw copy. Ported to TS
  (`src/data/formats/unpack.ts`), verified **154/154 blocks byte-exact**
  against `nbBytesUnpacked` (the container's own length = free oracle).
- **Sprites**: 2-byte header (w/16, h), 4bpp 16-px-interleaved bitplanes,
  index 0 transparent; sprite bank = `[u32 tableSize][nb × u32 offsets]`.
  Pixel-exact vs the reference viewer's own rendered PNGs.
- **Palettes**: raw 16-bit words, platform-interpreted (ST 3-bit /
  STe 4-bit / Amiga 4-bit×17). Sprite palette = RAM-dump pal1 @0x2CB6C
  (v11 build); **original-release Amiga palette location still open**.
- **World map** (decompressed `ext.mc0`): 32×32 zones ×128px; zone
  templates (grounds + hazards) and ground polygons with fixed tables.
- **`def.mc1`** = 6 dungeons (rooms: decor objects, 8 exits, switches);
  **`reg.mc1`** = 6 dungeon-script VM blocks (word-addressed instruction
  stream, fully documented opcodes); **`mon.mc1`** = 60 monsters
  (sprite banks or vector banks); `.txt` = dialogue files
  (`[nbCols][nbRows-1][unk01][unk02]` + lines).
- **FAT/disk**: `.st` sector images, FAT at 0x400 (`[name 12][offset u32]
  [size u32]`, 20 B/entry, disk name @0x7FC). The Amiga `DIR1`/`DIR2` are
  the same FAT extracted from `disk.1`/`disk.2`.
- **`.am2` files** (`jdr.am2` main program, `crea.am2` creatures) =
  custom-prefixed Amiga hunk blobs with real 68k code — the game's own
  loader, source for future data-table RE.

## Reference material

- Kroah's Drakkhen RE site: `http://bringerp.free.fr/RE/Drakkhen/main.php5`
  (missions, day cycle, items, world-map viewer, dungeon maps/scripts;
  the viewer's rendered PNGs are pixel oracles).
- Viewer archive (source + ST disks + RAM dumps) via the site's
  `utility.php5` page; disks + dumps live in `data/drakkhen/atarist/`.

## Version caveat (lesson: `reference-tool-data-revision-mismatch.md`)

The viewer ships **v1.1 disks** whose files are renamed (`jdr.app`,
`garde.tc1`, `res.tc0`, `resid.ech`) and whose `res.tc0` bank layout
differs from the original-release `res.mc0` (original has an extra bank;
bank numbering shifts by one). Palettes also differ between the v1.1 RAM
dump and the original release. Same formats, different revisions — verify
which revision your data matches before trusting versioned table pointers.

## Lessons sourced from this corpus (full list)
`reference-tool-data-revision-mismatch.md`, `decompressor-port-loop-condition-iteration-shift.md` (compiled 2026-10-06 by grepping `game-re-lessons/` for Drakkhen; the pre-2026-10 summary had no sourced list)
