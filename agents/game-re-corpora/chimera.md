# chimera — FE Three Houses, FE Warriors, FE Warriors: Three Hopes, FE Engage (Switch)

**Project root:** `~/Development/chimera` · **Full history/evidence:** `game-re-corpora/details/chimera.md` (read on demand) · **Open work:** one `docs/TODO.md`

Docs are flat `docs/<game>.md` (+ `fe3h-modding.md`, `few-modding.md`, `model-import-pipeline.md`, `kt-warriors-engine-survey.md`). Ids: `src/game-id.ts`. Decoders: `src/data/formats/`.

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

## Lessons sourced from this corpus
active-gui-tool-source-vs-passive-template-verify-stride.md, any-match-resumability-guard-orphans-partial-multi-item-entry.md, ascii-digit-version-field-needs-digit-weighted-decode.md, bind-pose-render-blind-to-joints-index-space-bug.md, bitmap-bit-order-from-transition-isotropy.md, block-chain-walk-stops-at-unknown-sibling-block-magic.md, bone-palette-may-bind-one-bone-twice-needs-proxy-joint-node.md, byte-granular-deswizzle-of-block-compressed-data.md, cloth-submesh-repurposes-vertex-attributes.md, community-format-name-mismatches-real-magic.md, community-table-name-mismatches-semantic-content.md, compressed-container-members-invisible-to-magic-scan.md, concurrent-sibling-live-edit-collision-on-shared-source.md, content-type-absence-needs-multiple-independent-angles.md, cross-platform-string-delta-reveals-stride-vs-offset.md, cross-table-outlier-corroboration-without-external-oracle.md, dense-range-offset-fit-needs-identity-oracle.md, detector-offset-generalized-from-partial-corpus-silently-skips-rest.md, doc-self-cross-reference-before-fresh-disassembly.md, embedded-texture-size-does-not-predict-material-diffuse-binding.md, engine-family-shared-decoder-not-shared-container.md, executable-resource-path-registry-names-asset-ids.md, external-validator-sample-insufficient-cli-spawn-slow.md, first-slot-magic-names-the-whole-container.md, first-subentry-only-check-misses-later-recurring-magic.md, format-field-width-unexercised-by-first-corpus.md, gap-region-may-be-offset-table-not-inline-header.md, gating-argument-may-be-a-compile-time-constant-not-data.md, gltf-joint-zero-weight-filler-duplicate-fear-untested.md, high-bit-set-field-is-flagged-index-not-pointer.md, identical-header-shape-two-container-formats.md, kind-marker-dispatch-grammar-survives-failed-stride-sweep.md, list-final-byte-is-a-data-value-not-a-terminator.md, live-ab-isolation-names-carrier-not-mechanism.md, magic-scan-can-substitute-for-container-reverse-engineering.md, missing-instance-link-invariant-table-substitutes.md, numeric-range-overlap-is-not-an-id-binding.md, override-layer-indexed-by-entry-id-not-semantic-filename.md, per-call-cache-clear-breaks-under-per-item-loop-conversion.md, per-instance-file-set-may-be-duplicate-blobs.md, platform-port-swaps-adjacent-header-fields.md, pointer-array-stride-signature-needs-content-plausibility.md, prefixed-sibling-family-shares-numeric-id-space.md, prescaled-joint-indices-divisibility-census.md, published-walkthrough-numeric-oracle.md, redundant-offset-field-poisoned-chain-by-length.md, reference-tool-data-revision-mismatch.md, reference-tool-field-never-consumed-by-its-own-importer.md, reuse-shared-palette-rows-for-byte-identical-reserialization.md, runtime-texture-swap-must-mutate-captured-original-material.md, secondary-attach-api-misses-primary-side-effect-wiring.md, semantic-output-diff-with-unchanged-parts-as-reference-frame.md, session-scratchpad-tmpfs-exhaustion.md, shared-decoder-behavior-is-a-cross-platform-contract.md, shared-table-column-role-varies-by-row-subtype.md, short-magic-hit-in-high-entropy-region-needs-falsification.md, sibling-field-comment-as-free-semantic-oracle.md, sibling-length-field-disagreement-read-past-real-stream.md, sibling-magic-may-be-same-struct-zeroed-field.md, silent-loader-clamp-makes-appended-record-look-live.md, skinned-composite-alignment-needs-joint-transform-diff.md, sparse-sample-flatness-heuristic-false-negative-on-real-content.md, stale-compressed-verdict-relocate-real-header.md, stored-bind-matrix-palette-is-a-per-entry-identity-oracle.md, undetermined-selection-may-be-immaterial-or-already-in-a-skipped-field.md, unexplained-pointer-pair-may-target-eof-anchored-footer.md, union-tiling-beats-per-record-offset-chaining.md, unknown-constant-field-is-engine-grammar-load-bearing.md, unknown-opcode-may-select-a-different-resource-kind.md, update-patch-ships-a-revised-struct.md, version-flag-conflates-independent-format-traits.md, vtable-bridged-consumer-defeats-call-census.md, weak-single-offset-fit-signals-missing-indirection.md
