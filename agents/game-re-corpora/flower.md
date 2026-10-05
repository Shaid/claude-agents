# flower — Drakengard 1/2/3, NieR (PS3/X360/PC), NieR:Automata, MGR:R, Chaos Legion, DMC, ZOE2

**Project root:** `~/Development/flower` · **Full history/evidence:** `game-re-corpora/details/flower.md` (read on demand) · **Open work:** `docs/<game>/TODO.md` per game (ZOE2: `docs/zoe2anubis/{ps2,ps3}/TODO.md`)

## Games
- Drakengard / Drakengard 2 (PS2, Cavia) — `drakengard`,`drakengard2`/`ps2` — all major formats decoded, shipped (3,380 / 528 models)
- Drakengard 3 (PS3, UE3 `SQEX03GAME`, Access Games) — `drakengard3`/`ps3` — base+DLC textures/meshes/anim/audio shipped; scenes 5/1,898 levels
- NieR 2010 (PS3 + X360, Cavia) — `nier`/`ps3`,`x360` — audio + 304 meshes (260 textured); X360 FMV (video-only)
- NieR Replicant 1.22 (PC, Toylogic) — `nier`/`pc` — textures, video, Wwise audio shipped; `.rmesh`/motion open
- NieR:Automata, MGR:Revengeance (PC, PlatinumGames) — `nierautomata`,`metalgearrising`/`pc` — textures/mesh/audio/video shipped
- Chaos Legion, Devil May Cry (PS2, Capcom) — `chaoslegion`,`devilmaycry`/`ps2` — registered; TIM2/FMV/audio/models partly
- ZOE2 / Anubis (PS2 + PS3 HD, Konami) — `zoe2anubis`/`ps2`,`ps3` — cipher, audio, textures, models solved
- Transformers: Devastation (PS3, Platinum) — `transformersdevastation`/`ps3` — in repo, not in corpus history; see its doc
- Dragon's Crown (PS3+PS4) — not started; `ps3-pkg.ts` should apply

## Solved formats → where documented
- Cavia `fpk`/`dpk` recursive container — confirmed (dpk hash untraced) — `docs/drakengard-cavia-archive-format.md`
- DG1/DG2 `\0V3a` (LZO1X blocks), `wZIM` (GS packets), `CSFg` + DG2 `VU1`, `CJFg`/`CJFd`, `CMFf`/`CMFd` (2nd track unconfirmed), materials, cavia-stream PS-ADPCM — confirmed — `docs/drakengard{,2}/ps2/data-structure.md` (§10 glTF bugs)
- DG3 — `docs/drakengard3/ps3/data-structure.md`: PKG/EDAT (DLC only), seekfree formats A/B §27, umodel §8, mesh §10, `.psa` anim §13, SCD §14, UnrealScript via UELib 99.9% §24, materials/placements §27-28, char dedup §18-19, DLC §23
- NieR PS3 — `docs/nier/ps3/data-structure.md`: `.SDAT` (no RAP), CRI CPK/CRILAYLA/AAX, `.MDP` = plain LZO1X, `HEAP` geometry, `TX2D` headerless BC1/3, `KPKy`/`MESH`/`NODT`; FMV negative §10
- NieR X360 `docs/nier/x360/data-structure.md` (XDVDFS, MPEG-2 `.sfd`, AIX); PC `docs/nier/pc/data-structure.md` (zstd `PACK`/`BXON`, FNV-1, `MARC` ASF, Wwise `AKPK`)
- NieR:A `docs/nierautomata/pc/data-structure.md` (`DAT\0`, WTB+DDS §16, WMB3 §18); MGR `docs/metalgearrising/pc/data-structure.md` (WMB4, WTB rev, USM+ADX, `HIRC`, debug cue-sheet names)
- Chaos Legion `docs/chaoslegion/ps2/data-structure.md` (TIM2/CLT2 §12, `LEGION.DAT/IDX`, hidden FMV + SShd PCM §9, models §13); DMC `docs/devilmaycry/ps2/data-structure.md` (`.XAG` §6, `.PSS` §9)
- ZOE2 `docs/zoe2anubis/{ps2,ps3}/data-structure.md`: STAGE cipher, VOX, `.tex`, `.mdz` (§4.10 correction), HVSTEX

## Engine-family / cross-project links
- PS2 Cavia ≠ DG3 (UE3, Access) ≠ NieR PS3 (third family); only link: `\0V3a`'s LZO1X reused for `.MDP`. "Last-byte variant" magics recur (`wZIMd`, `CJFd`, `CMFd`; `KPKy` vs Replicant `KPK\x7f` — unconfirmed lead)
- CRI CPK stack transfers unmodified across NieR PS3/X360, NieR:A, MGR (same `TocOffset>=0x800` base rule)
- Platinum WMB3→WMB4 is a restructure (Bayonetta family; `Kerilk/bayonetta_tools`, NieR2Blender refs); `BXM\0` from transformersdevastation
- `SShd`/`SSbd` stream framing shared by Cavia and Capcom PS2 titles; ZOE2 = MGS2 family (`kellymoen/MGDecrypt` buggy for ZOE2)
- Oracles: vgmstream, umodel, UELib, `neptuwunium/kaine`, Rainbow (TIM2), RPCS3 `unedat.cpp`. Recomp: `~/Development/seer/docs/{ps3-recomp,engine-based-porting,ps4-recomp}.md`

## Reusable code in this repo
- `tools/shared/`: `cavia-*.ts`; `ps3-pkg.ts`, `ps3-edat.ts` (EDAT+SDAT); `cri-cpk.ts`, `crilayla.ts`, `cri-aax.ts`, `xdvdfs.ts`, `dds.ts`, `tim2.ts`, `scd.ts`; UE3 `umodel.ts`, `psa*.ts`, `ue3-transform.ts`; `nier-*.ts`, `nierautomata-*.ts`, `mgr-*.ts`
- `tools/drakengard3/uelib-driver/` (patched vendored UELib); `tools/zoe2anubis/vudis.py` (PS2 VU disassembler)

## Know before you start
- DG3: work from disc dump `data/drakengard3/ps3disc/` (plaintext); umodel can't export anim or decompile bytecode
- glTF validator-clean ≠ correct: live-render every exporter (DG §10); walk real directories, not magic scans (DG2 skeletons are `CJFd`)
- NieR PS3: DLC01 RAP-blocked; per-part material binding exhausted (data paths + RSX shader route negative); don't rerun FMV search
- PS2: check raw-LBA gaps between catalogued files; detect PCM byte order per clip; ffprobe misses custom PES audio
- ZOE2: capstone/r2 misdecode R5900 3-op `mult`; PCSX2 savestates in `data/zoe2anubis/`; PS3 `STAGE.DAT` == PS2

## Lessons sourced from this corpus
`all-zero-stub-file-inflates-failure-count.md`, `asset-name-string-mining-beats-empty-localization-table.md`, `batched-resume-reprobe-cost-linear-in-corpus-size.md`, `blocking-execfilesync-defeats-promise-all-pool.md`, `byte-exact-adpcm-needs-exact-integer-sequence.md`, `byte-identical-cross-platform-archive-does-not-bypass-sibling-puzzle.md`, `byte-shape-classifier-needs-entropy-gate.md`, `catalogued-file-scan-misses-raw-lba-gap.md`, `chunk-tag-name-mimics-unrelated-format.md`, `container-declared-size-may-be-stale-not-decoder-bug.md`, `content-addressed-manifest-merge-needs-source-precedence.md`, `content-signature-source-must-predate-pipeline-mutation.md`, `content-type-absence-needs-multiple-independent-angles.md`, `declared-range-field-loose-for-bulk-records.md`, `deepest-qualifying-gap-not-largest-gap.md`, `embedded-known-name-fragments-signal-compressed-sibling-content.md`, `file-linked-local-package-needs-build-before-dev-server.md`, `fixed-stride-record-count-unverified.md`, `format-field-width-unexercised-by-first-corpus.md`, `generic-bucket-hides-real-content.md`, `generic-demuxer-misses-custom-pes-audio.md`, `iso9660-tree-near-empty-check-raw-lba-toc.md`, `legacy-32bit-binary-missing-shared-lib.md`, `lzo-style-decode-start-offset-independence-refutes-stream.md`, `manifest-scale-needs-lazy-category-load-plus-virtualization.md`, `model-silhouette-render-confirmed-by-placement-layer.md`, `multiformat-cli-silent-extension-fallback.md`, `named-field-base-offset-mimics-second-crypto-layer.md`, `offset-field-collision-with-confirmed-sibling-reveals-wrong-pool.md`, `per-instance-file-set-may-be-duplicate-blobs.md`, `ps2-inhouse-texture-embeds-gs-register-packets.md`, `redundant-transmission-needs-correlation-not-diff.md`, `reference-tool-field-never-consumed-by-its-own-importer.md`, `romhacking-community-tools-first.md`, `script-corpus-defaultproperties-reference-chain.md`, `script-files-may-be-native-code-bound-to-fixed-memory-map.md`, `self-relative-offset-needs-cpp-arithmetic-not-prose.md`, `shallow-magic-scan-undercounts-sibling-magic-corpus.md`, `shared-parser-column-picker-scoped-to-first-consumer.md`, `shipped-disc-leftover-vcs-tree-plaintext-oracle.md`, `sibling-format-encoding-paradigm-not-transitive.md`, `sibling-magic-may-be-same-struct-zeroed-field.md`, `sibling-text-files-mixed-encoding-silent-zero-match.md`, `single-outlier-defeats-bbox-camera-fit.md`, `single-working-consumer-hides-second-container-subformat.md`, `slugified-name-collision-overwrites-output.md`, `standard-codec-delegate-to-trusted-decoder-not-hand-reimplementation.md`, `stride-grouping-false-merges-in-dense-marker-regions.md`, `subprocess-export-leaves-truncated-output-file.md`, `texture-manifest-entry-needs-atlas-sidecar.md`, `unconstrained-nav-element-starves-flex-scrollable-list.md`, `vendored-parser-hang-needs-committed-source-patch.md`, `vertex-normals-as-winding-topology-oracle.md`, `vite-dev-server-stale-public-dir-listing.md`, `wildcard-batch-tool-aborts-on-first-bad-file.md`, `wwise-prefetch-fragment-vs-complete-embedded-audio.md`
