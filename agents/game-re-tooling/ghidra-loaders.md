# Tooling — Ghidra / IDA platform loaders

`Read` this when your target's executable format is one Ghidra or IDA won't
open natively, or when a raw-binary import is losing you segment layout,
relocations or symbols. A loader that knows the format gives you correct
segment bases and entry points for free — which is usually the difference
between a readable disassembly and one whose xrefs all point at nothing.

Radare2 remains the default for interactive work here (see `amiga.md`,
`psx.md`, `snes.md`); this table is for when it can't parse the container at
all, or when you specifically want a decompiler.

## Loaders by platform

| Platform | Loader | Notes |
|---|---|---|
| PSX | [ghidra_psx_ldr](https://github.com/lab313ru/ghidra_psx_ldr) | Loads `PS-X EXE`, plus PSYQ library/OBJ signature matching, GTE macro decompilation and overlay handling. The most mature entry in this table (319★, 285 commits). Radare2 already auto-detects `PS-X EXE` with zero config — reach for this when you want Hex-Rays-style decompilation or PSYQ symbol recovery |
| PS2 | [ghidra-emotionengine-reloaded](https://github.com/chaoticgd/ghidra-emotionengine-reloaded) | MIPS R5900 with VU macromode, plus PS2 ELF and IRX loaders |
| PS2 | [ghidra_mdebug](https://github.com/astrelsky/ghidra_mdebug) | `.mdebug` symbol format — recovers real function/variable names when a build shipped them |
| PS3 | [GhidraSPU](https://github.com/aerosoul94/GhidraSPU) | Cell SPU processor module (the PPU side is stock PowerPC) |
| PS4 | [GhidraOrbis](https://github.com/astrelsky/GhidraOrbis) | Orbis OS formats |
| PS5 | [GhidraProspero](https://github.com/astrelsky/GhidraProspero) | Prospero OS; pair with [libNidResolver](https://github.com/astrelsky/libNidResolver) for NID→name resolution |
| PSP | [ghidra-allegrex](https://github.com/kotcrab/ghidra-allegrex) | Allegrex CPU module |
| PS Vita | [VitaLoaderRedux](https://github.com/CreepNT/VitaLoaderRedux) | ELF-PRX loader; successor to the deprecated VitaLoader |
| Saturn | [Ghidra-SegaSaturn-Loader](https://github.com/VGKintsugi/Ghidra-SegaSaturn-Loader) | No `game-re-tooling/saturn.md` exists yet — this is the starting point if a Saturn target turns up |
| GameCube / Wii | [Ghidra-GameCube-Loader](https://github.com/Cuyler36/Ghidra-GameCube-Loader) + [ghidra-gekko-broadway-lang](https://github.com/aldelaro5/ghidra-gekko-broadway-lang) | Loader and the Gekko/Broadway processor language — you want both |
| Nintendo DS | [NTRGhidra](https://github.com/onepiecefreak3/NTRGhidra) | |
| Nintendo 64 | [Ghidra-RSP](https://github.com/Random06457/Ghidra-RSP) | RSP coprocessor only; the main CPU is stock MIPS |
| Switch | [Ghidra-Switch-Loader](https://github.com/Adubbz/Ghidra-Switch-Loader) | NCA/XCI |
| Xbox / Xbox 360 | [idaxex](https://github.com/emoose/idaxex) (IDA 9, plus an `xex1tool` CLI), [XEXLoaderWV](https://github.com/zeroKilo/XEXLoaderWV) (Ghidra) | XEX/XBE |
| Any | [ghidra-delinker-extension](https://github.com/widberg/ghidra-delinker-extension) | Delinks an executable back into relocatable object files (ELF/PE) — the enabling step for recompiling or relinking extracted functions |

## Gaps worth knowing

- **No Amiga HUNK loader in any public list surveyed** — but one is already
  checked out locally at `~/Development/ghidra_amiga_ldr`. Radare2 cannot
  parse HUNK either (`amiga.md`), so for Amiga the working path stays IRA for
  static disassembly plus radare2 on a flat-mapped image.
- **No Atari ST, Apple IIGS or Genesis/68k loader** in the surveyed
  collections. For Genesis see `genesis.md`'s own reference set.

Source: `awesome-game-file-format-reversing` (surveyed 2026-08). Only the
PSX entry has been verified directly; treat the rest as leads to check
against the repo before relying on a stated capability.
