# flower — Drakengard 1/2/3, NieR (PS3/X360/PC), NieR:Automata, MGR:R, Chaos Legion, DMC, ZOE2, Transformers: Devastation

**Project root:** `~/Development/flower` · **Full history/evidence:** `game-re-corpora/details/flower.md` (read on demand) · **Open work:** `docs/<game>/TODO.md` per game (ZOE2: `docs/zoe2anubis/{ps2,ps3}/TODO.md`) · **Last audit:** `docs/<game>/audit-2026-11-18{,-changes}.md`

## Games
- Drakengard / Drakengard 2 (PS2, Cavia) — `drakengard`,`drakengard2`/`ps2` — all major formats decoded and shipped; shipped counts include path aliasing (dedupe open: `cavia-pipeline-content-dedupe`)
- Drakengard 3 (PS3, UE3 `SQEX03GAME`, Access Games) — `drakengard3`/`ps3` — base+DLC textures/meshes/anim/audio shipped; **`data/drakengard3/ps3disc/` is an HDD install cache, not a disc dump** — all counts are lower bounds (`dod3-base-corpus-incomplete`)
- NieR 2010 (PS3 + X360, Cavia) — `nier`/`ps3`,`x360` — audio + meshes; X360 FMV (video-only); PS3 FMV blocked on the JP disc key
- NieR Replicant 1.22 (PC, Toylogic) — `nier`/`pc` — textures, video, Wwise audio shipped; `.rmesh`/motion open; PC claims unaudited
- NieR:Automata, MGR:Revengeance (PC, PlatinumGames) — `nierautomata`,`metalgearrising`/`pc` — textures/mesh/audio/video shipped; texture walker ships only the first DDS per bundle (open)
- Chaos Legion, Devil May Cry (PS2, Capcom) — `chaoslegion`,`devilmaycry`/`ps2` — TIM2/FMV/audio/models partly; DMC T32 pixel format open
- ZOE2 / Anubis (PS2 + PS3 HD, Konami) — `zoe2anubis`/`ps2`,`ps3` — cipher, audio, textures, models solved; `DEMO.DAT`/`MOVIE.DAT` internals open
- Transformers: Devastation (PS3, Platinum) — `transformersdevastation`/`ps3` — manifests shipped; real-corpus output unverified (encrypted ISO)
- Dragon's Crown (PS3+PS4) — not started; `ps3-pkg.ts` should apply

## Solved formats → where documented
- Cavia `fpk`/`dpk` recursive container — confirmed: fpk magic is a 24-bit check, `data_start = align_up(0x80+[0x18], align)`; dpk slots = `([0x0c]−0x20)/32`, entry hash = `md5(lowercase path)` — `docs/drakengard-cavia-archive-format.md`
- DG1/DG2 `\0V3a` (LZO1X blocks; 131,072 or 262,144), `wZIM` (GS packets), `CSFg` + DG2 `VU1`, `CJFg`/`CJFd`, `CMFf`/`CMFd` (region-A non-unit tracks skipped; semantics open), cavia-stream PS-ADPCM — `docs/drakengard{,2}/ps2/data-structure.md`
- DG3 — `docs/drakengard3/ps3/data-structure.md`: PKG/EDAT (DLC), seekfree formats A/B §27 (format-B names start at byte 0 of chunk 0), umodel §8, mesh §10, `.psa` §13, SCD §14, UnrealScript via UELib §24, materials/placements §27-28
- NieR PS3 — `docs/nier/ps3/data-structure.md`: `.SDAT`, CRI CPK/CRILAYLA/AAX, `.MDP` = LZO1X, `HEAP` geometry (header table §8.1.1.5 corrected), **`TX2D` carries an in-band `CellGcmTexture` descriptor** at `heapStart+HEAP[0x10]+descOffset` (DXT1/DXT5/A8R8G8B8; TV search is fallback only) §8.1.1.8
- NieR X360 `docs/nier/x360/data-structure.md` (XDVDFS, MPEG-2 `.sfd`, AIX); PC `docs/nier/pc/data-structure.md` (zstd `PACK`/`BXON`, FNV-1, `MARC` ASF, Wwise `AKPK`)
- NieR:A `docs/nierautomata/pc/data-structure.md` (`DAT\0` + hash map, WTA offsets → whole DDS files §15, WMB3 §18, `XML\0` = BXM); MGR `docs/metalgearrising/pc/data-structure.md` (WMB4, WTB, USM+ADX, BGM banks inside `ui_movie_bnk.dat`)
- Chaos Legion `docs/chaoslegion/ps2/data-structure.md`: TIM2/CLT2 §12, `LEGION.DAT/IDX`, FMV + SShd PCM (two audio tracks) §9, sound-driver `CAPSDRVD.IRX` `{u32 lba,u32 size}` whole-disc table at file 0xb290 (tiles 206/220) §9.3, leader bank = PS-ADPCM §9.2; DMC `docs/devilmaycry/ps2/data-structure.md` (`.XAG` §6, `.PSS` audio big-endian §9, wrapper aux records = sound banks)
- ZOE2 `docs/zoe2anubis/{ps2,ps3}/data-structure.md`: STAGE cipher, VOX, `.tex`, `.mdz`, HVSTEX; extension hash is many-to-one

## Engine-family / cross-project links
- PS2 Cavia ≠ DG3 (UE3) ≠ NieR PS3 (third family); only link: `\0V3a`'s LZO1X reused for `.MDP` (131,072-byte pages in both). "Last-byte variant" magics recur (`wZIMd`, `CJFd`, `CMFd`)
- CRI CPK stack transfers unmodified across NieR PS3/X360, NieR:A, MGR (`FileOffset` relative to `TocOffset`)
- Platinum WMB3→WMB4 is a restructure (Bayonetta family); `.mot` already decoded in `transformersdevastation` and `~/Development/legion` (LE) — port, don't re-derive; `BXM\0` decoder in `transformersdevastation`
- Capcom PS2 sound drivers (CL `CAPSDRVD.IRX`, DMC `TSNDDRVM.IRX`) share the `{lba,size}` table order; `SShd`/`SSbd` framing shared by Cavia and Capcom; ZOE2 = MGS2 family
- Oracles: vgmstream, umodel, UELib, `neptuwunium/kaine`, Rainbow (TIM2), RPCS3 `unedat.cpp`; Chaos Legion PC release (`MOVIE/*.mpg`, needs `unshield`) as a name/audio oracle; ZOE1 names for ZOE2 hashes (lead)

## Reusable code in this repo
- `tools/shared/`: `cavia-*.ts`; `ps3-pkg.ts`, `ps3-edat.ts`; `cri-cpk.ts`, `crilayla.ts`, `cri-aax.ts`, `xdvdfs.ts`, `dds.ts`, `tim2.ts`, `scd.ts`; UE3 `umodel.ts`, `psa*.ts`, `ue3-transform.ts`; `nier-*.ts` (incl. `nier-tx2d.ts` descriptor reader), `nierautomata-*.ts`, `mgr-*.ts`
- `tools/drakengard3/uelib-driver/` (patched UELib); `tools/zoe2anubis/vudis.py` (PS2 VU disassembler)

## Know before you start
- DG3: `ps3disc/` is an install cache (PARAM.SFO "INSTALL DATA"); get a real disc image or the PSN PKG before trusting whole-corpus counts or negatives
- glTF validator-clean ≠ correct: live-render every exporter; walk real directories, not magic scans (DG2 skeletons are `CJFd`)
- PS2: tile directory tables against the disc (sector-contiguity + shuffled null) before trusting per-entry sizes; check raw-LBA gaps and the disc tail (CL has a 28.6 MB AIFF there); detect PCM byte order per clip
- NieR PS3: cached BG `.MDP` files are truncated; DLC01 RAP-blocked; per-part material binding exhausted
- ZOE2: capstone/r2 misdecode R5900 3-op `mult`; PCSX2 savestates in `data/zoe2anubis/`; PS3 `STAGE.DAT` == PS2
- NieR:A / TD game data may be unmounted (dangling symlinks): mark figures "on trust" rather than re-deriving

## Key lessons
- `shallow-magic-scan-undercounts-sibling-magic-corpus.md` — walk directories: DG2 skeletons are `CJFd`
- `sibling-magic-may-be-same-struct-zeroed-field.md` — "last-byte variant" magics recur
- `catalogued-file-scan-misses-raw-lba-gap.md` — PS2 discs hide data between and after catalogued files
- `audio-byte-order-measurable.md` — per-clip byte order; wrong order = RMS ≈ 18,900, lag-1 ≈ 0 (DMC `.PSS`)
- `header-shape-ambiguous-pixel-encoding.md` — NieR TX2D: TV search 0/8 on "unique" picks; read the in-band descriptor
- `fixed-stride-record-count-unverified.md` — dpk "data start" field → phantom slot
- `check-that-cannot-fail-is-not-evidence.md` — fpk "467/467" measured only on nested containers
- `standard-codec-delegate-to-trusted-decoder-not-hand-reimplementation.md` — CRI/Wwise/ADX/LZO: delegate
- `lzo-style-decode-start-offset-independence-refutes-stream.md` — LZO1X decodes "succeed" at wrong offsets
- `offset-size-table-read-half-record-off-pairs-neighbours.md` — Chaos Legion `CAPSDRVD.IRX` `{lba,size}` read half a record off

Full list: `details/flower.md` § "Lessons sourced from this corpus (full list)".
