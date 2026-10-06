# chimera — FE Three Houses, FE Warriors, FE Warriors: Three Hopes, FE Engage (Switch)

**Project root:** `~/Development/chimera` · **Full history/evidence:** `game-re-corpora/details/chimera.md` (read on demand) · **Open work:** one `docs/TODO.md`

Docs are flat `docs/<game>.md` (+ `fe3h-modding.md`, `few-modding.md`, `model-import-pipeline.md`, `docs/kt-warriors-engine-survey.md`). Ids: `src/game-id.ts`. Decoders: `src/data/formats/`.

## Games
- FE: Three Houses — `fe-threehouses` — tex/mesh+cloth/anim/audio/gamedata/save/DLC outfits solved
- FE Warriors (2017) — `fe-warriors` — tex/mesh/G2A/audio, stage nav, scenario scripts, combat math solved
- FE Warriors: Three Hopes — `few-threehopes` — RDB/KTID/KOD, tex/mesh/audio/text/anim solved; gamedata partial
- FE: Engage — `fe-engage` — Unity; tex/mesh/MSBT (EN only)/AnimationClip (bounded run) solved
- Astral Chain — split out to `~/Development/legion` (commit `1161f18`); details entries historical
- `touken-ranbu-warriors` — registered, `docs/touken-ranbu-warriors.md`; not in details file

## Solved formats → where documented
- G1T/G1M/G2A shared by all 3 KT titles (`g1t.ts`, `g1m*.ts`, `g2a*.ts`): `MM1G` IBM-palette skinning, NUN cloth bake, joint idx = slot×3; G2A `0300`/`0400`/`0500` need two flags; G1A v`2400` Three Hopes only (`g1a.ts`) — confirmed — `docs/fe-threehouses.md`
- Audio: KTSR Opus `codecID=9` (`ktsr.ts`, `ogg-opus.ts`); bare-KTSS DSP-ADPCM `codecID=2` FE Warriors (`gc-adpcm.ts`); `ktgcadpcm.ts`; `asrs-ktsr.ts`
- FE3H: `data0.ts` (KT_GZ), `gamedata-container.ts` + 10 tables, `asset-id-table.ts`, `class-palette.ts`, `fe3h-save.ts`, DLC outfits, `.kldm` level geometry — `docs/fe-threehouses.md`, `docs/fe3h-modding.md`
- FE Warriors: exe resource-path registry (`nso.ts`, `kt-resource-registry.ts`), `stage-*.ts`, `battle-scenario.ts`, `xl-table.ts`, `fixed-record-table.ts` — `docs/fe-warriors.md`
- Three Hopes: `linkdata.ts`, KTGL RDB (`kt-rdb.ts`, byte-exact), `ktid.ts`, `kt-kod.ts`, `linkdata-g1x.ts` — `docs/few-threehopes.md`
- Engage: UnityPy `tools/fe-engage/*.py`, `unity-mesh-gltf.ts`, `unity-animation-clip.ts`, `msbt.ts` — `docs/fe-engage.md`
- glTF→KT import (`gltf-g1m*.ts`, `gltf-g2a.ts`, `*-pack-lint.ts`) — offline-verified only — `docs/model-import-pipeline.md`

## Engine-family / cross-project links
- KT trio: shared codecs, **different containers**; check audio `codecID` first. RDB/KTID/KOD are KTGL-wide (Nioh, Dynasty Warriors, Atelier).
- Exe as ID→name oracle: FE Warriors data array vs Three Hopes registration code (`game-re-method/name-hash-recovery.md`).
- Wwise → `tools/.bin/vgmstream-cli`; MSBT = Nintendo LibMessageStudio (`pymsb`). Oracles: 010-binary-templates/Progenitor, `Joschuka/fmt_g1m`, ThreeCopes templates, koeipy, vgmstream source.

## Reusable code in this repo
- `tools/extract-romfs.ts` (hactool; `game-re-tooling/switch.md`), `tools/shared/kt-rdb-source.ts`, `build/cache/scratch/fe3h-cap-audit/a64.ts` (pure-TS ARM64 xref census)

## Know before you start
- Run `hactool --listromfs` file count vs the extracted tree **first** — extraction silently dropped dirs (FE3H, FE Warriors); ExeFS never backfilled.
- Always `--game <id>` on `npm run extract-data`. Shared machine, tight RAM/disk: fd-based reads, no whole-file `readFileSync`.
- Bind-pose renders/validators prove nothing about skinning; shared `g1m*`/`g2a*` edits hit all 3 corpora (regen rows open).
- Magic scans miss compressed members (Three Hopes 54.5% zlib) — use the RDB directory.
- Community names mislead ("G1A" is G2A, `.bin.gz` isn't gzip); fan templates may describe the newer patch build.
- Settled negatives: FE3H native cloth physics (dead code), Three Hopes model/anim names. Details say FE Warriors SFX undecoded; `docs/fe-warriors.md` now says shipped.

## Key lessons
- `bind-pose-render-blind-to-joints-index-space-bug.md` — bind-pose renders/validators passed while skinning was wrong
- `shared-decoder-behavior-is-a-cross-platform-contract.md` — shared `g1m*`/`g2a*` edits change all three KT corpora
- `compressed-container-members-invisible-to-magic-scan.md` — magic scans missed 54.5% zlib members in Three Hopes
- `community-format-name-mismatches-real-magic.md` — fan names mislead: "G1A" is G2A, `.bin.gz` isn't gzip
- `update-patch-ships-a-revised-struct.md` — fan templates may describe the patched build, not base
- `doc-self-cross-reference-before-fresh-disassembly.md` — details and docs disagree on status (FE Warriors SFX)
- `engine-family-shared-decoder-not-shared-container.md` — KT trio shares codecs but not containers
- `executable-resource-path-registry-names-asset-ids.md` — exe registry is the ID→name oracle; ExeFS never extracted
- `prescaled-joint-indices-divisibility-census.md` — G1M joint index = slot×3
- `cloth-submesh-repurposes-vertex-attributes.md` — NUN cloth submeshes reuse vertex attributes; hair/capes collapsed

Full list: `details/chimera.md` § "Lessons sourced from this corpus (full list)".
