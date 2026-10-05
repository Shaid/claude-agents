# parasiteeve — Parasite Eve, Parasite Eve II (PSX), The 3rd Birthday (PSP)

**Project root:** `~/Development/parasite` (corpus name ≠ dir name) · **Full history/evidence:** `game-re-corpora/details/parasiteeve.md` (read on demand) · **Open work:** `docs/<game>/TODO.md` per game

## Games
- Parasite Eve (PSX, SLUS-00662) — game-id `parasiteeve`/`psx` — TIM/FMV/AKAO, 830 models, anims, 509 backgrounds shipped
- Parasite Eve II (PSX, disc1 `SLUS_010.42`, disc2 `SLUS_010.55`) — game-id `parasiteeve2`/`psx` — container/LZSS/TMD/audio/MDEC/FMV shipped; 6 animated actors
- The 3rd Birthday (PSP, 2011) — game-id `the3rdbirthday`/`psp` — container, media, 231 pack models + 6,488 textures shipped; bones open

## Solved formats → where documented
- PE1 `PE.IMG` flat container; actor-package table at `SLUS_006.62+0x83b78` (438 slots, 3 chunks each; zero-deviation chain) — `docs/parasiteeve/psx/data-structure.md`
- PE1 actor chunk container (header + 12 packed slots), confirmed. Chunk1/2 = VRAM pages via slot-9 20-byte upload descriptors (8,217/8,217)
- PE1 chunk3 models: 830/830 textured glTF. Bone-local vertices, real bind pose for 721, `AnimationClip`s for 715. Animation clips (slot 3) cover 9,042/9,042 clips. The hierarchy stack program (`-1` push/`-2` pop/row N) is verified 15,641/15,641. Y-down→Y-up conjugation `R'=F·R·F` is applied at export only
- PE1 backgrounds = runtime tile-scatter from chunk3 slot 6 "scene blob" sampling chunk1 VRAM x=768/832. 509 PNGs/414 packages, grouped by the trigger `+0x24` camera discriminator; unsigned deltas
- PE1 audio: chunk3 slot 8 = cue → `AKAO` (sector table `+0x83980`); 53/53 AKAO collections, 47 audible (vgmtrans SMF-channel ceiling); FMV — `docs/parasiteeve/psx/fmv-audio.md`
- PE2 `STAGE0.HED`/`STAGEn.CDF` chunk container, `.pe2pkg` LZSS (448/448 byte-exact), TMD geometry + per-primitive tpage/clut textures (568/598), `.spk`/`hSPK` SPU-ADPCM (0 diffs) + `hONE` SndScript grammar, MDEC "BS v2" stills (pixel-exact), `INTER*.STR` (same container as PE1), TMD skeletal anim (`GpPackedSvec` 11/10/11, `RotMatrix_gte`) — `docs/parasiteeve2/psx/data-structure.md`
- 3rd Birthday `3rd.fsd`/`3rd.pkg` (2048-byte segments, sentinel-terminated), PSMF (muxed MP4), SEDBSSCF→RIFF ATRAC3+ (229/244), `pack` = verbatim PSP GE vertex arrays (231/436), T4/T8 swizzled textures, `extraWords` = bone-matrix-register delta list — `docs/the3rdbirthday/psp/data-structure.md`

## Engine-family / cross-project links
- PE1, PE2 and 3rd Birthday are three unrelated codebases. PE1/PE2 share only the PSY-Q SDK. PE2 has no AKAO audio. Do not assume PE1/PE2 format compatibility unless independently verified
- PE2 oracle: `GabeRealB/parasite-eve-2-decomp` (matching decomp + `tools/peassets/` Python). Its docs lag its own source (`sndscript.c` is decompiled), so re-clone fresh
- 3rd Birthday container: XeNTaX thread t=5616 prose. PSP ATRAC3+ PES-walk ported verbatim from `~/Development/valkyrie` (`tools/shared/psp-atrac3p-audio.ts`); upstream candidate `tfb-upstream-atrac3p`
- PE1's `psx-actor-vram.ts` GPU helpers are reused unchanged by PE2 (generic tpage/clut)

## Reusable code in this repo
- `tools/shared/psx-actor-vram.ts` — generic PSX VRAM/tpage/CLUT sampling
- `tools/shared/psx-actor-model{,-gltf}.ts`, `psx-actor-animation.ts`, `psx-actor-pose.ts` (heuristic fallback), `psx-tile-scene.ts`, `psx-actor-chunk.ts`
- `tools/shared/psx-mdec-bs.ts` — the account's first PSX MDEC BS decoder
- `tools/shared/psx-pe2-lzss.ts`, `ps-adpcm.ts`, `ffmpeg.ts` (`muxVideoAudio`)
- `tools/shared/psp-ge-vertex.ts` — generic `pspgu.h` vertex-type→layout decoder; `psp-atrac3p-audio.ts`
- STR/XA movie classification now lives upstream in `@seer-project/playstation` (`classifySubheaderStream`, `wrapAsCdxa`)

## Know before you start
- Skinned-model work: numeric oracles (FK distance-preservation, mirror-pair cosine, byte-exact consumption) miss track-index and whole-body defects. Always do real Playwright renders and never trust a claimed visual check. See `length-invariant-blind-to-track-index-misalignment.md`, `statistical-proxy-blind-to-whole-body-visual-defect.md`, `verify-escalation-artifacts-not-just-claims.md`
- PE1 clip tracks: the `+1` placeholder track is LEADING, so bone `i` uses track `i+1`. Model row 0 at `model+0x1c` is a real animated node
- Disc-I/O and code-construction censuses gave false negatives on chunk1 and backgrounds. Data can be pre-packed or already resident (`disc-io-census-blind-to-already-loaded-data-consumer.md`, `data-table-stores-prepacked-value-code-census-misses-it.md`)
- PE1 "bust card" bank A (x=704, ~205 identical models) has no per-model texture to recover; its 20-byte format is still undecoded. Blank-CLUT rooms (`actor346/359/381/430/428`) are genuine data, not a bug
- 3rd Birthday: `pixelFormat` is a bit-depth tag (4/8), not a `GU_PSM_*` enum. Gate both geometry and texture-table reads on `hasConfirmedGeometryLayout`. `eboot.bin` is KIRK-encrypted, so the bone-matrix search is blocked
- PE2: on Python→JS ports watch `//` (`python-floor-division-port-to-js-silent-fraction.md`). Movie segmentation is heuristic

## Lessons sourced from this corpus
`validation-sentinel-scoped-to-sub-region-not-whole-array.md`, `quad-uv-array-winding-differs-from-index-array-winding.md`, `one-based-first-index-sum-is-total-minus-one.md`, `canonical-local-rest-frame-tests-rotation-necessity.md`, `golden-angle-sibling-fan-avoids-axis-collision.md`, `genuine-off-by-one-loop-matches-placeholder-record-convention.md`, `fk-distance-preservation-verifies-rotation-decode.md`, `verify-escalation-artifacts-not-just-claims.md`, `length-invariant-blind-to-track-index-misalignment.md`, `statistical-proxy-blind-to-whole-body-visual-defect.md`, `disc-io-census-blind-to-already-loaded-data-consumer.md`, `data-table-stores-prepacked-value-code-census-misses-it.md`, `domain-refuted-by-shape-not-values.md`, `corpus-wide-zero-minimum-plus-contiguous-row-confirms-unsigned-field.md`, `active-flag-plus-runtime-discriminator-means-mutually-exclusive-not-combined.md`, `always-full-run-manifest-merge-accumulates-stale-entries.md`, `opaque-fill-for-unpainted-region-is-a-false-visual-claim.md`, `declared-record-count-is-allocated-capacity-trailing-zero-run-is-padding.md`, `model-signature-field-mistaken-for-magic-constant.md`, `format-doc-prose-may-describe-converted-value-not-raw-field.md`, `tracker-prose-is-not-evidence.md`, `python-floor-division-port-to-js-silent-fraction.md`, `confirmed-generic-mechanism-may-not-apply-to-this-instance.md`, `reference-project-doc-claims-stale-vs-own-current-source.md`, `terminator-scan-must-be-record-aligned.md`, `file-named-dummy-may-hold-real-leftover-content.md`, `stock-sdk-routine-official-docs-outrank-disassembly.md`, `bind-pose-render-blind-to-joints-index-space-bug.md`, `small-sample-probe-undercounts-dominant-subformat.md`, `pixel-format-value-guessed-from-enum-not-confirmed.md`, `discriminant-gated-field-convention-applied-unconditionally.md`, `hardware-register-persistence-explains-sparse-delta-metadata.md`
