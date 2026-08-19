# vanille — Odin Sphere (PS2), Grim Grimoire (PS2), 7 Vanillaware titles registered

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

## Sibling links

- **House formats cross generations (verified 2026-08-12 by extracting
  real Dragon's Crown PS3 CPK files and comparing magics):**
  - `FTEX` textures: Odin `.FTP` (601) **and** Dragon's Crown PS3 `.ftx`
    (605) both start `FTEX` — same format family, header layout differs
    per port (Odin's 2nd u32 `0x8084` vs DC's `0xc006e000`-shaped
    fields; treat as a per-platform variant, see
    `game-re-lessons/platform-port-swaps-adjacent-header-fields.md`).
  - `FMBP` model packs: Odin `.MBP` **and** DC `.mbs` both start `FMBP`
    — the DC doc's earlier "FMBS" guess was wrong, the magic is FMBP.
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
  _MLI, i.e. the same house formats as Odin/Grim re-magicked),
  **RSTM** (.brstm Wii DSP ADPCM audio, 1,206), dev file lists leaking
  the project codename "NinPri". The RVZ→partition pipeline generalizes
  to any Wii RVZ dump.
- tri-Ace's VP2 (valkyrie corpus) is a *different* PS2 container family
  (XOR TOC + SLZ) — Vanillaware ≠ tri-Ace on PS2.
- `tools/shared/cri-cpk.ts` (Dragon's Crown/GKH CPK) and
  `tools/shared/rofs-cvm.ts` (Odin/Grim CVM) are the two CRI-shared
  decoders in this project.
