# powermonger — Powermonger (Bullfrog; Amiga classic + WW1 edition, DOS VGA)

**Project root:** `~/Development/powermonger` · **Full history/evidence:** `game-re-corpora/details/powermonger.md` (read on demand) · **Open work:** `docs/powermonger/TODO.md`

## Games
- Powermonger, classic (Amiga) — `powermonger`/`amiga` — fully worked: disk, codecs, graphics, palette, terrain gen, entity/AI
- Powermonger: World War I Edition (Amiga) — `powermongerwwi`/`amiga` — same disk/compression confirmed; formats not individually re-verified (see `docs/powermonger/amiga/ww1-edition.md`)
- Powermonger (DOS VGA) — `powermonger`/`dosvga` — separate doc tree; Huffman `.HUF` compression, not the Amiga LZ — `docs/powermonger/dosvga/{data-structure,huf-format}.md`

## Solved formats → where documented
Format specs: `docs/powermonger/amiga/data-structure.md`; 68k findings: `docs/powermonger/amiga/runprog-code.md`.
- Bullfrog track-based disk filesystem (not AmigaDOS; 5632-byte tracks, `DIR\0`/`WAR\0` directory at track 1) — `src/assets/formats/disk.ts`
- Two custom backward-bitstream LZ codecs: A (MSB-first gamma, `INTRODAT` only), B (LSB-first-per-longword, XOR-zero checksum trailer, everything else incl. RUN_PROG self-depack) — `src/assets/formats/depack-b.ts`
- Full-screen pictures: raw headerless planar; 5 plane-major, CAPGRAPH word-interleaved — `src/assets/formats/screen.ts`
- OCS palette: 3 × 16-colour tables in a runtime work table in RUN_PROG (copper list built at runtime); screenshot-confirmed — `src/assets/formats/palette.ts`
- Sprite banks SPRITE8/16/24/32 = masked 4bpp (mask + 4 planes); TEXTURES = plain 4bpp row-interleaved; all use the active screen palette (A) — `src/assets/formats/sprite-bank.ts`
- `FX.PAK` 16-byte descriptor directory (structure confirmed; "raw signed-8-bit PCM" is hypothesis) — `docs/powermonger/amiga/audio-format.md`, `src/assets/formats/fx-pak.ts`
- `END.PAK` sparse cumulative delta-patch animation (7 frames) — `src/assets/formats/end-pak.ts`
- Runtime resource loader: 16-entry `{namePtr, loadAddr, length}` table + `LoadResource(index)`
- `MAPDATA` 332-byte records (identical on PC, per Viridian Games) + terrain generation: LCG, random walk + smoothing (`$F860`/`$FCCA`, **live-verified byte-exact** under Musashi), object placement `$B488` and marching-squares classifier `$F912` (disassembly-confirmed only) — `src/assets/formats/{mapdata,terrain-gen,terrain-objects,terrain-classify}.ts`
- Entity/AI (RAM-only): entity pool `$77B7A`, team records `$7754C`, ≥75-case task dispatch `$144A2`, real main loop `$1286C`, mouse/order UI chain — `docs/powermonger/amiga/entity-ai.md`, `src/assets/formats/entities.ts` (documentation-as-code)
- Not covered by the details file (newer docs, read directly): `docs/powermonger/amiga/weather-system.md`, `mopup-findings.md`

## Engine-family / cross-project links
- Viridian Games' PC-side MAPDATA write-up (viridiangames.com, 2008) independently matches the Amiga record layout byte-for-byte.
- `@seer-project/gfx` `decodePlanar` handled all three bitplane layouts with no format-specific code (`game-re-tooling/amiga.md`).

## Reusable code in this repo
- `tools/musashi-verify/` — bare vendored-Musashi 68000 golden-model harness: run RUN_PROG's real code against real data and diff vs the TS port
- `src/assets/formats/depack-b.ts` — Bullfrog LZ variant B

## Know before you start
- RUN_PROG addresses: file offset = runtime address − `$1400` (depacked image `build/cache/powermonger/amiga/RUN_PROG_depacked.bin`).
- `decodeSpriteBank` (TEXTURES) is a cross-platform contract with the DOS pipeline — don't change its behavior (`shared-decoder-behavior-is-a-cross-platform-contract.md`).
- Entity/AI state is RAM-only; nothing under `data/` holds it (`docs/architecture-overview.md` zone split).
- Find buffer-family accessors with a displacement census, not a literal-address grep; find UI code by censusing one UI-state global, not keyword search.
- `BITMAP.PAK`'s `LoadResource(7)` is real but unreachable (MAPDATA #195 is outside the 15×13 level-select grid).
- FX audio is staged verbatim + JSON sidecar (`public/assets/powermonger/amiga/data/fx.json`), decoded at runtime.

## Lessons sourced from this corpus
`single-image-in-uniform-corpus-uses-different-planar-layout.md`, `runtime-built-lookup-table-defeats-static-scan.md`, `narrow-width-masks-a-planar-layout-correction.md`, `shared-decoder-behavior-is-a-cross-platform-contract.md`, `cumulative-delta-frames-not-independent-overlays.md`, `self-modifying-code-parameter-passing.md`, `reverify-raw-opcode-before-porting-bitexact-algorithm.md`, `classifier-case-index-direction-unverified-against-handler-semantics.md`, `cpu-overflow-instruction-leaves-destination-unchanged-not-undefined.md`, `guarded-call-confirmed-called-but-precondition-unreachable.md`, `literal-address-census-misses-buffer-family-aliasing.md`, `ui-state-global-census-beats-keyword-search.md`
