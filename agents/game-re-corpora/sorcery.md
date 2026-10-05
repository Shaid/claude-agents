# sorcery — Wizardry 6: Bane of the Cosmic Forge (Sir-Tech; DOS/EGA, Amiga, SNES)

**Project root:** `~/Development/sorcery` **no longer exists** — Wizardry 6 was migrated into `~/Development/crawl` (commit `ec912bd`); all paths below are relative to `crawl`, and `crawl.md` is the corpus for new work there · **Full history/evidence:** `game-re-corpora/details/sorcery.md` (read on demand) · **Open work:** `docs/wizardry6/TODO.md`

## Games
- Wizardry 6 (DOS/EGA, the source platform) — `wizardry6`/`dosega` — all containers decoded; overlay bodies + race table open
- Wizardry 6 (Amiga) — `wizardry6`/`amiga` — text, graphics, maze geometry, catalogs, deferred-draw renderer done; pcfile spans open
- Wizardry 6 (SNES, Japan-only, ASCII 1995) — `wizardry6`/`snes` — scheduler, text, font, portraits, view walk shipped; kanji mapping open

## Solved formats → where documented
- `.hdr`/`.dbs` containers (`misc.hdr` Huffman tree, `master.hdr`/`disk.hdr` sections over `scenario.dbs`, `msg.dbs` paged Huffman text, `pcfile.dbs`) — DOS = Amiga layout with every multi-byte field endian-swapped — confirmed — `docs/wizardry6/amiga/data-structure.md`, `docs/wizardry6/dosega/data-structure.md`
- `scenario.dbs` sections: XP/item/monster catalogs (monster HP `+0x78`, stamina `+0x7c`, resistances `+0x95`; alignment does not exist), maze geometry (sec 2; 14 levels × 12 8×8 regions, 2-bit wall planes), entity table (sec 3, structure), NPC names (sec 5), event scripts (6), treasure table (7) — confirmed — `docs/wizardry6/amiga/data-structure.md`
- Amiga `.EGA` screens (4 planes each padded to 8192 B) and `.PIC` cels (plane-major 4bpp, tile-presence bitmask); `mazedata.ega` art bank + `DrawMazePiece`; deferred-draw queue — confirmed — same doc
- DOS `.pic` = 4096-byte-block byte RLE around the Amiga tile payload (712 cels byte-exact); `.cga` (2bpp, banked CGA memory) / `.t16` (4bpp) are packed-pixel, not planar; `mazedata.ega` directory drops the offset field (cumulative sum); `.ovr` header is 14 bytes; `DS = CS + 0x0fd8` — `docs/wizardry6/dosega/data-structure.md` §6, §9
- Wall values (cross-platform): 0 open, 1 doorway, 2 wall, 3 closed door — confirmed by SNES view walk
- SNES: task scheduler, SPC700 upload + 151-module directory at `$A0:8000`, 8-bit text encoding, class/monster name tables, portrait + UI icon banks, opening sequence, 256-glyph font, 139-record spell-animation bank (LZSS), first-person view walk `$80:C69F` — `docs/wizardry6/snes/data-structure.md`

## Engine-family / cross-project links
- Amiga port was built from the DOS/EGA build (filename tables, palette order). SNES is an unrelated toolchain — a game-content oracle only.
- Zimlab.com Wizardry VI bestiary = numeric oracle for monster stats (`published-walkthrough-numeric-oracle.md`).
- `strike`'s SNES DMA-register census technique applies to SNES graphics here.

## Reusable code in this repo
- `tools/shared/snes-lzss.ts` (2 KB-window LZSS, 22 call sites), `tools/shared/snes-ppu.ts` (4bpp/2bpp tiles + BGR555), `tools/shared/amiga-planar.ts`
- Packed-pixel / CGA-banked decode now lives in `@seer-project/gfx` (`decodePackedPixelLinear`, `decodeCgaBanked`) — was `tools/shared/packed-pixel.ts`
- Decoders/renderers: `tools/wizardry6/` (+ `tools/wizardry6/snes/`)

## Know before you start
- Grep `docs/wizardry6/amiga/disasm/Bane.asm` first (99.47% code coverage after `.cnf` fix); A4 = DATA_start + `0x7FFE`; watch decimal-vs-hex A4 displacements (`game-re-tooling/amiga.md`).
- Amiga has exactly one executable, no overlays; DOS has `wroot.exe` + 11 `.ovr` overlays (`game-re-tooling/dos.md`).
- SNES: file offset ≥ `0x8000` is not bank `$00` (bank-rollover, `game-re-tooling/snes.md`); the `[tag][id]` "maze" region was really spell-animation tilemap words.
- A dead-ended dispatcher trace → census the parent function's full sibling calls (`sibling-functions-outside-callgraph-scope.md`).

## Lessons sourced from this corpus
`endian-swap-needs-matching-field-width.md`, `implicit-cumulative-directory-offsets.md`, `byte-scan-tag-byte-vs-wrong-stride.md`, `string-scan-crosses-structural-boundary.md`, `header-shape-ambiguous-pixel-encoding.md`, `planar-plane-padding-vs-tight-stride.md`, `verify-escalation-artifacts-not-just-claims.md`, `compressed-stream-start-offset.md`, `sibling-functions-outside-callgraph-scope.md`, `domain-refuted-by-shape-not-values.md`, `committed-ira-asm-silent-coverage-gap.md`, `published-walkthrough-numeric-oracle.md`, `reserved-slot-zero-shifts-extractor-index.md`, `indexed-table-base-below-valid-rom-window.md`, `nearest-preceding-immediate-is-not-dataflow.md`, `autocorrelation-period-is-the-scanline-stride.md`, `tilemap-word-assets-carry-own-palette-field.md`, `addressing-mode-operand-hides-implicit-index-offset.md`
