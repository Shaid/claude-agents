# vanille — Odin Sphere (PS2), Grim Grimoire (PS2), Dragon's Crown (PS3), Grand Knights History (PSP), 7 Vanillaware titles registered

**Project root:** `~/Development/vanille` (codename "vanille"; 7 Vanillaware
titles registered in `src/game-id.ts`, only the two PS2 ones have pipeline
stages wired).

## CRI ROFS "CVM" container — fully solved (both PS2 titles)

Odin Sphere (`SLUS_215.77`, US) and Grim Grimoire (`SLUS_216.04`, US) share
the identical CRI middleware stack (`DVCI/PS2EE Ver.2.73` + `ROFS Ver.1.81`
embedded in the boot exe): the retail ISO's `DISC.CVM` (99% of disc) is a
chunked container (`CVMH` + `ZONE` chunks, all BE) wrapping a plain
ECMA-119 ISO9660 image whose **directory sectors are scrambled** with a
per-title passphrase; file-data sectors are plaintext. Fully decoded and
shipped as `tools/shared/rofs-cvm.ts` (ported from roxfan's `cvm_tool`,
fork: `JayFoxRox/cvm_tool`) + `cvm-export.ts`/`cvm-assets.ts`; specs in
`docs/odinsphere/ps2/data-structure.md` (§ 3-4) and
`docs/grimgrimoire/ps2/data-structure.md`.

- **Passphrase → 8-byte key**: iterated 32-bit-wrapped sum over the
  passphrase, byte interleave, then 4 rounds of a 1024-prime-table hash.
  `shinobutan` → `45E3655352C34C15` (known-answer).
- **Per-sector cipher**: seed = `key[5]`; per 8-byte chunk, hash of
  `logicalSector*seed` selects one of 9 fixed byte-mix patterns (XOR/ADD)
  over key+hash; logical sector = `isoSector + datalocISO.sector −
  isoStartSector`. Scope: only ISO sectors 16..last-dir-sector.
- **Both games use the same passphrase `shinobutan`** (Emu-Land CVM
  password thread + verified: each PVD decrypts to `CD001`). Odin: 3,069
  files; Grim: 608.
- Container facts: header +0x24 is an ISO-9660 build timestamp (not a
  version field); +0x30 flags 0x10 = encrypted TOC; sector table at
  +0x80..+0x88; "ZONE" chunk's `dataloc1`/`datalocISO` locate a 0x800-byte
  mystery record stream (sector 2) and the ISO zone (sector 3).

**CVM password prior art:** the Emu-Land thread "Пароли для архивов .CVM
(CRI ROFS)" collects passwords for many CRI-CVM PS2 titles (Odin/Grim =
`shinobutan`; Yakuza 1/2 = `qi2o@9a!`; .hack//G.U. = `cc2fuku`; Sakura
Taisen = `tinaandluckandru`/`SAGUCHIFUNAYOI`/`itinenmotanai`; Arcana
Heart = `zxcv`; Nightshade = `PJ234110`; PSU = `4147a5c2b5fe0357`; Melty
Blood AA = `MELTYBLOOD_AA`; many titles ship unencrypted) — a fast oracle
for any future CRI-CVM target.

## Inner formats — identified by magic, not yet decoded

Odin: `.DAT`/`.DAU` = `ps2_DTPK`; `.FTP` = `FTEX` (same family as Dragon's
Crown PS3); `.MBP` = `FMBP`; `.TXT`/`.SSB`/`.ODB` = `FECD` (BE header +
Shift-JIS text); `.ZLD` = zone tables pairing `.ARD` area + `.SSB` script
names; `.ARD` = compressed area data; `.AFS` = standard CRI ADX archives
(BGM 114 / US_VOICE 472 / VOICE 472 — extents byte-verified against raw
magic scan). Grim: `.MBP`/`.FTP`/`.TXT`/`.GSB`/`VSD.DAT` + plaintext
English text near its CVM tail.

## CRI audio stack — ADX/AFS/ACB/AWB — solved and shipped across all four titles

One shared decode library (`tools/shared/adx.ts`/`afs.ts`/`acb.ts`/
`awb.ts`, plus `cri-cpk.ts`'s generic `@UTF` table reader) covers both
packaging shapes CRI middleware uses in this corpus: PS2-era standalone
`.AFS` archives (Odin/Grim) and PS3/PSP-era `.acb`/`.awb` banks embedded in
a CPK (DC/GKH). Full byte-level spec, verification evidence, and the
viewer's playback engine: `docs/audio-format.md` (project docs, not
duplicated here).

- **ADX** (CRI's ADPCM codec) — browser-safe decoder confirmed via
  non-degenerate-PCM + short-window lag-1-autocorrelation checks against
  real tracks, plus a confirmed **genuine-silence placeholder track**
  regression fixture (many `BGM.AFS` entries share one minimum byte size
  and legitimately decode to all-zero PCM — not a decoder bug).
- **AFS** (flat archive: magic + count + offset/size table) — Odin Sphere
  (1,058 ADX tracks: 114 bgm/472 voice/472 us_voice) and Grim Grimoire
  (2,796 ADX tracks: 28 bgm/2 se/1,383 voice/1,383 us_voice), both fully
  decoded and playable in-browser.
- **`@UTF`** (CRI's generic serialized table format) underpins both the CPK
  header/TOC *and* ACB banks — one parser for both. A real gap this
  session: storage-type `0x30` ("constant", embedded once in the schema,
  zero per-row bytes) wasn't handled, cascading a byte misalignment into
  every column read after one — fixed via a shared `readUtfValue()` helper.
- **ACB** (Atom Cue Bank) — an ACB is itself one `@UTF` table; its
  `WaveformTable` nested sub-table is the authoritative per-stream codec/
  rate/channel/sample-count source and needs no cue-graph resolution to
  read. The full CRI cue graph (`CueTable`→`SynthTable`→`SequenceTable`/
  `TrackTable`/`CommandTable` bytecode, for randomized/multi-layer cues) is
  NOT implemented — **positional pairing** (`CueNameTable` row N ↔
  `WaveformTable` row N, used only when the two tables' row counts match)
  is used instead, independently confirmed correct end-to-end against
  `vgmstream-cli`'s own metadata report (sample rate/channels/sample
  count/name all matching exactly at 6 spot-checked positions). When counts
  diverge (confirmed on a 397-cue/350-waveform SE bank), every waveform is
  still listed but named generically rather than guessed.
- **AWB** (Atom Wave Bank) — **two structurally distinct sub-formats
  sharing one extension**, both confirmed: classic **AFS2** (id table +
  offset table — DC's `bgm.awb`) and a **nested-CPK/ITOC** mini-container
  (GKH's `bgm_streamfiles.awb` — a *complete* mini-CPK using CRI's
  ITOC id-indexed TOC variant instead of AFS2, confirmed via its own
  `Tvers` string `awb.01.01.00, DLL2.78.04`). `parseAwb()` tries AFS2 first,
  falls back to ITOC. A real, corpus-corrupting AFS2 alignment bug was
  found and fixed this session — see
  `directory-align-field-scoped-to-payload-not-table.md`.
- **Codec identification via `WaveformTable.EncodeType`**: `2` = HCA
  (Dragon's Crown, confirmed via `vgmstream-cli`'s own report), `8` =
  ATRAC3 (Grand Knights History, confirmed via the raw stream's
  `WAVE_FORMAT_SONY_SCX`/`0x0270` `fmt ` chunk tag). Both HCA and ATRAC3
  decode are deliberately out of scope (proprietary lossy codecs) — DC's
  54 tracks and GKH's 50 tracks ship as structural-metadata-only manifest
  entries (real names, byte-exact AWB offsets, sample rate/channels/
  duration) rather than playable audio.
- **Architecture note applicable to any project with large audio
  originals**: per `docs/architecture-overview.md`'s "audio decoded live,
  not precompiled" exception, raw bytes are never extracted into
  `public/assets/` — manifest entries carry byte-range addresses
  (`audioDataPath`/`audioByteOffset`/`audioByteLength`) for on-demand HTTP
  Range fetches against the dev server's `/data/*` proxy, verified
  end-to-end with a real `curl -H "Range: ..."` request returning `206`
  and the exact expected magic bytes.
- **Real `manifest.json` blind-overwrite bug found and fixed**: two
  existing pipeline stages (`cvm-textures.ts`, `cpk-textures.ts`) wrote
  `manifest.json` directly instead of through the project's own documented
  "merged, upsert-by-name" convention, silently clobbering whatever another
  stage had already written. Fixed via a new shared `upsertManifest()`
  helper (`tools/shared/manifest-assets.ts`) — worth checking for in any
  project's manifest-writing stages, not just this one.

## Sibling links

- **House formats cross generations (verified 2026-08-12 by extracting
  real Dragon's Crown PS3 CPK files and comparing magics):**
  - `FTEX` textures: Odin `.FTP` (601) **and** Dragon's Crown PS3 `.ftx`
    (605) both start `FTEX` — same format family, header layout differs
    per port (Odin's 2nd u32 `0x8084` vs DC's `0xc006e000`-shaped
    fields; treat as a per-platform variant, see
    `game-re-lessons/platform-port-swaps-adjacent-header-fields.md`).
  - Model packs: Odin `.MBP`/Grim `.MBP` start `FMBP`; DC `.mbs` starts
    **`FMBS`** — a real, distinct sibling (big-endian, 0xE4 header, `f32`
    UV/XY, no PS2 VIF packaging), not the same magic. (A 2026-08-12 note
    here previously claimed DC's magic was `FMBP` too — that was wrong,
    corrected 2026-09-05 after direct byte inspection; see
    `docs/fmbp-model-format.md` in `vanille` for the full correction.)
    Both are now **fully solved** — one shared decoder
    (`tools/shared/fmbp.ts`) handles both variants' container AND inner
    attribute records (colour/uv/xy/part/frame/draw/drawGroup/clip),
    render-verified against real art on both platforms (PS2: a black cat,
    a fairy protagonist across 24 poses; PS3: a wooden barrel, a
    13,743-part goblin with sword and shield, a robed sorcerer). Two
    platform-port gotchas surfaced going PS2→PS3: FMBS's vertex-colour
    alpha is plain `0xFF==1.0`, not the PS2 GS's `0x80==1.0` (over-
    brightened every render until parameterized); and FMBS's part `uv`
    field is a `u32` whose low 16 bits are the real index and high 16 bits
    carry an unrelated, still-undecoded selector, invisible on small
    props and only exposed by the largest model in the corpus (13,743
    parts) via a `RangeError`.
  - Text containers did **not** survive the rename: DC `.fms` = `FMSB`,
    DC `.bsb` = `00 00 00 47`-headed (neither is Odin's `FECD`).
  - `ps2_DTPK` (Odin `.DAT`/`.DAU`): no DC equivalent found.
- Same CRI middleware family as Dragon's Crown (PS3) — but that game uses
  **CPK** (`@UTF` TOC + CRILAYLA), not CVM; the CRI stack is per-title
  configurable, never assume one container shape transfers.
- **Grand Knights History (PSP)** is also **CPK**: `GKH.CPK` starts
  `CPK ` + `ff 00 00 00` + an **unencrypted** `@UTF` packet (CRI CPK's
  DecryptUTF is optional per game — DC PS3 encrypts, GKH does not).
  `tools/shared/cri-cpk.ts` transfers with a plaintext option.
- **Muramasa (Wii)** is a *completely different* container family:
  a plain Wii disc (game id RSFE7U) in Dolphin **RVZ** form, no CRI
  stack at all. Fully decoded (`tools/muramasa/extract.py`): RVZ
  (Zstandard + RVZ packing + Lagged-Fibonacci junk runs, per Dolphin's
  `WiaAndRvz.md`) → decrypted game-partition stream (RVZ stores Wii
  partition data decrypted + hashless, bypassing the Wii common key) →
  main.dol → FST (2,736 entries, file offsets = entry×4 relative to the
  partition stream) → **2,733 files**. Inner formats: **FCMP** (1,454
  files — Vanillaware's Wii container wrapping FTEX/FMBS/EMB/NSB/WOLD/
  _MLI, i.e. the same house formats as Odin/Grim re-magicked, LZSS-style
  with a 0xFEE dictionary start), **RSTM** (.brstm Wii DSP ADPCM audio,
  1,206), dev file lists leaking the project codename "NinPri". The
  RVZ→partition pipeline generalizes to any Wii RVZ dump. **Wii's `FMBS`
  sprite models are now solved too** (549/621 `.mbs` published, incl.
  idle-clip animation) — a THIRD header/section-stride layout of the
  same `FMBS` container, not a copy of PS3's: a compact 0xA0 header at
  the same field *positions* as PS2 `FMBP`'s own header but read
  big-endian (not `FMBP`'s little-endian, not PS3 `FMBS`'s dedicated
  0xE4 layout), plus its own per-section strides (e.g. `drawGroup`=16 vs
  PS3's 20, pinned by a remainder sweep since it's the corpus's last
  section and its declared size absorbs trailing padding — the same
  technique already used once for `FMBP`). `parseFmbsHeader()` auto-
  detects layout from the literal `headerSize` field value; every other
  `FMBS` accessor needed zero code changes since fields are reached
  generically via `model.section()`. Confirmed via whole-corpus
  structural invariants, direct pixel inspection of 4 diverse models
  (a boss, the protagonist, an NPC, a 6,744-part multi-page yokai
  monster), a live-viewer Playwright animation check, and a byte-
  identical Dragon's Crown (PS3) regression rebuild after the shared
  `tools/shared/fmbp.ts` change. Full derivation:
  `docs/fmbp-model-format.md` § "FMBS on Wii" in `vanille`. Open: one
  model (`KisukeB_npc00.mbs`) renders as an unexplained blur; and
  `extract.py`'s flat single-directory extraction collapses 21 same-
  named files from different disc subdirectories into one physical
  file each, silently dropping content (FST declares 642 `.mbs`, only
  621 exist on disk) — see
  `game-re-lessons/flat-directory-extraction-collapses-same-named-siblings.md`.
- tri-Ace's VP2 (valkyrie corpus) is a *different* PS2 container family
  (XOR TOC + SLZ) — Vanillaware ≠ tri-Ace on PS2.
- `tools/shared/cri-cpk.ts` (Dragon's Crown/GKH CPK) and
  `tools/shared/rofs-cvm.ts` (Odin/Grim CVM) are the two CRI-shared
  decoders in this project.

## 13 Sentinels: Aegis Rim + Unicorn Overlord (Switch) — CRI CPK + Tegra FTX/NVT texture stack

Both titles run on Switch (NCA/RomFS extracted via `hactool` per
`game-re-tooling/switch.md`) and share **CRI CPK** (`tools/shared/cri-cpk.ts`,
the same reader used for Dragon's Crown PS3/GKH PSP) as their base
container, with `.ftx` archive members wrapping a `FTEX`/`FTX0`-tagged
Tegra X1 texture payload family (`.tex`/NVT). Full byte-level spec:
`docs/switch-ftx-nvt-format.md`.

- **Container**: `FTEX` outer archive (0x80-byte header, `count` of
  `FTX0` entries chained by `offset += headerBytes + payloadSize`) wraps
  one or more `.tex` (NVT) payloads. Format code at `.tex+0x04`: `0x44`
  BC3, `0x49` BC4, `0x4d` BC7 — no other value in 7,301 sampled payloads.
- **Tegra X1 block-linear layout — fully solved**, verified via a
  structural size invariant (0 deviations across all 7,301 payloads) and
  a round-trip test against an independently-written swizzler. Two real
  bugs found and fixed in the same session: (1) a per-block copy loop
  that never advanced its source cursor (`+ i` missing), which still
  looked plausible because each GOB landed in the right macro position —
  read as "fine dither" in QA rather than the ~97% wrong-block corruption
  it actually was; (2) a hardcoded 16-GOB macro-tile height, correct for
  only 40% of the corpus — block height is per-texture
  (`min(16, next_pow2(ceil(blockRows/8)))`) and must be derived, not
  assumed. A `tex-decoder`-vs-`texture2ddecoder-wasm` BC7 cross-check
  came back byte-identical once these were fixed, retroactively
  disproving an earlier "wasm decoder misdecodes mode-4/6 blocks" theory
  — the neon-green artifacts were the swizzle bug smearing a legitimate
  `#00FF00` chroma-key padding convention (background atlases pad to
  power-of-two with solid green; this is authored content, not a fault).
- **Localized sibling CPKs** (`ROBO_{FR,GE,IT,SP}.CPK`,
  `Unicorn_{DE,ES,FR,IT,US}.CPK`) reuse the base CPK's own `.ftx`
  relative paths almost 1:1 and reuse each other's paths too — see
  `wwise-shared-short-id-across-language-variants.md`. Fixed with a
  locale-namespaced Stage-1/Stage-2 publisher
  (`tools/shared/switch-game-assets.ts`); base counts unaffected
  (13S 4,508, UO 2,031), locale texture counts now shipped (13S 692
  across FR/GE/IT/SP, UO 70 — the project's entire BC3 corpus, 14 per
  locale × 5).
- Still open: `.tex+0x08/0x14/0x18` (constant `1` in every payload —
  candidate mip/array/depth count, unexercised by this corpus); BC4
  currently published as red-channel-only RGBA (correct data, weak
  presentation for font/mask atlases).
- **13 Sentinels' `.mbs` sprite models are a fourth `FMBS` layout, solved
  end-to-end** (2026-09-05, `tools/shared/switch-cpk-models.ts`): shares
  the `FMBP`/`FMBS` "paper-doll" family's 11-section architecture (see the
  `crawl` corpus entry above) but is little-endian with its own dedicated
  0x120 header, u64 section offsets, and a split-width (u32×4 + u16×8)
  count array — none of which were assumed from the PS2/PS3/Wii siblings,
  each re-derived from this corpus's own bytes. The one correction that
  mattered for actually rendering anything: uv fan coordinates are
  normalized `[0,1]` texture-space floats (every prior platform stores raw
  pixel-space floats) — an un-scaled render passed every structural/count
  invariant but produced a plausible-looking, completely blank white PNG,
  since every part sampled only the texture's top-left corner texel. 428/436
  `.mbs` published (base 348 + 22×4 locale GUI models, which reuse the base
  CPK's own paths verbatim and need the same `sourcePrefix` locale
  namespacing as textures). Full spec: `docs/fmbp-model-format.md` §
  "FMBS on Switch"; `docs/13sentinels/switch/data-structure.md`.

## Corpora-index row text formerly inline in `game-re.md`

Moved verbatim from the always-loaded agent prompt during the 2026-10 restructure.

| `~/Development/vanille` | Odin Sphere (PS2), Grim Grimoire (PS2), Dragon's Crown (PS3), Grand Knights History (PSP), Muramasa: The Demon Blade (Wii), 7 Vanillaware titles registered — CRI ROFS `CVM` container fully solved (scramble passphrase `shinobutan`), inner formats identified (FECD/FTEX/FMBP/ps2_DTPK/ZLD/AFS); Dragon's Crown/GKH's shared CRI **CPK** container (`.ftx`/`.mbs`/`.fms`/`.acb`/`.awb`) also solved. Vanillaware's in-house **`FMBP`/`FMBS` "paper-doll" sprite-model format is now fully solved end-to-end on both platforms** — one shared decoder (`tools/shared/fmbp.ts`) handles PS2 `FMBP` (little-endian, VIF1-packed 12.4-fixed UV/colour, 597+124 files, 580+101 published as rendered sprite atlases: a black cat, a fairy protagonist across 24 poses) and PS3 `FMBS` (a genuinely different sibling — big-endian, 0xE4 header, plain `f32` UV/XY, no VIF packaging, corrected from an earlier wrong "shares FMBP's magic" note — 397/407 Dragon's Crown `.mbs` files published, render-verified as a wooden barrel, a 13,743-part goblin with sword and shield, and a robed sorcerer) plus a THIRD `FMBS` header/section layout on **Muramasa (Wii)** — same field roles, but a compact big-endian 0xA0 header sharing `FMBP`'s field positions rather than PS3's own 0xE4 layout, auto-detected from the literal `headerSize` value (549/621 `.mbs` published with reconstructed idle animation, byte-identical PS3-regression-verified; see `game-re-corpora/vanille.md`). Porting the decoder PS2→PS3 surfaced two real platform-convention bugs, not just a stride/endianness diff: FMBS's vertex-colour alpha is plain `0xFF==1.0` (not the PS2 GS's `0x80==1.0`, which over-brightened every render until parameterized) and its part `uv` field's high 16 bits carry an unrelated, still-undecoded selector invisible on small test props and only exposed by the largest model in the corpus. **CRI audio (ADX/AFS/ACB/AWB) is fully solved and shipped across all four titles**: browser-safe ADX decoder + AFS archives give Odin Sphere 1,058 and Grim Grimoire 2,796 real playable tracks; DC/GKH's ACB (`@UTF` cue banks, positional cue-name↔waveform pairing rather than a full cue-graph interpreter) + AWB (two distinct sub-formats sharing one extension — classic AFS2 vs. a nested-CPK/ITOC mini-container, disambiguated by the ITOC variant's own `Tvers` string) resolve 54 HCA + 50 ATRAC3 tracks structurally (real names/byte-exact offsets/duration; the lossy codecs themselves are out of scope) — see `directory-align-field-scoped-to-payload-not-table.md` for a real AFS2 offset-table corruption bug found and fixed this session. Also **13 Sentinels: Aegis Rim + Unicorn Overlord (Switch)**: shared CRI CPK container (`tools/shared/cri-cpk.ts`, `.ftx` members) + a from-scratch Tegra X1 block-linear `FTEX`/`FTX0`/`.tex` (NVT) texture codec fully solved (`docs/switch-ftx-nvt-format.md`) — per-texture block-height derivation was the load-bearing fix over a hardcoded-16-GOB guess (7,301/7,301 payloads pass the padded-surface-size invariant, 0 deviations). Base + all localized sibling CPKs now published (13S `ROBO_US`+`{FR,GE,IT,SP}`=5,200 textures; UO `Unicorn`+`{DE,ES,FR,IT,US}`=2,101) via a locale-namespaced Stage-1/Stage-2 publisher — see `wwise-shared-short-id-across-language-variants.md` for the shared-relative-path dedup trap this surfaced. **13 Sentinels' `.mbs` sprite models are a solved FOURTH `FMBP`/`FMBS` header/section layout** (`tools/shared/switch-cpk-models.ts`): little-endian like `FMBP`, but its own dedicated 0x120 header, `u64` section offsets (every sibling uses `u32`), and a split-width `u32x4+u16x8` count array — none assumed from the PS2/PS3/Wii siblings, each re-derived from this corpus's own bytes (`part`/`drawGroup` record strides are also wider than any sibling's). The load-bearing correction: `uv` fan coordinates are normalized `[0,1]` texture-space floats rather than every prior platform's raw pixel-space floats — an unscaled render passed every structural/count invariant (correct dimensions, non-zero drawn parts, 0 skipped) yet rendered completely blank, since every part sampled only the texture's top-left corner texel (see `normalized-uv-passes-structural-checks-renders-blank.md`, sourced from here). 428/436 `.mbs` published (base 348 + 22x4 locale GUI models, which needed the same locale `sourcePrefix` namespacing as textures — see `wwise-shared-short-id-across-language-variants.md`); the part `page` field also moved offset (`+7` vs. every sibling's `+3`, see `header-field-role-not-transitive-across-sibling-format.md`). Full spec: `docs/fmbp-model-format.md` § "FMBS on Switch". | `game-re-corpora/vanille.md` |
