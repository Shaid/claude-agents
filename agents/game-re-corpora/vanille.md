# vanille — Vanillaware: Odin Sphere, Grim Grimoire, Dragon's Crown, Grand Knights History, Muramasa, 13 Sentinels, Unicorn Overlord

**Project root:** `~/Development/vanille` · **Full history/evidence:** `game-re-corpora/details/vanille.md` (read on demand) · **Open work:** `docs/<game>/TODO.md` per game

## Games
- Odin Sphere (PS2) — `odinsphere`/`ps2` — CVM solved, ADX audio + FMBP models shipped; FECD/FTEX/DTPK/ZLD/ARD identified, not decoded
- Grim Grimoire (PS2) — `grimgrimoire`/`ps2` — CVM solved, ADX audio + FMBP models shipped
- Dragon's Crown (PS3) — `dragonscrown`/`ps3` (`ps4` registered, empty) — CPK, FTEX, FMBS models, ACB/AWB (HCA metadata only) shipped
- Grand Knights History (PSP) — `grandknightshistory`/`psp` — unencrypted CPK; ACB/AWB (ATRAC3 metadata only)
- Muramasa: The Demon Blade (Wii) — `muramasa`/`wii` — RVZ→FST extracted; FCMP, Wii FMBS (549/621) solved
- 13 Sentinels: Aegis Rim (Switch) — `13sentinels`/`switch` — CPK + Tegra FTX/NVT textures + 4th FMBS layout shipped
- Unicorn Overlord (Switch) — `unicornoverlord`/`switch` — CPK + FTX/NVT textures shipped

## Solved formats → where documented
- CRI ROFS **CVM** (`CVMH`+`ZONE`, ISO9660 with scrambled directory sectors; passphrase `shinobutan` for both PS2 titles) — fully solved — `docs/odinsphere/ps2/data-structure.md` §3-4, `docs/grimgrimoire/ps2/data-structure.md`, `tools/shared/rofs-cvm.ts`
- CRI **CPK** (`@UTF` TOC + CRILAYLA; UTF encryption optional per game — DC encrypts, GKH doesn't) — solved — `docs/dragonscrown/ps3/data-structure.md`
- CRI audio **ADX/AFS/ACB/AWB** (AWB = AFS2 *or* nested-CPK/ITOC; ACB positional cue↔waveform pairing, no cue-graph interpreter; HCA/ATRAC3 decode out of scope) — shipped — `docs/audio-format.md`
- **FMBP/FMBS** "paper-doll" sprite models — four layouts: PS2 FMBP (LE, VIF-packed), PS3 FMBS (BE, 0xE4 header), Wii FMBS (BE, 0xA0 header at FMBP positions), Switch FMBS (LE, 0x120 header, u64 offsets, normalized UVs) — render-verified — `docs/fmbp-model-format.md`, `tools/shared/fmbp.ts`, `tools/shared/switch-cpk-models.ts`
- Switch `FTEX`/`FTX0`/`.tex` (NVT) Tegra X1 block-linear BC3/BC4/BC7 (7,301/7,301 payloads) — solved — `docs/switch-ftx-nvt-format.md`, `tools/shared/switch-nvtx.ts`
- Wii RVZ → decrypted partition → FST extraction; `FCMP` container (LZSS-style, 0xFEE dict start); `RSTM` audio — `docs/muramasa/wii/data-structure.md`, `tools/muramasa/extract.py`

## Engine-family / cross-project links
- House formats cross generations: `FTEX` (Odin `.FTP` = DC `.ftx` = Switch), `FMBP`→`FMBS` (distinct sibling magic, per-platform header layouts). Text did not survive: Odin `FECD` vs DC `FMSB`; `ps2_DTPK` has no DC equivalent.
- CRI stack is per-title configurable (CVM on PS2, CPK on PS3/PSP/Switch) — never assume a container shape transfers.
- CVM passwords for other CRI titles: Emu-Land thread "Пароли для архивов .CVM (CRI ROFS)" (Yakuza 1/2 `qi2o@9a!`, .hack//G.U. `cc2fuku`, Arcana Heart `zxcv`, PSU `4147a5c2b5fe0357`, …).
- tri-Ace VP2 (`valkyrie`) is a different PS2 container family (XOR TOC + SLZ). Third-party oracles: roxfan `cvm_tool` (fork `JayFoxRox/cvm_tool`), `vgmstream-cli`, `texture2ddecoder-wasm`.

## Reusable code in this repo
- `tools/shared/rofs-cvm.ts` — CRI CVM descrambler/reader; `tools/shared/afs.ts` — AFS archive
- CRI CPK/`@UTF`/CRILAYLA/ADX/ACB/AWB now in `@seer-project/cri` (was `tools/shared/{cri-cpk,adx,acb,awb}.ts`)
- `tools/shared/fmbp.ts` — PS2/PS3/Wii FMBP/FMBS decoder (header layout auto-detected from `headerSize`)
- `tools/shared/switch-nvtx.ts` — Tegra X1 deswizzle; `tools/shared/switch-game-assets.ts` — locale-namespaced publisher
- `tools/shared/manifest-assets.ts` (`upsertManifest()`) — never write `manifest.json` directly
- `tools/muramasa/extract.py` — generic Wii RVZ → partition → FST extractor

## Know before you start
- Audio is decoded live: manifests carry byte ranges into `/data/*` (HTTP Range), never raw audio in `public/assets/` (`docs/architecture-overview.md`).
- Platform-port traps in FMBS: alpha `0xFF==1.0` (not PS2 `0x80`); PS3 part `uv` high 16 bits = undecoded selector; Switch UVs normalized `[0,1]`; Switch `page` field at `+7`.
- Tegra block height is per-texture (`min(16, next_pow2(ceil(blockRows/8)))`); solid `#00FF00` padding is authored chroma-key, not corruption.
- Localized CPKs reuse base relative paths — namespace by locale (`wwise-shared-short-id-across-language-variants.md`).
- `extract.py` flattens directories and drops 21 same-named `.mbs` (642 declared, 621 on disk); `KisukeB_npc00.mbs` renders as a blur (open).

## Lessons sourced from this corpus
`directory-align-field-scoped-to-payload-not-table.md`, `platform-port-swaps-adjacent-header-fields.md`, `flat-directory-extraction-collapses-same-named-siblings.md`, `wwise-shared-short-id-across-language-variants.md`, `normalized-uv-passes-structural-checks-renders-blank.md`, `header-field-role-not-transitive-across-sibling-format.md`
