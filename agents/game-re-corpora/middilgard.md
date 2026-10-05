# middilgard — War in Middle Earth, Spirit/Vengeance of Excalibur, Conan, Warriors of Legend

**Project root:** `~/Development/middilgard` · **Full history/evidence:** `game-re-corpora/details/middilgard.md` (read on demand) · **Open work:** `docs/<game>/TODO.md` per game (`wime`, `spirit`, `vengeance`, `conan`, `legend`)

## Games
- War in Middle Earth (`wime`: Amiga, DOS VGA/EGA, IIGS, C64, CPC) — combat decoded + reimplemented; C64/CPC are separate 8-bit games, substantially cracked
- Spirit of Excalibur (`spirit`: Amiga, CDTV) — SCEN, combat, exploration, hero animation ranges decoded
- Vengeance of Excalibur (`vengeance`: Amiga, DOS VGA) — SCEN 100%, combat/exploration decoded; FSME VM encoding traced, pose naming open
- Conan the Cimmerian (`conan`: Amiga, DOS) — SCEN + palettes solved; 78/101 FRML animations hypothesis-only
- Warriors of Legend (`legend`: DOS VGA) — GAMI/LMRF/PAMM/NECS solved; `TAPM` still open

## Solved formats → where documented
- Mac-style **resource-fork** container, all games; endianness + byte-reversed FourCCs per platform (`IMAG`/`GAMI`, `FRML`/`LMRF`, `MMAP`/`PAMM`, `SCEN`/`NECS`) — `docs/formats/resource-fork.md`, `src/assets/formats/resource-fork.ts`
- `IMAG`/`FRML` (28/27/6-byte header variants; PackBits **or** LZSS, auto-detected) — `docs/formats/{imag,frml}.md`, `src/assets/formats/{imag,frml}.ts`
- `SCEN` scene object lists (Vengeance 4911/4911, Spirit 99.9%, Conan 6,542/6,542; per-game bitfield) — `docs/{spirit,vengeance,conan}/amiga/engine.md`, `src/assets/formats/scen.ts`
- Legend `NECS` (LZSS-compressed, 32-byte header + 32-byte records; 316 scenes render) — `docs/legend/dosvga/engine.md`, `src/assets/formats/legend-necs.ts`
- WIME `BScene`/`SynthSceneObjects` procedural generator (all 276 paths) — `docs/wime/amiga/bscene-format.md`
- FRML animation bytecode VMs: Spirit/Vengeance FSME (`(op:4<<12)|operand:12`), WIME per-race table (idle/walk/attack/death confirmed) — `docs/spirit/amiga/bytecode-vm.md`, `docs/wime/amiga/frml-colour-variants.md`, `docs/wime/dosvga/frml-extra-frames.md`
- Combat/exploration logic (WIME, Spirit, Vengeance) — `docs/<game>/amiga/{game-logic,battle-screen-presentation,exploration}.md`, `src/engine/BattleSystem.ts`
- SMUS/Sonix audio, sampled sound; Legend `XFSD` SFX (26/32) — `docs/formats/{smus,sampled-sound}.md`, `src/assets/formats/legend-xfsd.ts`
- WIME C64 (PORT/BLOCK multicolor bitmaps) and CPC (Laser Load map, serpentine tiles) — `docs/wime/{c64,cpc}/engine.md`
- Cross-platform exe data tables (Vengeance DOS `episode*.dat`, WIME DOS entity table 4,624/4,624) — `docs/wime/dosvga/exe-gameplay-data.md`, `docs/vengeance/amiga/gameplay-data.md`

## Engine-family / cross-project links
- Melbourne House / Synergistic engine, five games on one container — re-derive SCEN bitfield, id formula and header per game; expect a new variant, not the same constants.
- Conan's `Game`/`Conan` compressed DATA hunk = same custom backwards-LZ77 + 7-hunk shape as Black Crypt `bcdft` (`crawl` corpus); solved by running the exe's own CODE under musashi (`tools/conan/decompress-data-hunk/`).
- DOS ports are field-for-field x86 ports of Amiga code; Amiga data tables are byte-identical search oracles (swap 16-bit words for bytecode).

## Reusable code in this repo
- `src/assets/formats/resource-fork.ts`, `imag.ts`, `frml.ts`, `scen.ts` — shared container + image/anim decoders (fixed LE ref-list + size-prefix guard bugs)
- `src/assets/formats/exepack.ts` (`unexepack`/`isExepack`) — Microsoft EXEPACK unpacker
- LZEXE: `decompressLZEXE` from `@seer-project/pipeline` (was `tools/shared/lzexe.ts`)
- `tools/vengeance/fsme-vm.ts` — FSME VM reachability walker (candidate for Spirit reuse)
- `src/assets/formats/wime-frml-anim-vm.ts` (`traceWimeAnimRow`); `detectGeometricBoundaries` (`src/assets/formats/legend-frml-animations.ts`) geometry classifier, reused by Vengeance

## Know before you start
- SCEN entry longwords are byte-reversed on disk (fixed up in `_LoadScene`); `refId` is dispatched on a flags byte (`_aCharFlags`), not the id; SCEN ids are computed (`x*100+loc`).
- Executables ship `HUNK_SYMBOL` (~1,100 real C names) — resolve A4 `JSR`s via SAS/C jump-table stubs (`game-re-method/finding-the-reader.md`); displacements never transfer between `Excal` and `ExcalII`.
- FRML codec choice (PackBits vs LZSS) needs a structural tie-break (frame-0 bitplane depth), not a fixed preference.
- DOS exes are packed: Conan `START.EXE` LZEXE with crack-tampered `e_ip`/`e_cs`; WIME `START.EXE` EXEPACK (different file); Vengeance `game.exe`/`vex.exe` LZEXE 0.91; Legend `wofl.exe` in-file overlays stall static tracing.
- Format docs hold confirmed info only; every eliminated theory goes in `docs/reference/eliminated/` — check there before retrying.
- `www/` Astro site is a third rendering surface (`www/scripts/build.mjs`); multiple concurrent agent sessions commit to the same tree.

## Lessons sourced from this corpus
`partial-resolution-rate-is-noise.md`, `corpus-wide-render-reveals-trigger-scope-not-decode-bug.md`, `adjacent-ramp-table-masks-off-by-one-record-start.md`, `emulator-harness-input-boundary-not-algorithm.md`, `next-record-preview-defeats-stride-detection.md`, `optional-per-record-compression.md`, `tile-grid-dimension-needs-render-not-just-bytecount.md`, `canned-save-state-mirrors-exe-struct.md`, `text-field-periodic-interleave-byte.md`, `undecoded-format-may-be-compressed-with-known-codec.md`, `published-walkthrough-numeric-oracle.md`, `sprite-frame-geometry-reveals-animation-segments.md`, `port-reverses-whole-header-word-not-per-field.md`, `byte-value-collision-defeats-marker-only-guard.md`, `cross-platform-string-delta-reveals-stride-vs-offset.md`, `pre-decompression-guard-uses-decompressed-threshold.md`, `vm-bytecode-embeds-platform-addresses.md`, `traced-calling-convention-unverified-against-corpus.md`, `adjacent-subfield-roles-swapped-despite-correct-bit-boundaries.md`, `addresses-landing-in-reserved-region-means-wrong-boundary-model.md`, `boring-resolved-call-can-be-a-real-noop.md`, `packed-exe-mimics-variable-length-records.md`, `cross-platform-decode-oracles.md`, `bytecode-trace-in-range-result-can-still-be-noise.md`, `constant-valued-field-poisons-shared-wellformedness-gate.md`, `extracted-file-sizes-all-multiples-of-block-payload.md`, `palette-storage-quirks.md`, `serpentine-row-order-mimics-mirrored-rows.md`, `shared-prefixes-at-guessed-stride-fake-animation-frames.md`, `header-shape-ambiguous-pixel-encoding.md`, `byte-scan-tag-byte-vs-wrong-stride.md`, `bitfield-spans-multiple-addressable-bytes.md`, `negative-from-addressing-root-not-shapes.md`, `seeded-prng-stable-not-random.md`, `runtime-only-value-often-static.md`, `audio-byte-order-measurable.md`, `bitfield-residue-unread-past-cited-trace-window.md`, `rle-decode-succeeds-on-garbage.md`, `emulator-harness-pc-range-completion-defeated.md`, `hand-computed-test-fixture-vs-real-run.md`, `producer-fix-inert-without-consumer-audit.md`, `multiple-rendering-surfaces-same-data.md`, `bare-git-commit-sweeps-concurrent-stage.md`
