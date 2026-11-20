# lucina — Fire Emblem Awakening/Fates/Echoes/Warriors, Bravely Default/Second, Monster Hunter 4 Ultimate (3DS)

**Project root:** `~/Development/lucina` · **Full history/evidence:** `game-re-corpora/details/lucina.md` (read on demand) · **Spec:** one cross-title doc, `docs/3ds-formats.md` · **Open work:** `docs/<game>/TODO.md` · **Last audit:** `docs/<game>/audit-2026-11-18{,-changes}.md`

Data under `data/<game>/3ds/` (decrypted images; Echoes ships sealed). Project decoders: `src/formats/`; build steps: `tools/shared/`.

## Games
- Fire Emblem Awakening — `fe-awakening` — CGFX models, CTPK, `.arc`, `.bfnt` fonts, BCSTM; DLC CIA
- Fire Emblem Fates — `fe-fates` — BCH models + `ba/` skeletal clips; DLC CIAs unindexed
- Fire Emblem Echoes — `fe-echoes` — sealed CIA + BCH
- Fire Emblem Warriors — `fe-warriors` — Koei Tecmo LINKDATA → KT packs, G1M, G1T; BCSAR, no BCSTM
- Bravely Default — `bravelydefault` — **fan-modified dump** (Undub/Uncensored patch): byte-level claims describe the mod
- Bravely Second — `bravelysecond` — `.fs` crowd/index pairs, darc, CGFX
- Monster Hunter 4 Ultimate — `mh4` — Capcom MT Framework `.arc` (MOD, TEX, MRL), MCA audio

## Solved formats → where documented (all in `docs/3ds-formats.md`)
- RomFS/NCCH/CIA stack incl. > 2 GiB offsets — §1
- LZ10/LZ11/"LZ13" and the stored `00` wrapper — §2; decoder upstream in `@seer-project/3ds` `lz.ts`
- CTPK and CTR textures — §3–4; seer `ctpk.ts`, `ctr-texture.ts`
- FE `.arc` (generic pointer-table BIN container, also `m/*.bin.lz`, GameData) — §5, `src/formats/fe-arc.ts`
- BCH (Fates/Echoes, embedded textures, `ba/` clips) — §7, §13–14; CGFX multi-model (Awakening/Bravely) — §11
- Bravely `.fs` index + member wrapper — §7.2, `src/formats/fs-archive.ts`, `tools/shared/fs-member.ts`
- `.bfnt` font atlas — §7.3, `src/formats/bfnt.ts`
- G1T textures (KT) — §8, `src/formats/g1t.ts`; G1M — `src/formats/g1m.ts`
- MT Framework `.arc` / MOD / TEX — §9, `src/formats/mtf-mod.ts`, `mtf-tex.ts`
- BCSTM audio via ffmpeg — §12

## Engine-family / cross-project links
- Koei Tecmo G1M/G1T/LINKDATA: `chimera.md` (FE Warriors on Switch, Three Houses, Three Hopes) — same codec family; check per-texture header flags and containers separately (`engine-family-shared-decoder-not-shared-container.md`).
- 3DS shared codecs live in `@seer-project/3ds`, linked via `file:` symlink to seer `dist/`: rebuild seer before lucina picks up a decoder change.

## Reusable code in this repo
- `tools/shared/` — `bch-build`, `cgfx-build`, `fe3ds-build`, `fs-member`, `linkdata`, `romfs-export`, `gltf-export`, `audio-build`
- Real-data tests with null controls: `src/formats/__tests__/{g1t,bfnt}-real.test.ts`, `tools/shared/__tests__/fs-archive-real.test.ts`; seer `packages/3ds/src/__tests__/lz.test.ts`

## Know before you start
- **`docs/3ds-formats.md` often carries heavy uncommitted user WIP.** Treat the working copy as authoritative; don't commit or revert it unless asked.
- **`data/fe-echoes/3ds/` holds key/ticket files — never read them or attempt decryption.**
- Bravely Default is a fan patch build: don't generalise its bytes to retail.
- The shared LZ decoder passes unknown input through silently; census pass-throughs when adding a corpus.
- LZ13's outer u24 is an in-place buffer size, not the decompressed size; size from the inner LZ11 header.
- CTPK format ids are the PICA200 hardware values despite older comments.
- Several "fixed" constants came from small samples (G1T header, bfnt selector, MH4 stride filter): re-check over the whole corpus.
- Any "validated with <tool>" claim: check the tool exists in the repo (gltf-validator didn't).

## Key lessons
- `decoder-passthrough-fallback-hides-wrapper-variants.md` — LZ pass-through hid 31 stored `.lz` files
- `crunched-size-mistaken-for-decrunched-size-invariant-mismatch.md` — LZ13 outer size = in-place buffer
- `pixel-format-value-guessed-from-enum-not-confirmed.md` — CTPK "not hardware enums" was backwards
- `formula-check-small-sample-misses-conditional-rounding-term.md` — G1T 20-B header, bfnt selector from samples
- `tracker-prose-is-not-evidence.md` — README gltf-validator claim with no validator
- `engine-family-shared-decoder-not-shared-container.md` — KT codecs shared with `chimera`, containers differ

Full list: `details/lucina.md` § "Lessons sourced from this corpus (full list)".
