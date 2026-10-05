# siren — Final Fantasy VII, VIII, IX (PSX)

**Project root:** `~/Development/siren` · **Full history/evidence:** `game-re-corpora/details/siren.md` (read on demand) · **Open work:** `docs/<game>/TODO.md` (`ff7`, `ff8`, `ff9`) — the authoritative per-item status surface

## Games
- Final Fantasy VII (PSX) — `ff7`/`psx` — AKAO v1 + global instrument bank; 16 summons inventoried, battle models exported
- Final Fantasy VIII (PSX) — `ff8`/`psx` — LZS/LZK, battle DAT models, 22 GF/summon inventories; MAG VM partly solved
- Final Fantasy IX (PSX) — `ff9`/`psx` — dir13 SFX archive, dir07 battle meshes/anims, 33 eidolon timelines

## Solved formats → where documented
- **AKAO** sequenced audio — FF8/FF9 "v3" (0x40 header, identical across both; 9,832 tracks 100%) vs FF7 "v1.0" (0x14 header; 17,672 tracks 100%) — corpus-confirmed — `docs/akao-format.md`, `tools/shared/akao*.ts`
- FF8/FF9 AKAO sample bank (PSX SPU ADPCM + instrument records) — `tools/shared/akao-sample-bank.ts`
- FF7 global instrument bank `SOUND/INSTR.DAT` + `INSTR.ALL` (93 records; 12-TET pitch table; `PROGCHANGE` → record index 24,487/24,487) — substantially decoded; local drum-table grammar and `INSTR2.ALL` range discrepancy open — `docs/akao-format.md`, `tools/shared/akao-sample-bank-v1.ts`
- FF9 dir13 special-effect archive (IMG Type-3; chunk table + 3-byte command stream at `0x400` + small-file table), ported from Memoria `SFXBinaryFile.cs` — `docs/ff9/psx/sfx-format.md`, `tools/ff9/sfx.ts`
- FF9 dir07 battle mesh (type 0x02) + pose (0x03), TIM/VRAM material baking — 182 GLBs, 2,729 clips; type-C polygons explicitly unsupported — `tools/ff9/{model,gltf,vram}.ts`
- Not covered by the details file (status unknown here, read directly): `docs/ff9/psx/{ff9-img-format,db-archive-format,dot1-archive-format,field-data,ev-script,disc-manifest}.md`
- FF8 LZS/LZK compression + battle DAT models; MAG `*.X` bone-motion VM core + opcodes 10-23 confirmed (~90 handlers open) — `docs/ff8/psx/{lzk-format,data-structure,summon-sequences}.md`, `tools/ff8/`
- FF7 summons (`partial` — runtime timing/camera/VFX need overlay emulation) and 353 ENEMY battle models (`resolved`) — `docs/ff7/psx/data-structure.md`, `tools/ff7/summon.ts`

## Engine-family / cross-project links
- AKAO is shared Square in-house format but NOT byte-compatible across games; FF7's v1 family matches VGMTrans's.
- Oracles: **Memoria** (decompiled FF9 PC-port C#, check out ad hoc e.g. `/tmp/siren-memoria`) — strong for file byte layout, but a clean-room reimplementation, not PSX control flow; archived **"Rɘverse FF9"** JS fan viewer (minified + pretty-printed snapshots) covers some formats Memoria hands to native code. Survey: `docs/prior-art-psx-ff.md`.

## Reusable code in this repo
- `tools/shared/summon-sequence.ts` — the cross-game `SummonSequence` schema (models, camera, effects, audio, per-field `completeness`)
- `tools/shared/akao*.ts` — AKAO v1/v3 sequence parsers, sample banks, `akao-render.ts` debug renderer (`renderAkaoV3Sequence`/`renderAkaoV1Sequence`)
- `tools/shared/psx.ts`, `gltf-audit.ts`

## Know before you start
- FF9 model-effect opcodes 0x80-0x87 cross a proven closed-native boundary (Memoria P/Invokes `FF9SpecialEffectPlugin`): 108/126 dispatches are opaque — classify referenced resources only by their own leading bytes (`"AKAO"`, `0x6f73` "so" static mesh → dir07 mesh reader).
- FF7 instrument loop-seed records are 1-2 ADPCM blocks — tile them or renders come out >99% silent.
- FF8/FF9 instrument/drumkit table work (`akao-instruments.ts`) was a separate, concurrent pass.
- TODO files, not this summary, are the status source of truth.

## Lessons sourced from this corpus
`aggregate-ratio-across-corpus-confirms-closed-form-constant.md`, `multi-occurrence-convergent-target-confirms-self-relative-pointer.md`, `sequencer-silent-despite-passing-per-sample-audio-check.md`, `native-plugin-dispatch-erases-resource-kind-signal.md`
