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
  decompressed entries for G1T magic (plus, folded in later, entries whose
  shape is a "PACK" model container with its own embedded G1T section — see
  Models below) → BC/ASTC. 16,014 textures (1,682 of them pack-embedded).
  `src/data/formats/data0.ts`, shares `g1t.ts` with the other two Koei Tecmo
  titles below. Real content is 13,448/13,467 textures of G1T type `0x59`,
  reports `platform=10` (NSwitch) but decodes **linearly, not swizzled** —
  deliberately excluded from `g1t.ts`'s `MORTON` set; see
  `docs/fe-threehouses.md` and the `byte-granular-deswizzle-of-block-
  compressed-data.md` lesson's corollary. **Meshes fully solved** (including
  skinning — see the "G1M skinning — SOLVED" block under `fe-warriors` below,
  which is where the shared `MM1G` inverse-bind-matrix finding is written up;
  this game is where the bug surfaced, as cloth/hair exporting heaped on the
  ground): two
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
  pose). The shared skin/joint-index resolution's `ACCESSOR_JOINTS_INDEX_OOB`
  was already fixed by a same-day commit an earlier pass's doc note
  predated; a later pass confirmed 0 OOB errors corpus-wide and additionally
  fixed a lower-severity `ACCESSOR_JOINTS_USED_ZERO_WEIGHT` warning storm —
  see `gltf-joint-zero-weight-filler-duplicate-fear-untested.md`. **Audio
  fully solved, two codecs**: `nx/sound/*.ktsl2stbin` (KTSR container,
  `src/data/formats/ktsr.ts`) wraps standard Opus audio behind an
  undocumented `codecID=9`; muxed to Ogg Opus via a from-scratch RFC 3533 +
  RFC 7845 muxer (`src/data/formats/ogg-opus.ts`) needing no game-specific
  decode step, verified via `ffprobe`/`ffmpeg` and cross-checked against a
  fan mod-tool's published per-character voice-line ID ranges (exact stream-
  count matches, e.g. `SE_EN` = 20,073). 86,147 tracks, 0 errors. A
  full-corpus DATA0/DATA1 scan for this specific audio came back completely
  empty (265 entries share the container's *outer* magic) — the real files
  were loose romfs files **present in the NCA's own RomFS table but absent
  from the already-extracted dump on disk**; see
  `content-type-absence-needs-multiple-independent-angles.md`'s 5th angle.
  Separately, those same 265 DATA0-resident `KTSR`-magic entries **do**
  embed a second, different audio family after all: GC/Wii DSP-ADPCM
  ("KTGCADPCM") voice lines, missed by an earlier pass that only checked
  the first sub-entry after the entries' own root header — see
  `first-subentry-only-check-misses-later-recurring-magic.md`. Decoded via
  `src/data/formats/ktgcadpcm.ts` (reuses `gc-adpcm.ts`'s already-verified
  `decodeChannel`), byte-exact-verified against the community's own
  conversion tool + `vgmstream-cli` after fixing a declared-sampleCount-vs-
  declared-streamSize mismatch (see
  `sibling-length-field-disagreement-read-past-real-stream.md`). 14,625
  WAVs, 0 errors. **Gamedata: nine tables solved** (all share one outer
  `u32 numSections + (ptr,size)[]` + per-section 64-byte-header container,
  `src/data/formats/gamedata-container.ts` — every "`.bin.gz`" gamedata
  table name in this game's community docs is a file-name-map convention
  over a DATA0 entry, not a real romfs path, same pattern as "PACK"/
  `.kldm`): PersonData (DATA0 index 12, 1,059 character stat records,
  verified against the game's own `Names` character enum — 57/58 exact
  matches in canonical order); ClassData (index 11, 90 records, male/
  female asset IDs + weapon-rank bonuses verified via dozens of internal-
  consistency checks against real class archetypes); ItemData's weapon
  block (index 6, 500 records, verified byte-exact against published FE3H
  weapon stats — MT/Hit/Wt/Dur); Skill's ability-list block (index 15, 240
  records, verified via a **published-skill-effect oracle** — decoded
  `{property,value,condition}` enum triples for `Death_Blow`/
  `Fiendish_Blow`/`Darting_Blow`/`Vantage` matched their real documented
  effects exactly, see `published-walkthrough-numeric-oracle.md`'s
  skill-effect variant); StageData's terrain-data block (index 10, 128
  records, verified against real FE3H terrain mechanics — Forest/Desert
  avoid bonuses, Rock/Mountain flier-only passability); GrowthData's EXP-
  multiplier-by-level-difference (index 9, section 0, 41 records) and
  EXP-to-level-curve (section 5, 98 records) blocks, the latter verified
  via a compound-growth recurrence self-check (`floor(prev*1.1)` exact for
  21 consecutive values, then a slower regime — see
  `verification-techniques.md`'s recurrence-oracle addition) — **despite
  its name, this table holds global EXP-system constants, not
  per-character growth rates**, refuting an a-priori correlation
  hypothesis with `PersonData`, see
  `community-table-name-mismatches-semantic-content.md`; CalendarData's
  Celebrations block (index 35, 200 records) verified decisively via two
  independently-resolving enum spaces agreeing on 34/34 birthday records
  (record-index → `CalendarEvent` name, and the record's own `relatedCharId`
  field → the same `Names`/`CharID` enum `PersonData` uses); FreeScenarioData's
  Auxiliary-reward block (index 23, 100 records, verified via real
  `MiscItem` fishing-bait IDs resolving inside `FishAndBait`-category rows);
  Shopdata's weapon-shop block (index 30, 200 records, buy:sell ≈3:1 ratio
  matching the FE series' well-known shop convention). `src/data/formats/
  person-data.ts`, `class-data.ts`, `weapon-data.ts`, `skill-data.ts`,
  `stage-data.ts`, `growth-data.ts`, `calendar-data.ts`,
  `free-scenario-data.ts`, `shop-data.ts`. **`Scenario` (index 22, the
  per-battle chapter/paralogue/aux table) is now solved and shipped too**
  (`scenario-data.ts`, 100 records) — and this project is the account's
  worked example of the **"an update patch ships a revised struct, and the
  community template describes the *newer* build"** pattern
  (`update-patch-ships-a-revised-struct.md`). Two prior passes had refuted
  the community `Scenario.bt`'s declared field order against the base
  archive's 40-byte records and recovered only `chapter` at offset 5 from
  a template-blind byte census. In fact the v1.1.1 update ships the same
  table as a loose LayeredFS file (`nx/data/fixed_scenario.bin`) in every
  patch layer, and **patch3's records are 46 bytes and match the
  template's declared order verbatim** — `46 = 40 + 5` (the five
  `CharacterSettings` character-id fields widened `u8`→`int16`, forced by
  the DLC characters' own CharIDs 1040-1046) `+ 1` trailing pad. The two
  revisions then cross-check each other: mapping every stride-40 column
  onto its stride-46 counterpart and diffing adjacent patch layers gave
  **3,480/3,480 byte-exact on all 87 non-DLC records** vs null controls of
  16.8% (identity) and 22.3% (offset+5), confirming both layouts at once.
  Note the two revisions also *reorder* three field groups, so a
  widen-in-place bridging hypothesis was refuted — deceptively, since it
  decoded the record's tail correctly while the head was garbage. Also
  resolved along the way: the template's `unk1` u32 is a per-location
  `(x,y)` Fódlan world-map pin (33/37 maps carry exactly one coordinate,
  the 4 exceptions being exactly the region-generic battlefields; 8/8 DLC
  records reuse the base build's coordinate for their map), and the file
  has 2 sections, not 1. Still raw: `unkTeamModifier`/`unk3`/`unkTernary`/
  `progress[3]` (offsets confirmed by the cross-revision mapping,
  semantics not) and section 1's 11×3 table. The enum-mining techniques
  this needed — an index→label enum as free ground truth, a sparse enum's
  *gaps* as a negative test, and enum members' variant suffixes pinning a
  parallel array's slot order — are written up in
  `game-re-method/verification-techniques.md`. 1 further gamedata table
  remains undecoded (StageEnvInfo — outer container structurally
  confirmed), and BSI event scripts are structurally scoped but not decoded (real
  bytecode, confirmed via shared-prefix nesting across sibling events —
  container itself is byte-exact confirmed with no magic-number guess
  needed, via a 5-repeated-trailing-field-equals-filesize fingerprint).
  **`ktgcadpcm.ts`'s DSP-info block field order fixed** (a `+0x00`/`+0x04`
  sampleCount/nibbleCount mislabel inherited from an earlier pass, flagged
  by Three Hopes' byte-identical `asrs-ktsr.ts` struct and confirmed via a
  corpus-wide byte-accounting invariant, 0/14,847 deviations — see
  `platform-port-swaps-adjacent-header-fields.md`'s 4th case); all 14,625
  shipped voice-line WAVs regenerated. `.kldm` map-prop containers' leading
  header mostly decoded too — the two previously-unexplained "20 bytes
  apart" pointer fields turned out to target a trailing, EOF-anchored
  footer sub-container (nested `{count,(ptr,size)[]}` table + a per-object
  index array + an optional constant float block), found via testing
  `decompressedSize - field` arithmetic across the whole 29-entry corpus —
  see `unexplained-pointer-pair-may-target-eof-anchored-footer.md`. See
  `docs/fe-threehouses.md` for full byte layouts and verification
  evidence. **Animation fully solved, 126
  GLBs / 504 clips.** The community/task-brief name "G1A" (magic `_A1G`)
  was wrong — see `community-format-name-mismatches-real-magic.md`; the
  real format is **G2A** (magic `_A2G`, bit-packed/quantized cubic-curve
  keyframes), byte-identical to `fe-warriors`' G2A below (shared
  `src/data/formats/g2a.ts` + `g2a-gltf.ts`, ported from `Joschuka/
  fmt_g1m`'s Noesis plugin). Container differs from FE Warriors though:
  clips are embedded inside the same PACK/`.kldm` entry as the mesh
  (found via the same `_A2G` magic-byte scan, no container parsing
  needed). Verified via structural size-accounting (0 deviation) and
  physical plausibility (root/hip bone height matches the engine's known
  convention). Exported as a **separate skeleton-only GLB per character**
  (multiple named clips), not merged into the existing mesh GLBs — zero
  regression risk to the shipped mesh corpus. **Character/class ->
  3D-model-file mapping SOLVED** (`src/data/formats/asset-id-table.ts`):
  `PersonData`/`ClassData`'s small `assetId` field is a row index into
  `PersonData`'s own previously-unopened section 1 (a sibling of the
  already-decoded section 0, same container), whose `part1Body`/
  `part2Body`/`part1Head`/`part2Head`/`sothisFusedID` fields resolve to
  the real DATA0 mesh-pack index via per-kind additive constants
  (+3120/+3620/+3049) — corpus-wide 352/355, 144/144, 31/31, 87/88, every
  miss traced to a genuinely-empty archive slot (effectively 100%). An
  earlier direct `assetId + k` offset sweep only best-fit 87% — the fix
  needed one more indirection layer, not a better constant (see
  `weak-single-offset-fit-signals-missing-indirection.md`). The
  indirection section itself was found via a second, previously-
  unconsulted community source — `three-houses-research-team/Progenitor`,
  a full C# data-editing GUI (not just the already-read passive
  010-template repo) — whose own per-record reader has a real off-by-one
  stride bug, caught by checking it against the container's
  self-describing header instead of trusting its field count (see
  `active-gui-tool-source-vs-passive-template-verify-stride.md`). Shipped
  as a `tools/viewer/` character+class **model picker** (pick a name, pick
  a class, get the real rendered GLB — gender auto-defaulted from a newly
  decoded `PersonRecord.gender` field, pre-/post-timeskip variant
  selectable), end-to-end Playwright-verified against the real running
  dev server (Edelgard's personal outfit vs. her generic female Great
  Knight class render as two correctly distinct, real, textured meshes).
  Also surfaced a small residual mesh-export gap: 21 real, valid PACK
  entries (the game's giant monster-boss roster) parse but yield no
  geometry/skeleton in the existing G1M exporter — not investigated
  further, tracked as `fe3h-monster-pack-export` in `docs/TODO.md`.
  **Follow-up pass: the picker now composites the resolved head model
  onto the body** in the same 3D view (`MeshSession.addModel()`), verified
  correct via a byte-level joint-name/transform diff between two real
  shipped GLBs rather than a guessed offset (see
  `skinned-composite-alignment-needs-joint-transform-diff.md`) and
  confirmed visually via Playwright screenshots across several characters/
  variants. The same pass investigated whether shared generic-class
  bodies get a per-character recolor beyond the head swap and closed it as
  a "not reachable" negative — **superseded by a later re-oracle pass: the
  recolor is real and SOLVED, file-based like every KT sibling** (third
  worked example of "appearance variation via distinct files, never shader
  tints", after Astral Chain's per-costume `.dat`s and FE Warriors' `_V_*`
  files). DATA0 4740-5891 is 128 blocks x 9 replacement-diffuse GT1G
  variants (per shared class body / generic-unit body / mount barding /
  shield; `block = part2Body - 130` for bodies 130-194, Dancers at blocks
  65/66, single-wearer personal classes excluded — they carry baked
  diffuses instead), selected per character by the same `PersonData`
  section-3 `PaletteID CharColor` field the earlier pass had already
  domain-verified (house leaders = their house colors; enum->slot map 9/11
  domain-verified, still hypothesis-grade). Class-body PACKs ship **no
  colour diffuse at all** (mask+normal+grey only) — the palette entry IS
  the diffuse. **A later pass fully wired this into the viewer**: all
  1,134/1,134 confirmed-present palette textures shipped as PNG assets
  (fixing two real pipeline bugs found along the way — a `.some()`-vs-
  `.every()` resumability guard that permanently orphaned a partially-
  emitted multi-texture entry, and a sparse-sample flatness heuristic that
  false-positived on real low-colour-diversity armor textures), a runtime
  per-character baseColor swap in the picker (mutating the loaded model's
  captured original material in place so it survives a render-mode
  toggle), and a real default-slot bake for the flat asset browser's
  static class-body/Dancer GLBs. One more correction surfaced while
  wiring it: the class-body PACK's real "diffuse" material binding
  (its G1M material table's type-1 texture) resolves to a literal 4x4
  placeholder texture, not one of the "big" mask/normal/grey textures as
  first assumed — the swap has to target the pack's TINY embedded
  texture(s), not its large ones, confirmed by reading the G1M material/
  submesh binding table directly rather than reasoning from raw G1T
  texture sizes. Playwright-verified: Edelgard vs. Dimitri as Great Knight
  render distinctly recolored (red/gold vs. grey/navy armor), zero console
  errors; a character with no `CharColor` record falls back cleanly to a
  documented default slot. Two `CharColor` enum values (`White_and_Red_2`,
  `Red_2`) still use an unconfirmed slot-alias fallback — tracked as
  `fe3h-charcolor-alias-values` in `docs/TODO.md`. The decisive prior art
  was the community's `Throne-of-Knowledge/Model_and_Texture_List.txt`, a
  fan archive-index->name list naming every palette block+colour — for any
  game with a research org, grep their wiki/txt asset lists for
  "palette"/"costume" ranges before byte-hunting a recolor mechanism. The
  earlier pass's structural negatives all stand (the variants live outside
  both checked places); its `sothisFusedID + 3049` "31/31 confirmed" body
  resolution however is REFUTED (noise fit — see
  `dense-range-offset-fit-needs-identity-oracle.md`; the field is really a
  per-character hair-variant id, asset resolution still open, and the same
  table's community field names mislead across row subtypes — see
  `shared-table-column-role-varies-by-row-subtype.md`). Full spec:
  `docs/fe-threehouses.md` § "Class-body palette variants — SOLVED" and
  § "Class-body palette variants — WIRED (implementation)". **First
  executable-level RE for this game (later pass):** decompressed `main`
  (both base and v1.1.1-update builds; the update genuinely differs and was
  used) confirmed the engine's `KTGL_FX_SHADING_MESH_PHYSICALLY_BASED2_
  INDEXED_RAMP` toon-ramp shading mode is real (leaked literal enum text in
  rodata) with ~25 named ramp/rim-light shader parameters as strings
  (`rampIndex`, `rampCoordBias/Range/Scaler`, two-band `rampHL*`/`rampHH*`,
  primary+secondary rim-light params, `rampSDOccFade`) — the same engine
  family as Three Hopes' `QGWS`-mined `rampIndex` lead, confirming it
  generalizes. `IndexedRamp` is load-bearing (9 real ARM64 xrefs via a
  hand-written `ADRP`+`ADD` scanner, interleaved with 8 xrefs to
  `Refraction` at the same code region — a shared shading-mode
  name-registration loop). Independently, a full census of this game's own
  G1M texture-binding `type` field (7,080 bindings) found the exact
  predicted channel set by pure pixel statistics: type=3 is always a
  tangent normal map, type=5 a low-saturation grey scalar map, type=29 a
  mostly-zero single-green-channel mask — matching the ramp-coordinate
  input, an AO/specular scaler, and a per-pixel ramp-index override
  respectively, and matching this project's own already-documented
  "mask+normal+grey, no diffuse" class-body texture set found months
  earlier by content alone. No runtime trace connects a `type=29` binding
  to a ramp sampler slot specifically (data-driven inference, not code-
  confirmed); raw NVN shader microcode untouched (no tooling); still open
  as `fe3h-shading-pipeline`. **Later pass — viewer approximation shipped**:
  a new `'indexedRamp'` `MeshShadingMode` (`@seer-project/engine-3d`'s
  `mesh-shading.ts`, `MeshToonMaterial` + a synthetic 4-band `gradientMap`
  + an `onBeforeCompile` Fresnel rim term) is wired into `tools/viewer`,
  fed by the confirmed `type=3`/`type=5` bindings now exported as real
  glTF `normalTexture`/`occlusionTexture` via an opt-in, per-game-gated
  `g1m-gltf.ts` parameter (`{ rampTextures: true }`, FE Warriors/Three
  Hopes untouched — see `shared-decoder-behavior-is-a-cross-platform-
  contract.md`) — Playwright-screenshot-verified as visibly more stylized
  than the existing `'lit'`/`'toon'` modes on a class-body pack, 0 console
  errors. A real fresh header-only G1T scan (19,764 textures, no pixel
  decode) for a ramp/gradient-LUT-shaped texture also came back negative
  this pass (one `256x1` candidate decoded to a dither/noise pattern, not a
  gradient) — converts the "no ramp texture found" line above from
  carried-over prose into a checked negative. Still open, unchanged: the
  `type=29` binding, the `0x2d` registration constant, and the shader's
  real curve/rim constants — the shipped mode is a documented,
  honestly-labeled approximation, not a reconstruction. See
  `docs/fe-threehouses.md` § "Shading pipeline — engine-level evidence
  CONFIRMED, full binding chain still open" (subsection "Recommended
  viewer render mode — IMPLEMENTED"). **DLC "Change Attire" outfit system
  SOLVED end-to-end (2026-09-01/02, `re-codebreaker` + `re-oracle`)**:
  hardcoded 11-record outfit-slot table (`main` v1.2.0 image `0x19E87A0`,
  entries at `0xCD8A04`; 8 wildcard "any character" slots + 3 Byleth-only),
  AOC mount + global-archive-index map (base 0..31159, patch INFO1 31160+,
  DLC merge window 35223..36282), pure content-presence gating (archive-
  existence probes, no save flag), and — the final hop, cracked only after
  a plain ADRP+ADD xref on the table's own data address exposed a
  vtable-bridged consumer no bl-census could reach — the modelId→archive
  resolution: `modelId ∈ [500,570] → +400`, then the universal part
  resolver `FUN_3CD70` maps unified ids [900,1067] → `34810+id` (= DLC
  local `modelId−13`) and <900 → `3120+id`. 21/21 outfit models
  identity-verified as full bodies in the correct DLC archive (per-slot
  gate flags probe exactly each slot's own `modelId−13`), and wildcard
  records' `extraId=−1` structurally guarantees the head never changes —
  matching user gameplay ground truth. An earlier "3120+modelId for
  everything" formula was that resolver's `<900` branch misapplied: the
  5xx ids collided onto other characters' head packs (`HEAD_BASE =
  3120+500`). Full trace: `docs/fe-threehouses.md` § "Outfit `modelId` →
  archive index — SOLVED"; scripts in
  `build/cache/scratch/fe3h-outfit-resolve/`. **Save-slot format SOLVED
  (read-only, 2026-08-27 + re-derived 2026-09-02)**: 12-byte header
  (`u32 checksum = sum(data) mod 2^32`, `u32 version` 13 | 23, `u32
  fileSize`), then the roster — a sparse `Character[60]` array at
  `SaveData+0x644` whose `int16 Id` at record `+0x24` is the `PersonData`
  ROW INDEX (`-1` = empty); recruitment IS array membership, no separate
  flag. Two revisions: `version` 13 = 152,588-byte files, stride `0x230`;
  `version` 23 (current) = 154,412 bytes, stride `0x24C` — the +1,824 is
  60 x 28 (per-record `ClassExp`/`ClassLevel` widened 90 -> 100, tracking
  `fixed_classdata.bin`) + 144 pre-`Player`, so `Id` stays at `+0x24` and a
  whole-array-shift read can never match (see
  `cross-platform-string-delta-reveals-stride-vs-offset.md`'s 2nd
  instance). Verified on 14 real files incl. `suspend` (a full save image +
  battle state; checksum over the declared range only). `src/data/formats/
  fe3h-save.ts`, `tools/fe-threehouses/save-roster.ts`. An appended
  `PersonData[1201]` fits the int16 field but is exactly the first index
  `FindCharacterSlotById`'s hardcoded `Id > 1200` ceiling rejects — and,
  per the 2026-09-03 whole-corpus table-capacity audit
  (`docs/fe3h-modding.md` § "Fixed-size gamedata table capacity audit"),
  it is never even installed: every one of the 181 gamedata section
  loaders called from `main+0x3b5330` clamps `recordCount` to a compile-time
  CAP (`cmp/mov/csel`), `PersonData` at 1201, with three zero-exception
  invariants (`hdrOff == 24*CAP+8`, singleton alloc `== 24*CAP+32`,
  `CAP == shipped count` bar 5 named sections). So re-parking the record on
  one of the 113 byte-identical filler rows `<= 1200` is the ONLY working
  path — no IPS patch on either axis is needed for it, and the "108 copies"
  of the `Id > 1200` compare are 108 independent inlined
  `cmp w10,#0x4b0` encodings (save-side: 434 of the 932 `cmp #1200` sites
  sit beside the roster singleton, only 26 beside PersonData's), not copies
  of one choke-point function. That audit also found consumer-side id
  filters *independent* of the storage caps — `ClassData` rejects class id
  90 (25 sites, so only blank rows 93-99 are reusable), `Skill` treats ids
  240 and 255 as "none" (40 sites) — and located the patch copy of
  `WeaponData` a prior pass had declared absent (`patch4/INFO0.bin` entryId
  6 -> `fixed_data.bin`; slot 190 = Vajra-Mushti filled in place, see
  `override-layer-indexed-by-entry-id-not-semantic-filename.md` and
  `silent-loader-clamp-makes-appended-record-look-live.md`, both sourced
  here). The current-format layout was solved twice because
  a later pass never grepped the doc (`doc-self-cross-reference-before-
  fresh-disassembly.md`, 7th instance) and read a same-lineage editor fork
  covering only the old revision (`reference-tool-data-revision-mismatch.md`).
  **Environment/level geometry — the `.kldm` corpus is ~189 entries, not 29
  (2026-09-05).** The Monastery-hub/battle-map RE item was picked up for the
  first time: a fresh full-DATA0 `"MDLK0001"`-tag census (not a re-scan of
  the previously-documented 883-984 range) found 189 real hits at 5 header
  offsets spanning DATA0[883..2390] — 155 previously-undiscovered entries
  (929 MB) decode via the already-existing unmodified `parseG1MChain` to
  genuine environment/level-scale geometry (bboxes up to ~200,000 world
  units vs ~162 for a character mesh), refuting the "prop/decoration"
  characterization a first pass's 29-entry sample produced (see
  `detector-offset-generalized-from-partial-corpus-silently-skips-rest.md`,
  sourced here — even DATA0[978], the single largest `.kldm` entry, was
  inside the "documented" range but at a different real tag offset and was
  never exported). The same `MDLK0001` wrapper also turns out to carry a
  second payload kind (`"OC1G"` collision-primitive chains) that is
  **byte-identical to FE Warriors' already-solved `stage-collision.ts`
  G1CO format** and parses 2/4 sampled FE3H entries unmodified — a fresh
  worked instance of this project's own "container differs, codec/format
  doesn't" pattern applying one level deeper (a sub-payload inside a
  container, not just a top-level asset format). Also found a new,
  undocumented `"RIVER"` per-stage resource (10 instances, ~13.1 MB each)
  whose decoded floats show the structural signature of a real
  river/waterway spline (near-constant elevation, monotonic position,
  monotonically-decreasing width/arc-length field) — rendered from float
  plausibility alone, no external oracle checked. `detectKldmChainStart`
  fixed to scan for the tag instead of assuming a fixed offset, unit-tested
  (7 cases), and proven against 3 real entries as scoped `--only=` GLB
  exports (0 `gltf-transform validate` errors). Full-corpus regen
  deliberately deferred (disk/scope decision on a shared machine, not a
  research gap) — 5 new `docs/TODO.md` rows. See `docs/fe-threehouses.md`
  § "Environment/level geometry — the `.kldm` corpus is ~189 entries, not
  29".
- **Fire Emblem: Engage** — the account's **first Unity-engine title**
  (Unity 2020.3.18f1, not a Koei Tecmo engine — none of this project's
  KTGL/G1T/G1M knowledge applies). Unity Addressables `.bundle` → UnityPy
  (Python subprocess). **Textures**: 12,922 decoded
  (`tools/fe-engage/extract_unity_textures.py`) — the `.resS` resource-stream
  path needs explicit resolution, UnityPy doesn't auto-resolve it.
  **Meshes fully solved**: `tools/fe-engage/extract_unity_meshes.py`
  (UnityPy's own `MeshHandler`, resolving `SkinnedMeshRenderer`/
  `MeshFilter+MeshRenderer` + a per-bundle shared skeleton deduped by
  `PathID`) → GLB via a new `src/data/formats/unity-mesh-gltf.ts` (built on
  the same shared `gltf-builder.ts` the PlatinumGames/Koei Tecmo exporters
  use). 2,751 GLBs / 67,126 renderer instances, 0 decode errors, 0
  `gltf-transform validate` errors on every spot-checked sample. Two real
  bugs found and fixed along the way: **UnityPy's `MeshHandler` doesn't
  normalize `UNorm8`/`UNorm16` vertex-channel formats** — it applies the
  right struct type but hands back the raw fixed-point integer unscaled,
  so this game's `UNorm16` blend weights came back summing to 65535 instead
  of 1.0 (fixed by reading `m_VertexData.m_Channels[12].format` directly
  and dividing by 255/65535 — but *not* for `BlendIndices`, a real integer);
  and a **V8 hard string-length ceiling** (~512 MiB, `ERR_STRING_TOO_LONG`,
  unaffected by `--max-old-space-size`) hit on one whole-scene bundle
  (6,462 meshes in one Unity scene, `fe_scenes_hub_solanel`) whose JSON
  intermediate serialized past it — fixed by splitting into
  `<name>__partN.json` files under a conservative size estimate before
  serialization, each becoming its own GLB. The Unity (left-handed) → glTF
  (right-handed) coordinate conversion was **derived and numerically
  verified**, not assumed: mirror-X on positions/translations pairs with
  quaternion `(x,y,z,w) -> (x,-y,-z,w)`, confirmed by conjugating a
  rotation matrix by `diag(-1,1,1)` across random test rotations and
  checking it reproduces that exact formula (same conjugation generalizes
  to a full affine 4x4 for inverse-bind-matrix conversion); the
  compensating triangle-winding fix (swap the last two indices) was
  verified on real corpus data via a 500/500 face-normal-vs-vertex-normal
  agreement sweep. **Content census** (read-only, no-decode-required
  object-type survey across all 24,755 bundles,
  `tools/fe-engage/census_object_types.py`): found a real, mostly-tractable
  `TextAsset` corpus (5,029 files) — 93.6% are the `"MsgStdBn"`-magic
  dialogue container, 180 are plain, already-readable XML gamedata tables
  (`<Book><Sheet><Param>` spreadsheet-export shape, real column names), and
  143 are a small plaintext Lua-like battle-script DSL (`Include(...)`,
  `function Startup()...end`) needing zero decode work at all. Also found
  24,955 `AnimationClip` objects, initially misread as needing Unity's
  Avatar/HumanPose muscle retargeting math (wrong — see below).
  **`AnimationClip` — corrected, decoded, and shipped as a real pipeline
  stage (2026-09-06).** A follow-up census found the "needs retargeting"
  read was wrong: `m_MuscleClip.m_Clip` (the packed dense/streamed/constant
  curve container) carries every non-legacy clip's data regardless of
  Humanoid-vs-Generic rig, and a full-corpus check of
  `m_DeltaPose.m_DoFArray` (the actual muscle-DoF storage) found it
  all-zero across all 24,955 clips — 0 clips anywhere in this corpus use
  real muscle-space data. 16,123 non-empty clips all decode via an
  ordinary packed-curve read (`src/data/formats/unity-animation-clip.ts`,
  ported fresh from Perfare/AssetStudio's real C# source), and
  `genericBindings[].path` crc32 hashes resolve to real bone names via a
  corpus-wide hash table folded from every already-extracted mesh
  skeleton's own bone hierarchy (`unity-bone-path-hash.ts` — no per-clip
  skeleton pointer exists in the data, so one shared table stands in for
  per-clip pairing; verified against real data before writing any resolver
  code, see `docs/fe-engage.md`). A real pipeline stage
  (`tools/fe-engage/build-animations.ts` + `extract_animation_clips.py`)
  ships this, verified against a "container stores the same fact twice"
  cross-check (decoded root-motion curve endpoints exact-match the clip's
  own independent `m_StartX`/`m_StopX` fields). A full-corpus run was
  attempted and deliberately aborted mid-run after `df` showed the
  machine's real disk at 100% used with ~3.5GB free while the intermediate
  cache alone had already reached 1.3GB at 65% scanned — a real, measured
  disk-space constraint (not a pipeline defect); a smaller bounded
  production run (600 bundles, 180 clips, 0 errors, 97.0% bone-path
  resolution) is shipped instead, and the full run is a re-run away once
  disk space allows. See `docs/fe-engage.md` and
  `session-scratchpad-tmpfs-exhaustion.md`'s "the real project disk, not
  just tmpfs, can also be already full" extension.
  **MsgStdBn/MSBT dialogue-text container SOLVED (2026-09-02) — not a
  bespoke FE-specific format at all.** `"MsgStdBn"` is publicly-documented
  Nintendo "MSBT"/LibMessageStudio, a shared internal-library text format
  used across many first-party franchises for decades (Paper Mario, Animal
  Crossing, Zelda), not something bespoke to Fire Emblem — a real,
  actively-maintained reference implementation exists
  (`SunakazeKun/pymsb`) and its container-shape prose was independently
  re-verified against real FE Engage bytes (byte-exact header/section-size
  self-consistency across 11 sampled files, real legible English narrative
  text recovered from `after.bytes.bundle`'s epilogue table, labels and
  content cross-agreeing) before porting anything, rather than trusted
  outright — see `src/data/formats/msbt.ts` and `docs/fe-engage.md`. Ships
  the US English locale (336/4,706 files,
  `public/assets/fe-engage/switch/data/message_*.json`) — the other 7
  locales weren't extracted this pass (deliberately bounded scope on a
  large-corpus title, not a blocker). The embedded `0x000E`/`0x000F`
  control-tag *grammar* is solved (group/tagId/size header + raw payload);
  most of the 35 observed tag *kinds*' semantics are still unidentified
  (`fe-engage-msbt-tag-semantics`) — a handful were characterized directly
  from real payload content (length-prefixed UTF-16 strings: character
  name+mood inserts, item/asset-name inserts, a gendered-pronoun selector
  matching Alear's selectable gender, a zero-size player-name insert).
  Reusing this module's structural pattern (parse the container generically
  first, treat unidentified control tags as opaque-but-lossless data,
  extract real text before building any semantic tag decoder) should
  transfer directly to any other MSBT-using Nintendo title this account
  encounters. See `docs/fe-engage.md` and `docs/TODO.md`
  (`fe-engage-msgstdbn-locales`, `fe-engage-msbt-tag-semantics`,
  `fe-engage-animclip`, `fe-engage-texture-gap`, `fe-engage-xml-scripts`).
  Also: `tools/extract-romfs.ts`'s `hactool` invocations moved from a
  captured Node pipe to a real temp file after this title's ~180K-file
  RomFS listing reproducibly threw `ENOBUFS` through the pipe (a
  sandboxed-environment limit, not Node's own `maxBuffer`) — see
  `game-re-tooling/switch.md`.

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
  497 GLBs, 0 decode errors, 0 `gltf-validator` errors *and 0 warnings*
  across the whole batch after the skinning correction below.

  **G1M skinning — SOLVED (2026-08-23), shared by all three Koei Tecmo
  titles.** A SubMesh's `boneTableIndex` selects a bone palette (GM1G
  sub-array magic 6) and a vertex's `BoneIndex` attribute selects a *slot
  within that palette*, whose `{matrixId, clothId, boneId}` triple splits as:
  `matrixId` indexes the block's **`MM1G` inverse-bind-matrix palette**
  (`count(u32)` + `count` x 64-byte row-major 4x4 float matrices; the size
  invariant `12+4+count*64 == subsectionSize` holds 569/569 and 519/519 with
  zero deviation, and the matrices go into glTF `inverseBindMatrices`
  verbatim — a row-major row-vector matrix is bit-identical to a column-major
  column-vector one denoting the same transform); `boneId` names the bone
  (**mask off bit 31**, then a direct `bones[]` hit, else the `boneIndices[]`
  remap); `clothId` is a constant per-palette group tag. This supersedes two
  wrong verdicts that had stood for several passes across both games' docs —
  "`matrixId` is the GLOBAL skeleton bone index directly" and "`clothId`/
  `boneId` read as implausible `~0x8000xxxx` constants... most likely
  runtime-patched pointer/handle slots". Verified by a zero-deviation
  per-entry invariant, `world[boneId] x MM1G[matrixId] == identity`, holding
  for 108,510 of 117,842 Three Houses bindings; the 9,332 exceptions are
  precisely the `ONUN`/`VNUN`/`SNUN` (NUNO/NUNV/NUNS) cloth- and
  hair-physics bindings, whose vertices are stored in a bone-local space.
  The exporter now emits one glTF skin per bone palette (`joints[k]` = slot
  k's bone, `IBM[k]` = `MM1G[slot k's matrixId]`, so a raw `BoneIndex` value
  indexes `skin.joints` directly), with a whole-skeleton fallback skin for
  palettes that can't be expressed that way (12/2,841 3H primitives, all in
  `.kldm` prop chains). `pickPrimarySkeleton` also now selects the SM1G
  flagged `usesInternalBoneset` rather than "most bones".

  Why it survived so long: the old code used `matrixId` as the joint index
  *and* rebuilt each IBM as `inverse(world[joint])`, which composes to the
  identity for any joint whatsoever — so the bind-pose render reproduced the
  stored positions exactly and looked perfect for body geometry through
  multiple passes, a full validator sweep and real Playwright screenshots.
  Only bone-local cloth exposed it (Manuela's robes and Rhea's hair rendered
  heaped on the ground at `y ∈ [-13.8, 15.7]` while bodies reached `y=159`).
  Regression evidence: 93.95% / 97.20% / 100% of primitives bit-identical
  across the three games, and 642/642 + 336/336 of the moved ones now inside
  their own model's unchanged-geometry bbox (up from 53.7% / 50.9%). Lessons:
  `bind-pose-render-blind-to-joints-index-space-bug.md`,
  `stored-bind-matrix-palette-is-a-per-entry-identity-oracle.md`,
  `high-bit-set-field-is-flagged-index-not-pointer.md`,
  `bone-palette-may-bind-one-bone-twice-needs-proxy-joint-node.md`,
  `semantic-output-diff-with-unchanged-parts-as-reference-frame.md`,
  `undetermined-selection-may-be-immaterial-or-already-in-a-skipped-field.md`.
  **NUN-cloth driver-mesh control points and hierarchy now SOLVED too
  (2026-08-24)**, cross-referencing two independent GPL community tools
  (understanding-only, no code copied): Joschuka/Project-G1M (a C++ Noesis
  plugin) and the `three-houses-research-team/010-binary-templates` repo's
  `NUNO.bt`/`NUNV.bt`/`NUNS.bt`, which agree field-for-field. `ONUN`/`VNUN`/
  `SNUN` hold per-entry lists of control points (a driver bone's rest
  position) each paired with an influence record whose `P3` field is a
  parent-chain link — either another control point in the same entry or a
  sentinel meaning "attach to the entry's declared skeleton bone" — which
  the game turns into synthetic bones appended past the real skeleton and
  skins cloth/hair vertices to. Verified byte-exact against real FE3H data:
  Manuela's `ONUN` (NUNO3 sub-format) — 5 entries, 195 nodes, entry byte
  lengths summing to exactly 11,732 of 11,732 declared bytes, 0 slack — and
  a real `VNUN` (NUNV1) sample — 1 entry, 15 nodes, 864 of 864 declared
  bytes, 0 slack — both resolving into physically coherent parallel chains
  (parent-index links walking back by a constant stride to `-1` roots), not
  noise. `readNunSection` + helpers in `src/data/formats/g1m.ts`. Getting
  this working needed correcting a `chunkVersion`-field decode bug (see
  `ascii-digit-version-field-needs-digit-weighted-decode.md` — the field
  looks like ASCII digits but needs a digit-weighted decode, not a literal
  string read), caught only by the byte-exact entry-length self-consistency
  check, not by eyeballing plausible-looking decoded floats. NUNO1/NUNS1 are
  ported from the same two sources but not independently byte-verified
  (FE3H's own corpus only exercises NUNO3/NUNV1 for `ONUN`/`VNUN`, and a
  structurally-filtered scan found no genuine `SNUN` section — every raw
  `"SNUN"` byte match was a false positive, see
  `short-magic-hit-in-high-entropy-region-needs-falsification.md`); NUNO4/
  NUNO5 are unported (not observed in FE3H, and both sources' own LOD/
  subset-matching logic for them is only partially explained).

  **NUN procedural-cloth GEOMETRY now wired into `g1m-gltf.ts` and the
  hair-length content gap SOLVED (2026-09-01, `re-oracle`)** — a prior
  claim here ("today's shipped GLBs are already correct at rest pose via
  the `MM1G` fix") was WRONG for cloth submeshes and was itself the gap:
  a mesh-group entry's previously-skipped `clothType`/`externalId` fields
  (now parsed in `g1m.ts`) mark `clothType==1` submeshes whose vertex
  attributes are ALL repurposed as cloth-solver input (Position = CP
  weights, BoneWeight/Color = center-of-mass weights, BoneIndex/PSize/
  Fog/UV(u8x4) = four CP index sets, Normal = basis+depth) — the old
  exporter read weights as positions and collapsed every NUN strand onto
  its anchor (Lysithea/Dorothea/fByleth "short hair", Sothis's missing
  cascade, Manuela's missing cape; 170/569 packs, 1,168 lod-0 submeshes,
  +14 packs/132 submeshes of `clothType==2` whose positions are real but
  in a physics joint's frame, vertex idx/3 -> palette `clothId`). A static
  rest-pose bake of Project-G1M's evaluation now ships (`opts.bakeCloth`,
  FE3H-gated; CP rest position = `world[entryParentBone] x nodePos`,
  ABSOLUTE in the parent frame — Project-G1M's own chained-bone algebra
  provably cancels to the same thing), verified by render against the
  user's in-game screenshots for all gap characters + max |delta| ~1e-5
  vs the probe implementation + clean `gltf-transform validate`. Sibling
  `_M1G` PACK sections (188/569 packs) are complete runtime-VARIANT
  models, not LODs (fByleth Enlightened head, Dorothea pre-timeskip
  head), now exported as `pack_<i>_s<sec>` GLBs. Same investigation also
  found rigid G1M vertex joint indices are palette-slot x3 corpus-wide
  (1,369/1,369 census; `jointMap[3*j]` in Project-G1M) — fixed in the
  shared exporter, all three titles' corpora need regeneration. Residuals
  in `docs/TODO.md` rows `fe3h-mesh-corpus-regen`,
  `g1m-joint-index-x3-sibling-regen`,
  `fe3h-meshgroup-unknown-entries-parse`; full mechanism writeup in
  `docs/fe-threehouses.md` § "NUN procedural cloth (clothType 1/2)".
  Lessons: `cloth-submesh-repurposes-vertex-attributes.md`,
  `prescaled-joint-indices-divisibility-census.md`.

  **Runtime physics
  parameters (stiffness/damping/gravity) are now a settled negative, not an
  open search** — three further passes (two `re-codebreaker` escalations
  plus follow-ups) exhaustively worked every candidate native source
  (`RIGB` = a different system, KTGL's RealtimeRig pose-operator, not
  cloth; `SWGQ`/`QGWS` swing-data is real and fully decoded but has zero
  traced native consumer; `SOFT`/`HAIR`/`SNUN` are confirmed **dead
  shared-KTGL engine code** in this title — zero occurrences across the
  base game, both update patches, and both DLC archives; and finally the
  real per-frame NUN-cloth solver chain itself — factory, instance
  builder, FP-dense solver module, all disassembled and struct-mapped — is
  **also confirmed unreachable dead code**: its own gating call argument
  is a hardcoded literal `0` at its one and only call site, in both the
  base game and a later update build, with no indirect/vtable path around
  it (see `gating-argument-may-be-a-compile-time-constant-not-data.md` for
  the generalizable technique this surfaced — a mechanism surviving three
  independent re-verifications of its own internals is not the same claim
  as it executing at runtime). The viewer's spring-bone approximation
  (`fe3h-cloth-physics-approximation`) remains the only real output; no
  further native-code avenue is known to exist. See
  `docs/fe-threehouses.md` § "NUN-cloth driver meshes" and its later
  "`re-codebreaker` escalation result" / "the whole factory chain ...
  UNREACHABLE dead code" sections, and `docs/TODO.md` row
  `g1m-nun-cloth`.

  Separately, the same cross-reference pass checked **koeipy**
  (`github.com/3096/koeipy`, GPL-3.0, a Python toolkit for this engine
  family) for two other potential gaps: its `kt_gz.py` independently
  validates this project's own `ktGzDecompress` byte-for-byte (no new
  finding, already solved here), and its `kt_arc.py`/`inject_data.py`/
  `pack_data.py`/`pack_info.py`/`pack_bin.py` do **not** write a
  `DATA0.bin`/`DATA1.bin`-shaped pair (they target a simpler, different
  single-file archive shape) and ship no working end-to-end modify+repack
  demo for any gamedata table — a real `DATA0`/`DATA1` write path remains
  a genuine, unbuilt gap (relevant to `docs/TODO.md`'s
  `fe3h-custom-character-injection`).

  **Audio fully solved, 30,165 tracks** — an earlier
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
  instead. **Animation fully solved, 34 GLBs / 674 clips.** Same premise
  correction and shared decoder as Three Houses above: real format is
  **G2A** (`_A2G`), not the community/brief-named "G1A" (`_A1G`, ~0 real
  hits corpuswide) — `src/data/formats/g2a.ts` + `g2a-gltf.ts`, ported from
  `Joschuka/fmt_g1m`'s Noesis plugin (also confirms these exact games as
  real G2A consumers, not just template coverage). Version-gated bitfield
  widths: this game's clips report version string `"0300"` (10-bit
  boneID/18-bit offset), vs. Three Houses' `"0500"` (8-bit boneID/20-bit
  offset + extra reserved field) — same codec, different quantization
  width per title. Clips live in wholly separate files, `nx/action/
  motion/*.bin.gz`, matched to `nx/action/model/*.bin.gz` by identical
  filename — unlike Three Houses' embedded-in-mesh-pack container. Bone
  resolution required a previously-unparsed `g1m.ts` skeleton field,
  `bone_indices[boneTableCount]` (an i16 remap table, documented in the
  community `.bt` template but never read by this project before): G2A's
  `boneId` only resolves in-range 100% of the time through this remap
  table vs. ~63% as a direct `bones[]` index — see
  `community-format-name-mismatches-real-magic.md` for the general
  "check for an established remap-table indirection in the same format
  first" lesson this produced. Open/unconfirmed: rotation quaternions are
  exported without the reference Noesis decoder's `NoeQuat(x).transpose()`
  step (closed-source semantics, no posed-render oracle yet) — see
  `docs/TODO.md` `g2a-quat-transpose`. **Gamedata: container-level solved,
  field semantics open.** Two new shared, reusable table formats found
  from scratch (no community docs exist for this game's gamedata layout —
  confirmed by an empty WebSearch): `src/data/formats/fixed-record-table.ts`
  (a minimal `<u32 count, u32 stride, u32, u32>` header + flat
  `count x stride`-byte record array — a
  previously-undocumented format, confirmed on 15 files via strict size
  accounting and, decisively, a monotonic leading-u16-ID +1 sequence census,
  e.g. `ModelChrParam.bin`: 348/349 consecutive IDs 100-470) and
  `src/data/formats/xl-table.ts` (generalizes `event-point.ts`'s
  previously-single-instance "XL"-magic table into a whole family reused
  throughout `common/common/{initdata,scenario_initdata}.bin`'s "pack"
  slots and several standalone `common/battle/alg/`/`common/gallery/`
  files — found via the same raw-magic-scan-and-validate technique already
  used for this game's G1T/G1M/G2A/KTSS, so the outer pack layer never
  needs solving). See `identical-header-shape-two-container-formats.md` for
  the pitfall this pass's header census produced (the same leading 16-byte
  shape ambiguates the two container formats; strict size-accounting is
  what discriminates them). `ModelChrParam.bin`'s 350-record, ID-100-470
  registry is the strongest single per-character-table candidate found —
  looks like physical/collision model parameters (scale, capsule
  dimensions), not classic RPG base stats, plausible for this game's
  Musou/action combat model rather than FE's tactical one. Field-by-field
  semantics remain open for every table (`docs/TODO.md` `few-gamedata`).
  `adventure_initdata.bin` is a known big-endian outlier of the same pack
  container (not yet covered by the LE-only scanner). **Follow-up pass**:
  **the model-ID name oracle is SOLVED** — after four passes concluded "no
  external ID->name oracle exists for this game" (010-template/cheat-table/
  save-editor WebSearches all empty), a fifth found it *inside the game's own
  `main` executable*: a flat 13,133-entry resource-path registry
  (`{u64 pathPtr, u64 handleSlot, u64 flags}`, 24-byte stride, at vaddr
  `0x9d9e30`) naming every loadable file in numeric-resource-ID order. Model
  ID `N` = registry entry `1130 + N`; that base is **derived, not
  hardcoded** — `findModelIdBase` searches every candidate and requires the
  placeholder-sentinel triple (found a pass earlier from bytes alone) to
  agree with the registry's `not_exists_file.bin.gz` entries for all 350
  `ModelChrParam` records, 0 FP / 0 FN, uniquely maximal over a +/-6 shift
  sweep, with an independent RomFS-only cross-check via
  `nx/effect/NNN_<Name>.bin.gz` filenames (32/32 at a constant delta of 99).
  New shared code: `src/data/formats/nso.ts` (NSO0 + hand-written LZ4-block
  decoder) and `kt-resource-registry.ts`; `tools/extract-romfs.ts` now dumps
  the ExeFS unconditionally. All 350 `ModelChrParam` records, 160/300 real
  `ModelWpnParam` records, `ModelDItmParam` 37/37 and `ModelEvntParam` 46/50
  are now named; `ModelPackInfo.bin` fell out fully decoded (750 records =
  one per global model ID, with a host-pack field and a 4-entry redirect
  that exactly explains `ModelEvntParam`'s only 4 disagreements — 0
  unexplained residue). `id=132 = C_Evildragon` promoted hypothesis ->
  CONFIRMED, vindicating the earlier cross-table corroboration
  (`cross-table-outlier-corroboration-without-external-oracle.md`).
  `ModelWpnParam.bin` was already confirmed as a per-weapon, not
  per-character, catalog via two named-legendary-weapon string matches —
  now cross-checked by name (`149_05_raijinsword_aura` sits on
  `W_Sword_V_ForRyouma`, Raijinto being Ryoma's katana;
  `149_04_fujin_arrow` on `W_Arrow_V_ForTakumi`). Several pass-2/3 semantic
  guesses were corrected by the names: `col2==21` is the manakete
  (`*_Mamukute*`) transformed form, 14/14 pure, not a generic-mob category;
  `col1==1` is the `O_Soldier_*` rank-and-file flag, 31/31 and 0/222; the
  weapon table's `col1==8` block is the `W_SP_*` character-unique action-prop
  family, not a monster/boss block. Two new pitfalls came out of it —
  `executable-resource-path-registry-names-asset-ids.md` and
  `pointer-array-stride-signature-needs-content-plausibility.md` — plus
  `game-re-tooling/switch.md`. Still open: the columns that are physically
  characterised but not stat-named (`col3` torso-capsule height, ratio 0.727
  +/- 0.061 against real G1M mesh heights; `col20` r=+0.59; `col9` tracks
  mount/flight class), and the non-model tables (`UnitParamData`,
  `CommonExd`, `alg_*`) whose ID spaces this registry does not name.
  Separately, **`common/battle/stage/area###.gz`'s `"FTHD"`-tagged slot-4
  payload and the sibling `gimmick###.bin.gz` files are now both decoded**
  — a fixed-capacity per-stage AREA/zone table and a new 12-byte-header +
  fixed 200-record table respectively (`src/data/formats/stage-area.ts`,
  `stage-gimmick.ts`), closing two of the `few-stage-scenario` TODO item's
  named leads (0 parse errors across all 20 stages for both); neither
  turned out to carry victory/loss objective or camera-scripting data.
  **The `few-stage-scenario` item is now fully closed**: `common/battle/
  scenario/{sn,snHST,snPTN,snSTG,snSUB}###.bin.gz` (159 files, previously
  "0 readable strings, proprietary control data") is the battle scenario /
  mission-event script — a 9-section container whose section 8 holds 8,098
  events (across the whole corpus), each gated by a condition tree
  (AND/OR + leaf tests) and driving a command list, both delimited by two
  arity tables solved as a corpus-wide constraint-satisfaction problem
  (`src/data/formats/battle-scenario.ts`). This *is* the victory/loss
  objective and camera-scripting data the item was chasing: command `880`
  sets per-battle objective state and `1780` ends a sub-mission with a
  success/failure result code (cross-checked against real text in the
  paired `snstr*.bin` "XL" tables), and `1540`/`1650`/the 7000-7300 block
  are camera-move/cutscene-staging commands (the `1540` world-space
  coordinate cross-check against the already-shipped `EventPoint` decoder
  agrees to <0.1%). Originated as an unfinished `re-codebreaker` (Opus)
  escalation output that was found uncommitted, untested, and unverified;
  a follow-up pass independently re-derived every headline number from the
  real 159-file corpus from scratch (not trusted from the module doc),
  added 19 unit tests, and wired it into the pipeline
  (`scenario_events.json`). One reusable pitfall surfaced along the way —
  see `prefixed-sibling-family-shares-numeric-id-space.md`: this
  directory's five prefix families (`sn`/`snHST`/`snPTN`/`snSTG`/`snSUB`)
  share one bare numeric id space, and each has its own same-prefixed
  `snstr*` text companion, not one shared per-number file. Residual open
  work (message-text-to-event linkage, ~137 command ids /54 condition ids
  left semantically unnamed) is tracked as `few-stage-scenario-text`. See
  `docs/fe-warriors.md` "Levels / scenarios" and "Text / gamedata tables".
  The sibling `few-stage-containers` item is now **mostly closed** too:
  `nx/stage/info/S###-Info.bin.gz` is the per-stage **navigation data** — a
  256x256 1-bit walkable bitmap at 256 world units/cell plus a 128x128
  coarse grid whose cells carry a rectangular sector/region partition at 512
  units/cell (`src/data/formats/stage-info.ts`, 19/19 files, 0 errors,
  shipped as `stage_navgrids.json` + a PNG per stage) — and
  `nx/stage/g1co/S###-G1co.bin.gz` is a variable-length **collision
  primitive** list (box/sphere/capsule, `"OC1G"` = `"G1CO"` reversed,
  `stage-collision.ts`, 271 shapes, byte-exact chain-to-EOF on all 19
  files). Both were verified purely against the project's *own* earlier
  output — 53/54 already-decoded `EventPoint` markers land on walkable cells
  (vs a ~17% baseline; transposing drops it to chance) and 97.7% of 19,682
  `ObjInfo` placements fall inside the sector partition. `nx/stage/local/`
  and `common/StageNature.bin.gz` are **confirmed texture bundles only**
  (magic census finds nothing but `GT1G`; `local/`'s 19 same-size files hold
  just 2 distinct contents, so they are not per-stage data at all) and need
  no extractor. Residual open work: `info/` slot 2's two near-empty
  51,200-byte blocks, slot 4's f32 parameter block and slot 3's 128-bit-mask
  tail, and what the collision shapes / 70 `"_COK0100"` quads attach to.
  Four pitfalls came out of this pass —
  `first-slot-magic-names-the-whole-container.md` (the `"OFNI"` magic that
  named a 128-byte near-constant descriptor, not the file),
  `bitmap-bit-order-from-transition-isotropy.md`,
  `redundant-offset-field-poisoned-chain-by-length.md` (this game's "pack"
  container poisons `cumulativeEnd` two different ways) and
  `per-instance-file-set-may-be-duplicate-blobs.md`. See
  `docs/fe-warriors.md` "`info/` — CONFIRMED, decoded, shipped" and the
  three sections following it.

  **Real-time combat-resolution math — SOLVED (2026-09-07, `re-codebreaker`)**:
  `damage = max(0, ATK - DEF)`, capped at 999 (`main+0xdbac8`/`0xdbacc` sub+bic
  idiom, `main+0xdbd9c` clamp) — the classic subtractive mainline-FE shape.
  A real gameplay LCG RNG (`0x41C64E6D`/`0x3039`, two independent seed
  streams) IS wired into combat: hit rate resolves via a 2RN-averaged "True
  Hit" roll, crit rate via a 1RN roll that triples damage on success. This is
  a genuinely different formula shape from sibling Three Hopes below, whose
  `ComputeDamage` is a ratio/divide with **no** RNG at all (that LCG constant
  is completely absent from its binary) — despite both being the same Koei
  Tecmo Musou engine family, investigated the same project-week; see
  `engine-family-shared-decoder-not-shared-container.md`, generalized here
  from container formats to gameplay-math formulas. `src/data/formats/
  battle-formula-few.ts` (pure functions, mirroring FE3H's `battle-formula.ts`
  pattern). Open: 5 of 9 `GetParam` stat ids unnamed, and the separately-
  confirmed posture/guard-break gauge's (`unit+0x198`, capped at 4000) fill/
  drain schedule — see `docs/fe-warriors.md` § "Real-time combat-resolution
  math — SOLVED" and `docs/TODO.md`'s `few-combat-math`/`few-guard-break` rows.

  **The generic KT-table container** (magic `0x134c58`, `tableSize`/
  `flagSize`/`numEntries`/`pointerSize`/`headerSize` header — first documented
  in `src/data/formats/msgdata.ts` for FE Three Houses' *text* archives, where
  `pointerSize` selects a string-pointer table) is reused here for pure
  **numeric** fixed-stride records with no string pointers at all —
  `common/battle/alg/alg_unitdata.bin`/`alg_act_comb.bin`/`alg_pur_comb.bin`
  (AI-tuning-shaped constants, not yet semantically decoded). Generalization:
  `pointerSize` doubles as record stride whenever the payload isn't text.

- **FE3H: the loader's own `_M1G` parse grammar, and the first in-game
  contact of pipeline-GENERATED G1M geometry (2026-09-02).** The engine's
  block parser (`main+0xa33bd0`, v1.2.0, image offset = vaddr) is a
  sequential stream reader: GM1G array-section `size` fields are never used
  to seek, an unknown section type is not skipped, and each handler's false
  return frees the model and returns NULL, which the caller
  (`main+0x4e018c`, LR `0x4e0180`) dereferences unguarded — the `<BackRead>`
  VA-0x0 crash signature. Handler table (types 1..9 via `0x188abf0`) with
  addresses and per-record consumption is in `docs/fe-threehouses.md`
  § "REVIEWFIX PACK crash ROOT-CAUSED". Two grammar facts the project's
  reader had wrong: a submesh is `0x24` bytes + `[+0x20]` × 20-byte draw
  ranges (`g1m.ts`'s `unknown5`, = 1 in 12,637/12,637 native; the importer
  wrote 0 and every generated PACK crashed on first load), and an empty
  Socket section is 16 bytes (`{count, 0x100}` head), not 12. Fixed in
  `gltf-g1m.ts`/`g1m-writer.ts`; `fe3h-pack-lint.ts`'s
  `g1m-engine-parse-walk` rule replays the disassembled grammar (569/569
  native PACKs pass, every pre-fix pipeline PACK fails) and is now the gate
  before staging anything. The crash had been mis-attributed for a day to
  the DLC-archive mod that carried one of the PACKs (its AOC load path, then
  its slot 19) — see `live-ab-isolation-names-carrier-not-mechanism.md` and
  `unknown-constant-field-is-engine-grammar-load-bearing.md`, both sourced
  here. Live re-test of the rebuilt PACKs still pending.

- **FE3H class + creature combat motion containers** (2026-09-03) — where
  FE3H keeps body/combat animation, which several prior passes had looked
  for in the character PACKs and not found. Two separate subsystems, both
  in `nx/action/motion/`, both using one container shape:
  - **class motion**: `DATA0[4622..4632]`, ten of eleven named by
    `patch4/INFO0.bin` (`KB_L_100/200/300/500/600_PACK.bin`, three `_R`
    mounted variants, `BC_PACK.bin`; 4627/4631 not overridden there).
  - **creature motion**: `DATA0[4253..4273]`, 21 archives, 34-143-bone
    rigs; `DATA0[4271]` is byte-identical (3 bytes aside) to
    `patch3/nx/action/motion/KB_M18_0.bin.gz`.

  Container (confirmed, all 11 class packs): outer is the generic pack in
  `xl-table.ts` **with its documented last-slot-sentinel caveat**; slot 0 is
  a `u32[]` motion-set id table with exactly one id per remaining slot
  (`len == 4*(slotCount-1)`, 0 deviations), slots 1..N are KT_GZ member
  archives. A decompressed member is a 17-slot pack: slots 0-14 per-clip
  metadata (undecoded), **slot 15 a nested pack, one `_A2G` clip per slot**,
  slot 16 a nested pack of 1-track/boneId-0 camera tracks. All clips are G2A
  `"0500"` at 60 fps. **FE3H and Three Hopes body-motion clips are
  set-identical on a 56-bone core id set** (`KB_L_100` member 1 vs. seven
  ported Shez clips: shared 56, only-either 0; all 56 resolve on Byleth's
  `DATA0[3121]` `boneIndices`) — the sharpest confirmation yet of the shared
  cross-game global bone namespace. A structurally faithful splice is built
  and verified (60/60 sibling members and 16/16 metadata slots
  byte-identical, 19/19 untouched donor clips byte-identical). **Open:** what
  binds a class to a motion-set id — no field in any section of any of the
  33 `nx/data/fixed_*.bin` tables carries it (per-field census against the
  real 223-id set), and the `ClassData.male/femaleAssetId` candidate is
  refuted (see `numeric-range-overlap-is-not-an-id-binding.md`, sourced
  here). Next step is an executable trace near `main+0x3E480`. Full spec +
  paths-tried: `docs/fe3h-modding.md` § "Where FE3H keeps class combat
  motion".

- **glTF -> KT-engine import, donor-independent** (2026-09-03) —
  `src/data/formats/gltf-g1m-fresh.ts` builds a G1M skeleton directly from a
  glTF's own node/skin graph when its bones match no known donor
  (`classifyGltfAgainstDonor` + `buildG1MFromGltfAuto`/
  `buildFe3hPackFromGltfAuto` dispatch; the donor-matching path is
  unchanged), and `src/data/formats/gltf-g2a.ts` resamples/encodes a glTF
  animation as a G2A clip (LINEAR/STEP/CUBICSPLINE, any of the three
  sub-versions). Tested against a real cross-project asset: Drakengard 3's
  Zero (`flower`) -> an FE3H PACK on Byleth's `DATA0[3121]` donor, 0 lint
  issues, 173 bones, every unrelated donor slot byte-identical.

- **FE Warriors (2017) as a glTF-import TARGET — Milestone 6 of
  `docs/model-import-pipeline.md` (2026-09-03), offline-verified only.**
  The FE Warriors "pack" is byte-for-byte FE3H's PACK (`u32 count + count x
  {ptr,size}`; 506/506 native packs rebuild identically — the older
  `fe-warriors-pack.ts` framing was 4 bytes late). `src/data/formats/
  gltf-pack-target.ts` (`buildPackFromGltf(target, donor, glb)`,
  `PACK_TARGETS.fe3h` / `['fe-warriors']`) plus `few-pack-lint.ts` (loader
  rules from the FE Warriors disassembly: fixed 260-byte `FM1G` read, slot
  table `{0,3..17}`, 20000-band cloth ids — the two live crash classes the
  `mods/fe-warriors/BylethHijack/` splices hit, reproduced offline; 0 fails
  on 436/436 native packs). **Multi-block hero packs** (57/436, every playable
  hero: skeleton-only slot 0 with the 200-305-bone rig, one self-contained
  `_M1G` per costume part in slots 3..17 with a 1-bone stub SM1G and
  `0x80000000|id` bind words against the canonical rig, a slot-18 costume
  registry of `0xff`-terminated part-id lists where part `p` = slot `p+3`)
  import per part via `gltf-g1m-parts.ts` (`BlockAssemblyOptions`: donor-
  cloned mesh-entry table, donor bind-word encoding, NUN-cloth submesh
  passthrough, donor `MM1G` row reuse — see
  `reuse-shared-palette-rows-for-byte-identical-reserialization.md`).
  Oracle: `C_Girl.bin.gz` (Lianna) whole-pack round trip, 0 lint issues,
  every non-rebuilt slot and every part's SM1G/MM1G/materials/mesh entries
  byte-identical, positions/UVs exact. The registry's "`01`-terminated"
  description was a data-value-mistaken-for-terminator error — sourced
  `list-final-byte-is-a-data-value-not-a-terminator.md`. Not yet loaded in
  Ryujinx (`docs/TODO.md` `few-pack-import-live-test`).

## Partially solved

- **Fire Emblem Warriors: Three Hopes (2022)**, `few-threehopes` — LINKDATA
  container format **fully confirmed** (5,310/5,310 non-empty entries decode
  across all 19 archives): `src/data/formats/linkdata.ts`. Two per-entry
  payload encodings (raw vs. size-prefixed zlib chunk stream) selected by
  the `unpacked_size` field. **G1T/G1M/KTSR/G2A are not inside LINKDATA at
  all** — a full census of every decoded LINKDATA entry found zero hits for
  any of them; textures, meshes, audio, and animation all instead live
  behind `File/CMN/Asset/FDataPackage/Master/`. **That wrapper is now fully
  solved: it is the Koei Tecmo KTGL **RDB resource directory**
  (`root.rdb`+`root.rdx`, `system.rdb`+`system.rdx`; `_DRK0000` header,
  `IDRK0000` records), `src/data/formats/kt-rdb.ts` +
  `tools/shared/kt-rdb-source.ts` — CONFIRMED byte-exact, all five
  redundant fields agreeing between directory entry and in-package record
  header across **161,563/161,563** records, 0 deviations, and independently
  corroborated by the executable's own strings (`root.rdb`, `IDRK0000`,
  `"%s0x%08x.fdata"`). This is an **engine-family format, not a per-game
  one** — expect it in other KTGL titles (Nioh, Dynasty Warriors, Atelier).
  **Solving it overturned the previous "the wrapper doesn't need
  reverse-engineering, the magic scan finds everything" position, which had
  silently capped every stage's corpus**: 54.5% of the game's 166,571
  resources are zlib-compressed (chunked zlib, `u32 len` + ≤0x4000 member)
  and carry no magic, so the scan saw 198 files' worth of G1M where the
  directory lists **6,923**, and 1,675 animation clips where it lists
  **5,152** — see `compressed-container-members-invisible-to-magic-scan.md`.
  The directory also names all 33 resource types by sampling payload magics,
  and shows 304 packages referenced but not shipped (4,980 records, 365 MB,
  all one type — DLC/stripped content, no G1M/G2A/G1T affected). A second,
  easy-to-miss member class also lives here: `Master/data/*.file`, 28 large
  loose bulk-resource blobs under a different filename convention, reached
  through the same directory via an `external` flag.
  **Text (LANG, 11 languages not 12), textures, meshes, and audio are all
  fully extracted, full corpus, 0 decode errors**: 796,628 UTF-8 strings
  (`kt-text.ts`, NUL-delimited-string scan, sidesteps an unresolved
  off-by-one in the entry offset table); 2,463 real textures (`g1t.ts`
  unmodified, after fixing a Morton-deswizzle block-size bug this game's
  content newly exercised — see `byte-granular-deswizzle-of-block-
  compressed-data.md`); 181 mesh GLBs / 882 G1M containers (`g1m.ts`/
  `g1m-gltf.ts` unmodified); 97,286 Ogg Opus tracks / 27 audio banks
  (`ktsr.ts`/`ogg-opus.ts` unmodified, `codecId=9` matching Three Houses'
  Opus convention), **plus a second, structurally distinct audio type: RDB
  `0xbbd39f2d`/`ASRS`, 243 resources, 421 MB, 243/243 compressed — 13,679
  DSP-ADPCM WAV tracks shipped, 0 errors.** Wrapper-stripping alone did
  **not** hand this to the already-working `ktsr.ts` unmodified, despite an
  earlier pass's prediction that it would — the bytes past the wrapper are
  a genuine `"KTSR"`-magic-sharing but structurally different sub-format
  (Koei Tecmo's "as"/audio-set bank vs. the already-solved "ktsl2stbin"
  shape: different chunk-type constants, no literal `"KTSS"` anywhere,
  audio reached via a double pointer indirection) — see
  `sibling-magic-may-be-same-struct-zeroed-field.md`'s neighbour case and
  `magic-scan-can-substitute-for-container-reverse-engineering.md` for why
  a matching magic + a plausible size field is not proof of a known
  sub-format. Cracked by a `re-codebreaker` escalation that checked
  `vgmstream`'s own `src/meta/ktsr.c` source (not just its CLI) — a broader
  prior-art source than the 010-template + fan-Python-script pair this
  project's existing `ktsr.ts` support was built from — and verified
  byte-exact against `vgmstream-cli` across the full corpus (13,679/13,679
  streams, 629,449,167 samples, 0 mismatches) before handing back
  `src/data/formats/asrs-ktsr.ts`, which reuses `gc-adpcm.ts`'s
  `decodeChannel()` unmodified (no new codec code). 216/243 banks are
  purely internal (this shipped content); the other 27 are purely
  external, each just a name + byte-offset reference into an already-
  shipped TSRS track (a free name oracle for the existing 97,286-track
  corpus, not yet joined — see `few3h-tsrs-naming-via-asrs` in
  `docs/TODO.md`). Also surfaced a likely sibling bug: Three Houses'
  `ktgcadpcm.ts` (a different DSP-ADPCM container) appears to swap its DSP
  header's `numSamples`/`numNibbles` field labels, needing a
  sample-truncating clamp as a workaround — flagged, not yet fixed (see
  `fe3h-ktgcadpcm-field-swap`). **Animation: BOTH formats decoded and
  shipped — 5,152/5,152 of the RDB's animation resources, 112 GLBs,
  313,854/313,956 tracks resolved (99.97%)**, sourced through the RDB.
  `g2a-gltf.ts` is unmodified but **`g2a.ts` needed a real fix**: version
  `"0400"` is a genuine third variant (OLD 10-bit bone-ID bitfield, NEW
  32-byte header), not the fall-through to `"0300"` previously documented —
  the old reading started every spline 4 bytes early, overran 110/4,569
  blocks and shifted every `boneId` one table slot; confirmed by a 4-way
  header-size × bitfield-width test scoring 4,569/4,569 clean on exactly
  one combination (see
  `version-flag-conflates-independent-format-traits.md`). Both sibling
  games' output is provably unchanged. The container still gives **no
  per-character pairing**, but per-clip best-fit skeleton selection over
  the RDB's **211** distinct `boneIndices` topologies (vs the 13 a magic
  scan could reach; largest rig 236 bones, a strict superset of the
  124-bone playable one) takes the original 1,675-clip population from
  88.35% to **100.00%** track resolution.

  **G1A — the other 583, now solved (and unique to this title among the
  three).** `_A1G` v`"2400"`, `src/data/formats/g1a.ts` + `g1a-gltf.ts`, a
  plain-f32 cubic-segment ancestor of G2A rather than a quantized one. The
  community `fmt_g1m` plugin does have a `processG1A`, but it is wrong in
  two ways real data caught: the header `fileSize` is in **16-byte units**
  (583/583 vs 0/583 read as bytes — the reference parses it and then never
  uses it, so nothing there could catch it,
  `reference-tool-field-never-consumed-by-its-own-importer.md`), and its
  opcode table is missing `0x66`, which is **39% of the corpus and not a
  bone track at all but a camera** (eye/interest/roll/FOV,
  `unknown-opcode-may-select-a-different-resource-kind.md`). Per-opcode
  component counts were pinned by whole-section union tiling with 0 gaps
  and **0 trailing slack**, the only invariant that survives the format's
  shared/deduplicated data slots and its 16-byte alignment
  (`union-tiling-beats-per-record-offset-chaining.md`). The 583 split
  227 camera / 356 skeletal, a partition three unrelated signals agree on
  exactly. **The skeletal 356 are the only clips in this game with a real
  model pairing** — each shares an `.fdata` with a G1M, and narrowing that
  package membership by skeleton topology names **exactly one model for
  213 of them**, at most four for 271. Verification: 583/583 parse, 0
  non-finite across 2,100,225 samples, 0 non-unit quaternions across
  247,390 rotation samples, and — using the now-known-correct co-located
  rig — 81.6% of position tracks reproduce their bone's bind-pose
  translation exactly, confirming the tracks are absolute local TRS.
  **KTID — the engine's name hash — SOLVED and code-confirmed**
  (`src/data/formats/ktid.ts`): `ktid(s) = Σ s[i]·31^(i+1) mod 2^32`, chars
  read **signed**, traced to the inlined loop at `main+0x75D574` (and
  `+0x76DC08`). Every RDB `fileId`/`typeId`, every `KOD` class and property
  key, and every `…ObjectNameHash` value is this hash of a plain string. The
  anchor corpus came from the executable's own property-registration
  jump table (`main+0x6A572C`), whose every case loads an 8-byte
  `{tag|count, nameKtid}` constant next to the name string — 8,037 cells,
  2,756 distinct anchors, **2,756/2,756 reproduce, 0 mismatches**, lengths
  2–65. Method writeup: `game-re-method/name-hash-recovery.md`.
  **`KOD` (`_DOK0000`) fully decoded** (`src/data/formats/kt-kod.ts`):
  4,952/4,952 resources walk end to end, **560,408/560,408 blocks tile their
  value section with 0 slack**, ten element-type tags fitted by least squares
  over a whole-corpus size invariant. Note it interleaves two block magics —
  `IDOK0000` objects and `RDOK0000` (75,158 blocks, same record shape plus
  one header word); a walker that knows only `IDOK` truncates on 320 files
  while looking healthy on the other 4,632
  (`block-chain-walk-stops-at-unknown-sibling-block-magic.md`). What the
  hash bought: **21 real resource names** (all hardcoded bootstrap object
  DBs, e.g. `Field_Common.character.level.kidssingletondb` — which pins the
  convention: a resource is named by a **bare filename with extension, no
  directory path**), **3,187/3,354 (95.0%)** of `KOD` property names
  resolved to plaintext over 10.5 M occurrences, and a **188-edge resource
  dependency graph**, every edge type-homogeneous
  (`KTGLModelDataResourceHash`→G1M 3,654/3,654, `KTGLTexContextResourceHash`
  →G1T 52,464/52,464, `KTGLRigBinResourceHash`→RIGB 2,094/2,094, …). Class
  `0xD40B3C8F` is the model bundle: one object ties a G1M to its rig,
  collision, cloth, shader bind tables and LOD distances across 47 readable
  properties.
  **Reasoned negative — model/animation names are not recoverable from
  shipped data.** Not "not yet": `ktid` is 32-bit and integer-linear, so
  `ktid(P+T) = ktid(P) + 31^|P|·ktid(T)` makes any unknown prefix a free
  32-bit parameter; a positional-difference scan over the ID set alone
  (chance rate 0.011 pairs, observed 182/178/148/129 at positions
  15/26/27/30 for the 6,923 G1M ids) measures model names at 16–36
  characters; and a 710,924-string × 31-extension sweep of *all* shipped
  data against all 166,571 `fileId`s hit only the chance rate. Class and
  type names likewise resolve 0/866 and 0/22. Only an external filename list
  can close this — and `ktid()` would verify one in a single pass. Also
  refuted this pass: `KOD` as a clip→model oracle (only 1 of 92 `KOD`
  resources holds both a clip wrapper and a model bundle). Still open:
  `few3h-mesh-rdb-coverage` (mesh stage still magic-scan sourced, ~945 of
  6,923 models).
  **Gamedata**:
  three character tables confirmed in `LINKDATA_A.BIN` (entries 59/90/141 —
  age/height, preferred classes+outfits, base stats+growth curves), found
  via a second community 010-template repo
  (`DeathChaos25/ThreeCopes_010EditorTemplates`) the same way Three Houses'
  PersonData was found, and confirmed the same way too (two independent
  offset-derivation methods agreeing byte-exactly + character/stat
  plausibility) — including a genuine, verified cross-table character-ID
  namespace mismatch between two of the tables (see
  `sibling-field-comment-as-free-semantic-oracle.md`'s second trap shape).
  A 4th table (a 77-entry debug/asset-identifier string registry, found by
  a whole-corpus header-shape census rather than a template) and a 5th
  format family (**"G1X"**: `TB1G`/`MN1G`/`FP1G`, 92 entries, this engine's
  self-describing `magic+version+size` section-header convention recurring
  *inside* `LINKDATA_A` — `src/data/formats/linkdata-g1x.ts`) cover a
  further 92 entries but a disproportionate 25% of the remaining
  unclassified bytes. `TB1G`'s node-level grammar (a small "leading kind
  marker selects record shape" dispatch — see
  `kind-marker-dispatch-grammar-survives-failed-stride-sweep.md`) decodes
  byte-exact for 36/44 real trees (81.8%), all 36 also matching the
  header's own declared node count exactly, after an earlier stride sweep
  had found nothing; several node "type hash" values recur byte-identically
  across all 44 independent trees (a shared, unnamed action/type enum,
  matching the task's own "AI Behavior Tree" hypothesis — no community
  documentation of this format exists anywhere, checked via WebSearch).
  `MN1G`'s container is now **fully closed** (an offset table between the
  root header and its 7 named sections, previously mistaken for an
  unresolved inline sub-header — see
  `gap-region-may-be-offset-table-not-inline-header.md` — chains byte-exact
  across 24/24 real entries); its 7 sections (`IZSG`/`TVWG`/`GEWG`/`MAWG`/
  `CAWG`/`OLAG`/`TCAG`, reversed-magic reading "G1NM") look navmesh-shaped
  but are individually undecoded. `LINKDATA_A.BIN`'s remaining ~3,858
  entries (item/scenario/event data, if it lives here at all) are still
  untouched — a relaxed-magic resweep and a leading-8-byte histogram both
  came back empty/inconclusive this pass. **Checked and
  confirmed absent**: FE Warriors (2017)'s third KWBN/`_HBW0000` SFX audio
  container does not recur here (2 raw `KWBN` magic hits, both proven
  coincidental — no `_HBW0000` wrapper anywhere) — this game's audio corpus
  is genuinely complete, not a case of `content-type-absence-needs-
  multiple-independent-angles.md`'s extraction-gap trap.

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

**Whether a title's executable holds a resource-path registry is predicted
by its container design, and this was checked across all three KT titles.**
FE Warriors ships loose RomFS files with no LINKDATA at all, so its `main`
*must* hold literal paths — and does (13,133 entries, see above). Three
Houses (`DATA0`/`DATA1`) addresses assets by number, so its `main` holds
only `"%s.bin"`/`"%s:/%s.bin"` templates and **no registry** — confirmed by
extracting and scanning its ExeFS. Three Hopes has no registry either, but
for a *third* reason and on evidence that only exists as of the RDB pass:
its assets are **hash**-addressed, not index-addressed (`main` carries
`"%s0x%08x.fdata"`, `"KtidFilePath"`, `"root.rdb"`, no path array anywhere
in the 39 MB image). Its ExeFS had in fact **never been extracted** when
the original "confirmed for both" claim was written — `extract-romfs.ts`
only writes ExeFS when `p0-exefs/main` is absent and never backfills a
title extracted before that step existed.
Their asset-ID->name problems have to be solved from the archive indices
instead. Note the structural stride signature alone false-positives on both
(17,322 and 946 bogus entries), which is why the locator also scores
candidate runs on path-shapedness.

**But "no registry" is not "no oracle" — the two titles have oracles of
different *shapes*, and this is the account's worked pair.** FE Warriors'
oracle is a **data array** in the executable (a resource-path registry you
read directly). Three Hopes' is in the executable's **code**: it ships no
path array at all, yet its property-registration jump table pairs every
plaintext name with its precomputed hash constant in adjacent instructions,
which yields the KTID algorithm and with it every name that survived
anywhere in the binary or the data (see the Three Hopes entry above).
So when a hash-addressed title looks like a dead end, go after the
registration code before closing the search — and then *measure* the hash's
reach rather than assuming it, because on Three Hopes it named thousands of
property and object names while leaving model and animation names
permanently out of reach. Chain: `game-re-method/name-hash-recovery.md`.

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
shape of game where it won't. **Animation**: `fe-threehouses` and
`fe-warriors` both use **G2A** (magic `_A2G`), not the community-doc-named
"G1A" (`_A1G`) — see `community-format-name-mismatches-real-magic.md`.
The codec (`src/data/formats/g2a.ts`, ported from `Joschuka/fmt_g1m`) is
shared byte-identically, following the same "container differs, codec
doesn't" pattern as meshes: FE Warriors keeps clips in a separate file
matched by filename, Three Houses embeds them in the mesh's own PACK/
`.kldm` entry, and the titles use different version-gated layouts
(`"0300"`, `"0400"`, `"0500"`) that one `g2a.ts` handles — but note the
version gate needs **two** independent flags, not one boolean: Three Hopes'
`"0400"` pairs `"0300"`'s bitfield widths with `"0500"`'s 32-byte header
(`version-flag-conflates-independent-format-traits.md`). And Three Hopes
*does* ship 583 real `_A1G`/G1A v1 resources — the "no game here ships real
G1A" claim holds only for the two 2017/2019 titles; Three Hopes' were
compressed inside the RDB and invisible to the magic scan that produced it.
G1A is now fully decoded (`g1a.ts`), and since neither sibling game ships
any, there is nothing to be cross-compatible with — but its *export* path
is shared: `g2a-gltf.ts`'s clip input was widened to a structural
`SkeletalAnimationSource` so both formats use one glTF writer, a type-only
change leaving both other games' output byte-identical.
`few-threehopes` also uses G2A, confirmed via the same magic-byte-scan
technique — a third version string (`"0400"`) transfers with zero code
changes — but centralizes every clip into one shared package with no
per-character skeleton pairing at all, unlike either sibling game's
filename-match or same-container convention; see the `few-threehopes`
entry above and `missing-instance-link-invariant-table-substitutes.md` for
how that gap was closed anyway.

## Operational notes specific to this project

- **Memory-constrained shared dev machine.** `data/extracted/` holds ~115 GB
  across five romfs dumps; other projects on the same machine can hold
  double-digit GB of RSS concurrently. Prefer fd-based random access
  (`openLinkData`/`loadDATAArchive`/`openPKZ` all show the pattern) over
  `readFileSync`-the-whole-file, especially in any corpus-wide scan script;
  `--max-old-space-size` does not bound `Buffer`/WASM linear memory, so a
  Node heap cap alone won't prevent an OOM from a large allocation.
- **Whole-image ARM64 censuses with no capstone/r2/numpy installed.** The
  FE3H cap audit ran entirely as TypeScript typed arrays over the relocated
  `main` image (`build/cache/scratch/fe3h-cap-audit/a64.ts`: ADRP index,
  `xrefsTo`, `blTo`, encoding-mask predicates, `llvm-mc -disassemble` for
  spot reads). Mask predicates must compare the *masked* word against the
  *masked* constant and test the immediate field separately —
  `cmp wN,#imm12` is `(x & 0xffc0001f) === 0x7100001f && ((x>>>10)&0xfff)
  === imm`; the first version compared the masked word against a constant
  that still contained the immediate and returned 0 guard sites for every
  table, which reads exactly like "no guards exist". Sanity-check any
  encoding predicate against one known-good site before trusting a
  zero-hit census.
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

## Corpora-index row text formerly inline in `game-re.md`

Moved verbatim from the always-loaded agent prompt during the 2026-10 restructure.

| `~/Development/chimera` | Astral Chain, Fire Emblem: Three Houses, Fire Emblem: Warriors, Fire Emblem: Engage (the account's first **Unity**-engine title, not Koei Tecmo — texture+mesh export solved via UnityPy, see the corpus file for the Unity-left-handed-to-glTF mirror-conversion derivation and a real UnityPy vertex-weight-normalization bug found along the way), Fire Emblem Warriors: Three Hopes (all Switch). Notable: this project is the account's worked pair for **"the executable is the ID->name oracle" in its two different shapes**. FE Warriors' whole model-ID space is named from a resource-path registry — a *data array* inside `main`. Three Hopes ships no such array (hash-addressed KTIDs), but its oracle is in `main`'s *code*: the property-registration jump table pairs each plaintext name with its precomputed hash constant, which yielded 2,756 anchors and so the **KTID hash itself** (`ktid(s) = Σ s[i]·31^(i+1)`, code-confirmed) — naming 21 resources, 95.0% of `KOD` property keys, and a 188-edge resource dependency graph after `KOD` was fully decoded (560,408/560,408 blocks, 0 slack). Its animation corpus is fully shipped (G2A + G1A, 5,152/5,152) with 213 clips pinned to exactly one model by co-location on skeleton topology, but clip/model *names* are a **reasoned negative**, not an open search — a 32-bit linear hash cannot be inverted for the 16-36-char names the ID set itself measures, and no plaintext for them ships. Also the account's worked example of **"a post-launch update ships a revised struct, and the community template describes the *newer* build"** (FE3H's `Scenario` table: base records 40 bytes, the v1.1.1 LayeredFS patch layer's copy 46 and matching the fan template verbatim; the two revisions then cross-check byte-exactly, 3,480/3,480). Also the account's worked example of a weak-but-real single-offset fit meaning "one more indirection layer," not noise or the whole answer: FE3H's small `assetId` character/class-model field only best-fit 87% against real mesh-archive indices directly, but is really a row index into an already-parsed container's own unopened sibling section, whose fields resolve ~100% with the right per-kind offset — surfaced via a second, active community GUI-editor's source (not the already-consulted passive binary-template repo) and shipped as a `tools/viewer/` character+class model picker (see `weak-single-offset-fit-signals-missing-indirection.md` and `active-gui-tool-source-vs-passive-template-verify-stride.md`). **G1M skinning is now fully solved** across all three Koei Tecmo titles (one shared `src/data/formats/g1m.ts`/`g1m-gltf.ts`): a bone palette's `matrixId` indexes the `MM1G` **inverse-bind-matrix palette** and `boneId` (bit 31 masked off) names the bone — superseding a long-standing "matrixId is the bone index; clothId/boneId are runtime-patched pointer slots" verdict that was wrong on both counts. Confirmed by a zero-deviation per-entry invariant (`world[boneId] x MM1G[matrixId] == identity` for 108,510/117,842 bindings; the 9,332 exceptions are exactly the NUNO-driven cloth/hair bindings, whose vertices live in bone-local space and were previously exported heaped on the ground). 577/497/183 GLBs rebuilt and validated. This is the account's sharpest worked example of **a bind-pose render being zero evidence about skinning** (the bug survived multiple passes, a full `gltf-validator` sweep and real Playwright screenshots) and of **using a stored-vs-recomputable redundancy as a hypothesis discriminator** — see `bind-pose-render-blind-to-joints-index-space-bug.md`, `stored-bind-matrix-palette-is-a-per-entry-identity-oracle.md`, `high-bit-set-field-is-flagged-index-not-pointer.md`. **FE3H's long-standing "hair-length content gap" is SOLVED (2026-09)**: G1M `clothType==1` submeshes repurpose EVERY vertex attribute as NUN cloth-solver input (Position=weights — the old exporter collapsed 170/569 packs' hair/capes/skirts onto their anchors; a verified static rest-pose bake now ships, see `cloth-submesh-repurposes-vertex-attributes.md`), sibling `_M1G` PACK sections are complete runtime-variant models (fByleth Enlightened/Dorothea pre-timeskip heads, now exported as `pack_<i>_s<sec>` GLBs), and rigid G1M vertex joint indices turned out to be palette-slot x3 corpus-wide — a third bind-pose-invisible skinning bug across all three titles' shipped corpora, fixed in the shared exporter (see `prescaled-joint-indices-divisibility-census.md`; sibling corpora still need regeneration). NUN cloth driver-mesh geometry is solved (see the corpus file); native runtime cloth-physics *parameters* are a settled negative after three follow-up passes — the whole native solver chain is confirmed unreachable dead code (its gating call argument is a hardcoded literal at its only call site), so the viewer's spring-bone approximation is the only real output. **FE3H's class-body palette-variant recolor mechanism (previously solved-but-unwired) is now fully wired end-to-end**: all 1,134/1,134 confirmed-present palette PNGs shipped (fixing two real pipeline completeness bugs along the way — see `any-match-resumability-guard-orphans-partial-multi-item-entry.md` and `sparse-sample-flatness-heuristic-false-negative-on-real-content.md`), a runtime per-character baseColor swap in the `tools/viewer/` character/class picker (Playwright-verified: Edelgard vs. Dimitri as Great Knight render distinctly recolored, zero console errors), and the flat asset browser's static class-body/Dancer GLBs now bake a real default-coloured diffuse instead of a mask/normal/grey map — the swap target itself needed correcting from "the big embedded texture" to "the always-4x4 placeholder texture" by reading the G1M material table directly (see `embedded-texture-size-does-not-predict-material-diffuse-binding.md` and `runtime-texture-swap-must-mutate-captured-original-material.md`). **FE3H's body+head compositing picker got 4 real bug fixes this pass**, one of them a SHARED `@seer-project/engine-3d` change (not host-side-only): `MeshSession.addModel()` now wires the same render-mode/shading/texture-filter toggles `setModel()` always had (previously a composited head silently ignored every appearance toggle — see `secondary-attach-api-misses-primary-side-effect-wiring.md`), which also surfaced and fixed a shared-shading-cache-clobber bug the fix's own per-model loop would otherwise have introduced (`per-call-cache-clear-breaks-under-per-item-loop-conversion.md`; 254/254 engine-3d tests passing). The other three (timeskip-variant dropdown decoupled from the body-only gate, an eye-rendering `alphaMode` fix requiring real threshold tuning against measured alpha histograms, and a corpus-surveyed neck-bone runtime alignment fix superseding the single-pair "no transform needed" verdict — see `skinned-composite-alignment-needs-joint-transform-diff.md`'s correction block) are chimera-only. **FE3H DLC cosmetic-outfit content found and shipped**: 2 of 12 DLC NSPs (never decrypted before — Rights-ID crypto like BKTR patches but not a Patch partition, silently skipped by the largest-NSP-only base extractor) hold real, previously-undocumented outfit geometry (22 GLBs, ≥4 distinct outfits incl. a casual/loungewear pair and an academy officer's uniform, +54 palette textures) via a new `extract-dlc-outfit-archive.ts`; the whole "Change Attire" equip system is now SOLVED end-to-end (hardcoded 11-record outfit-slot table in `main`, AOC mount + content-presence gate, and the final modelId→archive hop: a windowed `+400` remap into the DLC merge window, `dlcLocal = modelId−13`, 21/21 identity-verified full bodies) — the last hop took a re-oracle pass because the consumer is vtable-bridged and an earlier "3120+modelId" fit was one branch of a range-gated resolver, see `vtable-bridged-consumer-defeats-call-census.md` and `dense-range-offset-fit-needs-identity-oracle.md`'s second instance. **FE3H's class + creature combat-motion containers are now located and decoded** (`nx/action/motion/{KB_L_*,BC}_PACK.bin` at `DATA0[4622-4632]` and per-creature `DATA0[4253-4273]`; outer slot 0 = `u32[]` motion-set id table, KT_GZ members, 17-slot member archive whose slot 15 is a nested pack of G2A `"0500"`/60 fps clips) — found by asking the patch layer's own `INFO0.bin` to name one id in an anonymous band, and confirming FE3H's and Three Hopes' body clips are **set-identical on a 56-bone core id set**; the class→motion-set-id binding stays open (no gamedata field carries it — see `numeric-range-overlap-is-not-an-id-binding.md`, sourced here). Also this project's glTF→KT import now has a real donor-independent path (`gltf-g1m-fresh.ts` synthesizes a skeleton from a glTF node/skin graph; `gltf-g2a.ts` resamples glTF animation into G2A) | `game-re-corpora/chimera.md` |

## Lessons sourced from this corpus (full list)
active-gui-tool-source-vs-passive-template-verify-stride.md, any-match-resumability-guard-orphans-partial-multi-item-entry.md, ascii-digit-version-field-needs-digit-weighted-decode.md, bind-pose-render-blind-to-joints-index-space-bug.md, bitmap-bit-order-from-transition-isotropy.md, block-chain-walk-stops-at-unknown-sibling-block-magic.md, bone-palette-may-bind-one-bone-twice-needs-proxy-joint-node.md, byte-granular-deswizzle-of-block-compressed-data.md, cloth-submesh-repurposes-vertex-attributes.md, community-format-name-mismatches-real-magic.md, community-table-name-mismatches-semantic-content.md, compressed-container-members-invisible-to-magic-scan.md, concurrent-sibling-live-edit-collision-on-shared-source.md, content-type-absence-needs-multiple-independent-angles.md, cross-platform-string-delta-reveals-stride-vs-offset.md, cross-table-outlier-corroboration-without-external-oracle.md, dense-range-offset-fit-needs-identity-oracle.md, detector-offset-generalized-from-partial-corpus-silently-skips-rest.md, doc-self-cross-reference-before-fresh-disassembly.md, embedded-texture-size-does-not-predict-material-diffuse-binding.md, engine-family-shared-decoder-not-shared-container.md, executable-resource-path-registry-names-asset-ids.md, external-validator-sample-insufficient-cli-spawn-slow.md, first-slot-magic-names-the-whole-container.md, first-subentry-only-check-misses-later-recurring-magic.md, format-field-width-unexercised-by-first-corpus.md, gap-region-may-be-offset-table-not-inline-header.md, gating-argument-may-be-a-compile-time-constant-not-data.md, gltf-joint-zero-weight-filler-duplicate-fear-untested.md, high-bit-set-field-is-flagged-index-not-pointer.md, identical-header-shape-two-container-formats.md, kind-marker-dispatch-grammar-survives-failed-stride-sweep.md, list-final-byte-is-a-data-value-not-a-terminator.md, live-ab-isolation-names-carrier-not-mechanism.md, magic-scan-can-substitute-for-container-reverse-engineering.md, missing-instance-link-invariant-table-substitutes.md, numeric-range-overlap-is-not-an-id-binding.md, override-layer-indexed-by-entry-id-not-semantic-filename.md, per-call-cache-clear-breaks-under-per-item-loop-conversion.md, per-instance-file-set-may-be-duplicate-blobs.md, platform-port-swaps-adjacent-header-fields.md, pointer-array-stride-signature-needs-content-plausibility.md, prefixed-sibling-family-shares-numeric-id-space.md, prescaled-joint-indices-divisibility-census.md, published-walkthrough-numeric-oracle.md, redundant-offset-field-poisoned-chain-by-length.md, reference-tool-data-revision-mismatch.md, reference-tool-field-never-consumed-by-its-own-importer.md, reuse-shared-palette-rows-for-byte-identical-reserialization.md, runtime-texture-swap-must-mutate-captured-original-material.md, secondary-attach-api-misses-primary-side-effect-wiring.md, semantic-output-diff-with-unchanged-parts-as-reference-frame.md, session-scratchpad-tmpfs-exhaustion.md, shared-decoder-behavior-is-a-cross-platform-contract.md, shared-table-column-role-varies-by-row-subtype.md, short-magic-hit-in-high-entropy-region-needs-falsification.md, sibling-field-comment-as-free-semantic-oracle.md, sibling-length-field-disagreement-read-past-real-stream.md, sibling-magic-may-be-same-struct-zeroed-field.md, silent-loader-clamp-makes-appended-record-look-live.md, skinned-composite-alignment-needs-joint-transform-diff.md, sparse-sample-flatness-heuristic-false-negative-on-real-content.md, stale-compressed-verdict-relocate-real-header.md, stored-bind-matrix-palette-is-a-per-entry-identity-oracle.md, undetermined-selection-may-be-immaterial-or-already-in-a-skipped-field.md, unexplained-pointer-pair-may-target-eof-anchored-footer.md, union-tiling-beats-per-record-offset-chaining.md, unknown-constant-field-is-engine-grammar-load-bearing.md, unknown-opcode-may-select-a-different-resource-kind.md, update-patch-ships-a-revised-struct.md, version-flag-conflates-independent-format-traits.md, vtable-bridged-consumer-defeats-call-census.md, weak-single-offset-fit-signals-missing-indirection.md
