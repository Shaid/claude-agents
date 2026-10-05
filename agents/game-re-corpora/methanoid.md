# methanoid — Millennium 2.2, Deuteros, Reunion (Amiga)

**Project root:** `~/Development/methanoid` (one repo holds all three games; there is no `~/Development/deuteros`) · **Full history/evidence:** `game-re-corpora/details/methanoid.md` (read on demand) · **Open work:** `docs/<game>/TODO.md` per game

## Games
- Millennium 2.2 (Novagen, Amiga) — game-id `millenium22`/`amiga` (one "n") — boot chain solved; palettes, audio, 135-image art bank shipped; dump truncated
- Deuteros (Novagen, Amiga) — game-id `deuteros`/`amiga` — boot chain + protection solved; title screen, palettes, audio shipped
- Reunion (Amnesty Design, Amiga AGA) — game-id `reunion`/`amigaaga` — solved end to end
- Reunion OCS/ECS (6 raw ADFs) — game-id `reunion`/`amiga` — nearly fully solved; small `.tbl` residual open

## Solved formats → where documented
- M2.2 boot chain: `BB_ENTRY` at `0xC`, then a self-relocating stub, then hand-built trackdisk I/O using standard `ETD_*` commands. `Disk.2` is a blank disk stamped by the in-game formatter (magic `0x16C65710`). `TDIC` track has no consumer (static + 3G-instruction Musashi trace) — `docs/millenium22/amiga/data-structure.md`
- M2.2 content: 2 `amiga12` palettes (LoadRGB4), Paula driver + 2 PCM banks, command grammar + 16 envelope curves (confirmed; arpeggio content only rendered), compressed art bank at `Disk.1+0x21000` (Deuteros' RLE codec, 135/136)
- Deuteros: raw flat-blob boot chain (no HUNK exe). "DISC COMPANY 010991" protection = CPU probe, then trace-vector self-decrypt, then a CIA timing check vs `$DA8DBFDB` (Musashi harness). Track-8 title picture + LoadRGB4 palette; 4 UI palettes; 13 audio-shaped regions (approx. rate 8287 Hz) — `docs/deuteros/amiga/data-structure.md`
- Reunion AGA: RNC1/IMP! via `ancient`; IFF ILBM/PBM/8SVX; ProTracker MOD; `EFT!ANIM` key+delta animation; `AMN0` wireframe models; `pmain/*.DAT` grids (role rendered, not confirmed); 1bpp `STMAP`/`GRKIEG` `.CHR` rasters; ALIEN portrait + FAJ palettes (rendered) — `docs/reunion/amigaaga/data-structure.md`
- Reunion OCS: `Install` 390-entry catalog (`(disk<<12)|block`). `1AM`/`2AM` LZ77 found in `Main.exe` (48/49 byte-identical vs AGA). Manual-code check (table `Main.exe+0x67B0`) and its gating are solved. Multi-FORM 8SVX; 242/242 planar `.CHR` screens; spwar EFT palette; `MUSIC/*.pin/.tbl/.hin` grammar — `docs/reunion/amiga/data-structure.md`

## Engine-family / cross-project links
- M2.2 and Deuteros: boot blocks are unrelated, but both use the same "Disc Company" trace-vector protection (dynamically confirmed) and the same RLE-over-16-bit-words art codec
- M2.2 is NOT a Mercenary-style vector engine despite the shared Novagen developer: 0 line/poly LVOs and 0 BLTCON0 hits (`engine-family-shared-decoder-not-shared-container.md`)
- Reunion OCS reuses the AGA `AMN0`/`EFT!ANIM` decoders unmodified, and AGA files serve as its byte-exact oracle. `AMN0` JSON follows the hunter/carrier-command polygon convention
- `decodeByteRun1()` was added to `@seer-project/iff` from this project. Use it for any IFF BODY

## Reusable code in this repo
- `tools/shared/amiga-rle-gfx.ts` — Novagen RLE-over-words codec (Deuteros + M2.2)
- `tools/deuteros/emu/`, `tools/millenium22/emu/` — Musashi 68000 harnesses (trace-vector decrypt, whole boot chain); upstream candidate
- `tools/deuteros/trace-boot-chain.ts` — reproducible raw-blob extractor
- `tools/reunion/{eft-anim,amn0,amn-lz,stmap-raster,chr-raster,ocs-audio,ocs-music,install-catalog,ocs-container}.ts`
- `tools/shared/ipf-tools/` — IPF track dump

## Know before you start
- Owner instruction for at least one Deuteros round: work statically and avoid Amiberry. Musashi harnesses are the dynamic fallback, but they cannot pass M2.2's CIA disk-index timing gate
- M2.2 `Disk.1` is truncated (67/80 cylinders, dense high-entropy tail). Static analysis cannot resolve it; it needs a fresh image
- Raw-boot games without a HUNK exe need `executable: 'Disk.1'` in game-config, or export is silently skipped. Also beware `cli-script-main-fires-on-import.md`
- Reunion: extensions mislead (`.BAT` = 8SVX, `.RDA` = chunky PBM, `.001`-`.079` are frame numbers). Dispatch on decompressed magic and keep full basenames
- IRA's `;NNNNNN` column is not a file offset once a `.cnf` spans multiple hunks (`file-offsets-vs-segment-relative.md`). Reunion is not primarily SAS/C A4-relative
- LoadRGB4/LVO hits need A6-provenance tracing (`lvo-byte-pattern-false-positive.md`). An untraced disk region is not proof of filler

## Lessons sourced from this corpus
`amiga-bb-entry-offset-is-12-not-4.md`, `self-relocating-boot-stub-invalid-past-jmp.md`, `illegal-vector-hijack-anti-debug-desyncs-disasm.md`, `m68k-trace-vector-decrypt-needs-emulate-trace-on.md`, `mistyped-base-constant-underflows-capture-buffer-bounds-check.md`, `lvo-byte-pattern-false-positive.md`, `unrecoverable-base-register-solved-from-single-content-anchor.md`, `relocation-invariant-content-across-copies-proves-placeholder.md`, `engine-family-shared-decoder-not-shared-container.md`, `disc-io-census-blind-to-already-loaded-data-consumer.md`, `cli-script-main-fires-on-import.md`, `no-traced-reader-region-is-not-proof-of-filler.md`, `naive-byte-window-address-scan-crosses-instruction-boundary.md`, `single-disassembler-src-dst-order-trusted-unverified.md`, `file-offsets-vs-segment-relative.md`, `duplicate-asset-trailing-bytes-may-be-executed-code-overlay.md`, `block-chain-walk-stops-at-unknown-sibling-block-magic.md`, `magic-search-must-not-be-wider-than-codes-real-comparison-width.md`, `carry-chain-opcode-census-locates-hand-written-bit-readers.md`, `relocated-base-plus-displacement-hides-call-target.md`
