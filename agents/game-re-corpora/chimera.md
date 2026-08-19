# Chimera — corpus notes

Seer-framework project (`~/Development/chimera`). Nintendo Switch titles
only. Docs convention differs from other seer projects: **one flat file per
game at `docs/<game>.md`** (not `docs/<game>/<platform>/data-structure.md`).
Architecture summary: `docs/architecture-overview.md`.

Games: `astralchain`, `fe-threehouses`, `fe-warriors`, `fe-engage`,
`few-threehopes` (`src/game-id.ts` is the source of truth for the exact
string ids).

## Solved

- **Astral Chain** (PlatinumGames) — **Textures fully solved**: `.pkz` (ZSTD)
  → `.dat`/`.dtt` pairs (or loose) → `.wta`/`.wtb`/`.wtp` → BC/ASTC.
  21,001/21,001 (100%, all 82 PKZ archives, 0 decode errors — the majority of
  textures are DAT-nested, not loose PKZ entries; see `docs/astralchain.md`
  for the DAT/DTT-pairing and duplicate-container-dedup corrections).
  `src/data/formats/pkz.ts`, `dat.ts`, `wtb.ts`, `texture.ts`. **Meshes fully
  solved**: `.wmb` (WMB3, PlatinumGames' NieR/Bayonetta-family model format)
  nested inside the same `.dat` archives as textures (0 loose PKZ entries,
  1,918 found across 4,083 parsed DAT/EVN containers) → GLB via
  `src/data/formats/wmb.ts` + `wmb-gltf.ts` (built on the shared
  `gltf-builder.ts` also used by the Koei Tecmo titles' G1M exporter below).
  1,815/1,822 GLBs (7 skipped as genuine sub-140-byte placeholder stubs), 0
  `gltf-validator` errors/warnings across the full corpus (in-process
  `validateBytes()`, not a per-file CLI sample — see
  `external-validator-sample-insufficient-cli-spawn-slow.md`, whose second
  confirmed instance is this exporter), 0 out-of-bounds joint indices across
  871 skins — does **not** share the `fe3h-joint-oob` TODO item's bug
  (different bone-remap scheme entirely). **Audio fully solved**: Astral
  Chain uses Audiokinetic Wwise middleware, not KTSR/Opus like the Koei
  Tecmo titles — loose `.wem`/`.bnk` under `sound/`, decoded via a vendored
  `tools/.bin/vgmstream-cli` build (the reference multi-format game-audio
  decoder; handles Wwise's stripped-RIFF "Custom Vorbis" and IMA-ADPCM
  codecs natively, no game-specific decode code needed) piped through
  `ffmpeg -c:a libvorbis` for Ogg Vorbis output. 11,391 tracks (8,172 loose
  `.wem` + 3,219 `.bnk`-embedded voice subsongs after locale-aware
  deduping), 0 decode errors. The v1.0.1 update patch was manually decrypted
  and diffed against the base game (`hactool --basenca=<base NCA>
  --titlekey=<key>`): changes only 2/1,243 meshes and 2/33 audio banks,
  genuinely negligible — not worth a patch-merge pipeline. See
  `docs/astralchain.md`.
- **Fire Emblem: Three Houses** — `DATA0.bin`+`DATA1.bin` (fixed 0x20-byte
  index records) → KT_GZ (Koei Tecmo block-zlib, size-prefixed chunks) → scan
  decompressed entries for G1T magic → BC/ASTC. 14,332 textures.
  `src/data/formats/data0.ts`, shares `g1t.ts` with the other two Koei Tecmo
  titles below. Real content is 13,448/13,467 textures of G1T type `0x59`,
  reports `platform=10` (NSwitch) but decodes **linearly, not swizzled** —
  deliberately excluded from `g1t.ts`'s `MORTON` set; see
  `docs/fe-threehouses.md` and the `byte-granular-deswizzle-of-block-
  compressed-data.md` lesson's corollary. **Meshes fully solved**: two
  DATA0/DATA1-resident container shapes both wrap the same G1M format the
  `fe-warriors` entry below also cracked (shared `src/data/formats/g1m.ts` +
  `g1m-gltf.ts`) — "PACK" entries (`u32 count` + `count x (ptr,size)`,
  community name `nx/action/model/*.bin.gz`, 569/893 non-empty, the real
  per-character/prop model source) and `.kldm` entries (community name only
  — real on-disk magic is `"MDLK0001"`, **not** compressed/proprietary
  despite an earlier pass's docs saying so; see
  `stale-compressed-verdict-relocate-real-header.md`, a chain of
  concatenated self-describing `_M1G` blocks with no embedded textures, 29
  found). Full-corpus run: 577 GLBs, 0 decode errors. Verified via the
  format's own bbox field vs. decoded POSITION min/max (5+ significant
  figures on 2/3 axes) and skeleton plausibility (183-bone humanoid rest
  pose); a genuine open issue remains in the shared skin/joint-index
  resolution (`ACCESSOR_JOINTS_INDEX_OOB` on every sampled GLB — geometry
  unaffected). **Audio fully solved**: `nx/sound/*.ktsl2stbin` (KTSR
  container, `src/data/formats/ktsr.ts`) wraps standard Opus audio behind an
  undocumented `codecID=9`; muxed to Ogg Opus via a from-scratch RFC 3533 +
  RFC 7845 muxer (`src/data/formats/ogg-opus.ts`) needing no game-specific
  decode step, verified via `ffprobe`/`ffmpeg` and cross-checked against a
  fan mod-tool's published per-character voice-line ID ranges (exact stream-
  count matches, e.g. `SE_EN` = 20,073). 86,147 tracks, 0 errors. A
  full-corpus DATA0/DATA1 scan for this audio came back completely empty
  (265 entries share the container's *outer* magic but are an unrelated
  command-table sub-resource) — the real files were loose romfs files
  **present in the NCA's own RomFS table but absent from the already-
  extracted dump on disk**; see `content-type-absence-needs-multiple-
  independent-angles.md`'s 5th angle. See `docs/fe-threehouses.md` for full
  byte layouts and verification evidence.
- **Fire Emblem: Engage** — Unity Addressables `.bundle` → UnityPy (Python
  subprocess, `tools/fe-engage/extract_unity_textures.py`). 12,922 textures.
  The `.resS` resource-stream path needs explicit resolution; UnityPy doesn't
  auto-resolve it.

- **Fire Emblem Warriors (2017)**, `fe-warriors` — **has no LINKDATA archive
  at all**, despite being the same Koei Tecmo/Omega Force Musou engine as
  the two games below and sharing their G1T texture format; see
  `engine-family-shared-decoder-not-shared-container.md`. Assets live as
  individual per-character/per-asset "pack" files directly in the romfs tree
  (`nx/action/model/*.bin.gz`, `nx/effect/*.bin.gz`, `nx/map/data/*.g1t.gz`,
  `common/battle/stage/*.gz`) — the `.gz` extension is stale/misleading, none
  of these are actually gzip. **Textures fully solved**: raw magic-byte scan
  for G1T's `GT1G` tag against every romfs file (bypasses the pack format
  entirely — see `magic-scan-can-substitute-for-container-reverse-
  engineering.md`); full-corpus run complete, 4,872/8,216 raw G1T entries
  decode to real content (rest are verified-flat placeholder maps). **Meshes
  fully solved**: the pack's `<letter>M1G<version>` chunk tags (previously
  unidentified) are G1M — Koei Tecmo's Warriors-engine model container,
  documented publicly by `three-houses-research-team/010-binary-templates`
  (010 Editor templates, used as the primary reference here — one real
  correction needed against the template, see `docs/fe-warriors.md`). Found
  the same way as G1T: raw magic-byte scan for `_M1G` against every romfs
  file, no pack-header parsing needed. `src/data/formats/g1m.ts` +
  `g1m-gltf.ts` (skinned GLB export, shares low-level GLB assembly with the
  Astral Chain WMB3 exporter via a new `gltf-builder.ts`); full-corpus run:
  461 GLBs, 0 decode errors, 0 `gltf-transform validate` errors across the
  whole batch. **Audio fully solved, 30,165 tracks** — an earlier
  "confirmed absent" verdict (four independent checks: extension census,
  corpus-wide magic scan, `ffprobe` on all 23 cutscene `.mp4`s, NCA
  content-type audit) was **wrong**: `extract-romfs.ts` had silently
  dropped `nx/sound`/`nx/voice` (and, unrelated to audio, `nx/ui`/`nx/
  stage`/`nx/shader`) from the extracted tree — the same extraction-gap bug
  already seen on Three Houses below; see Operational notes and
  `content-type-absence-needs-multiple-independent-angles.md`'s 5th angle.
  Recovered via a direct `hactool --romfsdir` re-extraction. Unlike Three
  Houses/Three Hopes, this game wraps bare `KTSS` blocks with **no `KTSR`
  root header at all** — a "G1L" container (`_L1G` magic, same reversed-
  magic convention as G1M) and the model-pack container above both just
  point a flat offset table straight at KTSS magics; `findKTSSStreams` (new
  export on `ktsr.ts`) scans for the raw magic directly rather than solving
  either table. **Codec also differs**: every stream is `codecID=2`
  (GameCube/Wii DSP-ADPCM), not Three Houses/Three Hopes' `codecID=9`
  (Opus) — confirmed against `vgmstream`'s source, which names this exact
  game in its `codecID=2` branch (see `format-field-width-unexercised-by-
  first-corpus.md`'s 4th instance). New decoder `src/data/formats/
  gc-adpcm.ts`, verified byte-exact (0 sample mismatches) against
  `vgmstream-cli`'s own decode across 14 samples. Output is WAV (ADPCM has
  no native browser decoder, unlike Opus): 193 BGM + 29,972 voice lines,
  0 decode errors, 7.3 GB. Sound effects (`nx/sound/se/*.bin.gz`,
  `_HBW0000`/`KWBN`-tagged, no KTSS/KTSR anywhere) are a **third, still-
  undecoded** audio container — not attempted. The model-pack container's
  own outer directory (a `{length, cumulativeEnd}` slot table) remains only
  partially reverse-engineered and was never needed for texture/mesh/
  BGM-voice extraction — all three use the direct magic-byte-scan approach
  instead.
## Partially solved

- **Fire Emblem Warriors: Three Hopes (2022)**, `few-threehopes` — LINKDATA
  container format **fully confirmed** (5,310/5,310 non-empty entries decode
  across all 19 archives): `src/data/formats/linkdata.ts`. Two per-entry
  payload encodings (raw vs. size-prefixed zlib chunk stream) selected by
  the `unpacked_size` field, both occurring in the same archive. **G1T
  textures are not inside LINKDATA** — a full census of every decoded entry
  in all 19 archives found zero G1T/G1M/KTSR magic anywhere; textures,
  meshes, and audio all instead live behind
  `File/CMN/Asset/FDataPackage/Master/` (`PDRK0000`/`IDRK0000`-tagged
  wrapper, not reverse-engineered — not needed, same magic-scan technique as
  `fe-warriors` finds every embedded resource directly). LANG text (11
  languages, not 12 as an earlier brief assumed — `LINKDATA_LANG_*.BIN`,
  1,280 entries/language, 100% zlib-compressed) is **fully extracted**:
  796,628 strings, plain UTF-8 (confirmed by decoding the same entry index
  in English and Japanese and getting 1:1 matching content — not UTF-16LE,
  not Shift-JIS, despite both being the a priori expectation). Decoder:
  `src/data/formats/kt-text.ts`, which scans for NUL-delimited printable-
  UTF-8 runs directly rather than depending on the per-entry offset table
  (partially reverse-engineered — a `{count, firstStart}` header then
  `{length, cumulativeEnd}` pairs, same shape as the `fe-warriors` pack
  container's outer table — but has an unresolved off-by-one on at least one
  real entry). `LINKDATA_A.BIN` (the other LINKDATA archive family,
  gamedata/CMN) also has text-shaped entries mixed with real binary
  game-data structs; the same NUL-delimited-string heuristic over-reports
  there (incidental UTF-8-valid byte runs inside binary tables), so it was
  **not** extracted this pass — would need real per-record-type
  classification first. Texture full-corpus run (1,417 `.fdata` files, 11
  GB) not yet launched; a bounded 20-file smoke test confirmed the extractor
  and its resumable `.progress`-file logic both work against real data.
  **Meshes and audio fully solved, and confirmed byte-identical to the
  sibling games' decoders** — a raw magic-byte scan of the same `.fdata`
  corpus (`ripgrep` over 11 GB, seconds not minutes thanks to OS page-cache)
  found G1M (`_M1G`/`<letter>M1G`, 198/1,417 files) and KTSR/KTSS (29/27
  files) alongside the already-known G1T hits, and both decoded with zero
  changes to `g1m.ts`/`g1m-gltf.ts` and `ktsr.ts`/`ogg-opus.ts`. **The G1T-
  bearing `.fdata` corpus also holds audio, via a second, previously-
  unnoticed member class**: not every asset in
  `File/CMN/Asset/FDataPackage/Master/` has a `.fdata` extension — a
  sibling `Master/data/*.file` directory holds 28 large (6.6 MB-380 MB)
  loose bulk-resource blobs, 27 of which are audio banks (the other is
  something else with a different `PDRK0000` sub-tag, see below); they
  share the exact same wrapper header family as `.fdata`, just under a
  different filename convention and outside the `.fdata` extension a naive
  `find *.fdata` would use — worth checking for on any future Koei Tecmo
  title with an FDataPackage-style asset store: don't assume one file
  extension covers the whole package family. Full-corpus runs: 181 GLBs
  (882 G1M containers, 0 decode errors, 0 `gltf-transform validate` errors
  on a 39-file sample) and 97,286 Ogg Opus tracks (0 decode errors,
  `codecId=9` on every stream, matching Three Houses' empirical Opus
  convention). The wrapper's per-entry resource-type tag (4 ASCII bytes at
  wrapper offset 0x38) was observed to vary by content — `"TSRS"` on real
  audio banks, `"CGRS"` on an empty/placeholder KTSR shell — a cheap
  classification hook if the wrapper is ever fully reverse-engineered, but
  not needed for extraction (the magic-byte scan works regardless).

## Engine-family links

Astral Chain is a one-off within this project (PlatinumGames, PKZ/WTA-WTB
textures + WMB3 meshes, unrelated codec family to the Koei Tecmo titles) —
but its **audio middleware (Audiokinetic Wwise, `.wem`/`.bnk`) is a
widely-used cross-studio standard**, not game- or engine-specific: any
future Switch/PC/console title shipping loose `.wem`/`.bnk` files should
reach for a vendored `vgmstream-cli` build first (see `docs/astralchain.md`
"Audio (Wwise)" for the exact CMake build invocation), the same way this
project already steers Koei Tecmo Musou-family titles toward `g1t.ts`/
`g1m.ts`/`ktsr.ts` — vgmstream is the reference decoder for Wwise's
stripped-RIFF "Custom Vorbis" codec and handles it with zero game-specific
code, so there's no reason to hand-port the community `ww2ogg` tool's
codebook-repacking logic for a new Wwise title either.

`fe-threehouses`, `fe-warriors`, and `few-threehopes` are all Koei
Tecmo/Omega Force Musou-engine titles and share the **G1T texture format**
(`g1t.ts`) — but *not* a shared archive/container (see
`engine-family-shared-decoder-not-shared-container.md`): Three Houses reaches
G1T via `DATA0`/`DATA1`, FE Warriors via per-asset pack files with no
top-level index, Three Hopes via `.fdata` blobs with no LINKDATA involvement.
Any future Koei Tecmo Warriors-family Switch title should be checked against
`g1t.ts` and the magic-byte-scan technique before assuming a new texture
codec is needed, but its *container* should be verified from scratch (a
five-second `find`/`grep` for the expected archive filename, before planning
any header-comparison work). The same split applies to **meshes**: all
three titles (Three Houses, FE Warriors, Three Hopes) wrap the identical
G1M model format (`g1m.ts` + `g1m-gltf.ts`, shared verbatim across all three
pipelines, reused **completely unmodified** for Three Hopes — see
`concurrent-sibling-live-edit-collision-on-shared-source.md` for how Three
Houses/FE Warriors independently converged on the same byte layout), reached
via three structurally different containers (DATA0/DATA1-resident
PACK/`.kldm`, a headerless per-asset pack, and `.fdata` asset packages
respectively — each found by the same raw magic-byte-scan technique, never
by understanding the container). **Audio**: Three Houses' and Three Hopes'
KTSR/KTSS-wraps-Opus format (`ktsr.ts`, `ogg-opus.ts`) is also confirmed
**byte-identical between those two titles**, reached via two different loose-
file locations (`nx/sound/*.ktsl2stbin` vs. `File/CMN/Asset/FDataPackage/
Master/data/*.file`) — both games report the same empirical `codecId=9`
Opus convention. **FE Warriors (2017) breaks the "codec doesn't [differ]"
half of that pattern**: same `KTSS` magic, but no `KTSR` wrapper (a "G1L"
container or the model-pack shape point straight at KTSS blocks instead)
and a different codec entirely (`codecID=2`, GameCube/Wii DSP-ADPCM, not
Opus) — the earlier (2017) title predates the Opus convention the two
later titles share. Any future Koei Tecmo Warriors-family Switch title
should check `g1m.ts` unmodified against real data before assuming a new
mesh decoder is needed (three-for-three so far on "container differs,
codec doesn't" for meshes) — but for **audio** specifically, check the
`codecID` field first before assuming `ktsr.ts`'s Opus path applies
unmodified; an earlier, pre-Opus-era Koei Tecmo Switch title is exactly the
shape of game where it won't.

## Operational notes specific to this project

- **Memory-constrained shared dev machine.** `data/extracted/` holds ~115 GB
  across five romfs dumps; other projects on the same machine can hold
  double-digit GB of RSS concurrently. Prefer fd-based random access
  (`openLinkData`/`loadDATAArchive`/`openPKZ` all show the pattern) over
  `readFileSync`-the-whole-file, especially in any corpus-wide scan script;
  `--max-old-space-size` does not bound `Buffer`/WASM linear memory, so a
  Node heap cap alone won't prevent an OOM from a large allocation.
- **`npm run extract-data` with no `--game` runs every registered game.**
  Always scope with `--game <id>` unless a full multi-game run is actually
  intended.
- Several stages (`fe-threehouses`, `fe-warriors`, `few-threehopes`) use a
  `.progress`/`fdataProgress.json`-style resumability pattern: a JSON array
  of already-processed relative paths written after every file, checked at
  stage start. A bounded `limit` parameter (stop after N new files) is a
  useful smoke-testing pattern layered on top of the same resumability logic
  — proves a stage's real end-to-end behavior against real data without
  paying for a full multi-GB sweep.
- `tools/shared/__tests__/game-config.test.ts` enforces that every
  `GAME_IDS` entry has a matching `GAME_CONFIGS` entry with both a
  `romfsSignature` and a `buildAssets` — registering a new game and
  forgetting one half of that pair is a guaranteed test failure, not a
  silent gap.
- **An already-extracted `data/extracted/.../p0-romfs` dump is not
  guaranteed complete — confirmed twice now, treat this as certain, not
  possible.** `tools/extract-romfs.ts`'s one-shot NSP→romfs extraction
  silently dropped an entire directory (`nx/sound/`, 3.2 GB, 17 files) for
  Three Houses despite the files being present in the Program NCA's own
  RomFS table, and separately dropped **eight** directories including
  `nx/sound`+`nx/voice` (2.2 GB combined) for FE Warriors (2017) — that
  second gap was missed for an entire pass, long enough for a "confirmed
  absent" audio verdict built on the incomplete tree to ship in the
  project's docs before being caught. Caught both times via `tools/.bin/
  hactool -k <prod.keys> --disablekeywarns --listromfs <NCA>` (lists the
  archive's own directory without re-extracting anything) compared against
  the extracted tree's real file count, then recovered with a full
  `--romfsdir=<out>` re-extraction against the same already-decrypted NCA
  and copying just the missing subtrees in. **Run the `--listromfs`
  file-count comparison unconditionally, first, before any content-level
  investigation** — not as a fallback check after a negative result looks
  suspicious — on every Switch romfs dump in this project; see
  `content-type-absence-needs-multiple-independent-angles.md`'s 5th angle
  for why this now outranks the other four negative-result angles. Also
  note: adding a recovered subtree back into an already-"fully extracted"
  romfs can break *other* stages that blindly walk the whole tree by
  design (G1T/G1M are found by magic-byte scan, not extension) and whose
  own `.progress` resume files don't know about the new files — FE
  Warriors' `nx/sound`/`nx/voice` recovery included one ~1 GB single file
  that, combined with the texture/mesh stages both trying to `readFileSync`
  it inside `extract-data.ts`'s one shared Node process, reliably OOM'd;
  fixed by excluding the (confirmed audio-only) recovered trees from those
  two stages' file walks.
