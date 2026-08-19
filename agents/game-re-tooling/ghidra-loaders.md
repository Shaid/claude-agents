# Tooling — Ghidra platform loaders

`Read` this when your target's executable format is one Ghidra won't open
natively, or when a raw-binary import is losing you segment layout,
relocations or symbols. A loader that knows the format gives you correct
segment bases and entry points for free — which is usually the difference
between a readable disassembly and one whose xrefs all point at nothing.

Radare2 remains the default for interactive work on the platforms that have
native or near-native support (see `amiga.md`, `psx.md`, `snes.md`); reach for
Ghidra when you specifically want a decompiler, or when the container format
needs a real loader (encrypted/compressed headers, multi-segment executables,
symbol tables radare2 doesn't parse). For the actual driving mechanics —
connecting to GhidraMCP, headless batch analysis, when to fall back to the
GUI — see the `ghidra-disasm` agent; this file is the loader/platform
reference it and `game-re` both read.

All of this targets the local install at `~/ghidra_12.1.2_PUBLIC`. The real
per-user extensions directory is `~/.config/ghidra/ghidra_12.1.2_PUBLIC/Extensions/`
(this build resolves the XDG-style path, not the legacy `~/.ghidra/.ghidra_12.1.2_PUBLIC/`
one — confirmed via its own application.log and real project history), with
general user scripts in `~/.config/ghidra/ghidra_12.1.2_PUBLIC/ghidra_scripts/`.
Most platform scripts below instead ship inside their own extension's bundled
`ghidra_scripts/` folder (Ghidra auto-registers each extension's own script
dir), which is where to look first. Amiga has a working loader too —
`ghidra-amiga`, see the table below — it is not a gap.

## Installed extensions

| Platform | Extension | Source repo (checked out under `~/Development/ghidra-extensions/`) | Notes |
|---|---|---|---|
| PSX | `ghidra_psx_ldr` | [lab313ru/ghidra_psx_ldr](https://github.com/lab313ru/ghidra_psx_ldr) | Loads `PS-X EXE`, PSYQ library/OBJ signature matching, GTE macro decompilation, overlay handling. Radare2 already auto-detects `PS-X EXE` with zero config — reach for this loader when you want decompilation or PSYQ symbol recovery instead |
| PS2 | `ghidra-emotionengine-reloaded` | [chaoticgd/ghidra-emotionengine-reloaded](https://github.com/chaoticgd/ghidra-emotionengine-reloaded) | MIPS R5900 with VU macromode, PS2 ELF and IRX loaders. Turn off the Decompiler Parameter ID analyzer and enable the deprecated demangler for correct output — see `ps2.md` |
| PS4 | `GhidraOrbis` | [astrelsky/GhidraOrbis](https://github.com/astrelsky/GhidraOrbis) | Orbis OS formats. **Does not decrypt SELF** — needs an already-decrypted ELF as input. Fixed one upstream bug this session: `StackChkFailAnalyzer` was calling instance `getName()` instead of the existing static `NAME` field (PR #29 regression, unrelated to Ghidra's own API) |
| Wii / GameCube | `GameCubeLoader` | [Cuyler36/Ghidra-GameCube-Loader](https://github.com/Cuyler36/Ghidra-GameCube-Loader) | DOL/REL/Apploader. Not empirically smoke-tested against a live binary import this session — verify before trusting blindly |
| Genesis / Mega Drive | `ghidra_sega_ldr` | [lab313ru/ghidra_sega_ldr](https://github.com/lab313ru/ghidra_sega_ldr) | Headered `.bin`/`.md` ROM loader. **This closes a previously-documented gap** — earlier surveys (and `genesis.md`) said no Genesis Ghidra loader existed; that was true until this session. 68000 CPU support itself is stock Ghidra, only the container format needed a loader |
| Switch | `SwitchLoader` | [Adubbz/Ghidra-Switch-Loader](https://github.com/Adubbz/Ghidra-Switch-Loader) | NSO/NRO. First-party-NRO handling included. Built clean but trimmed a naive `runtimeOnly fileTree(...)` dependency that was pulling in every other installed extension's jars (49MB bloated zip, duplicate `lz4-java`) — the installed copy is a manually assembled clean directory |
| PSP | `ghidra-allegrex` | [kotcrab/ghidra-allegrex](https://github.com/kotcrab/ghidra-allegrex) | Allegrex CPU module (MIPS-derived, PSP-specific instructions). Pair with the NID/HW-register scripts below. `psp.md` has the `fileOffset = vaddr + 0x60` ELF convention and cross-module NID-call resolution |
| 3DS | `ghidra-ctr-loader` | [Martmists-GH/ghidra-ctr-loader](https://github.com/Martmists-GH/ghidra-ctr-loader) | CXI (direct import), CIA (decrypted-only, first container only), CRO/CRS (multi-file linking works; `.bss`/relocations and multiple `.rodata`/`.data` sections in `static.crs` are explicitly unimplemented upstream). No decryption — pre-decrypted CXI/CIA input required |
| Xbox 360 | `XEXLoaderWV` | [zeroKilo/XEXLoaderWV](https://github.com/zeroKilo/XEXLoaderWV) | XEX2/XEXP. Unlike PS3/PS4/3DS, this fork **does self-decrypt** retail and devkit keys — no external decryption step needed |
| Amiga | `ghidra-amiga` | Author "Bartman/Abyss" per its own `extension.properties`; its bundled `README.md` says it builds on [lab313ru/ghidra_amiga_ldr](https://github.com/lab313ru/ghidra_amiga_ldr) and apparentlymart's `ghidra-amiga-whdload`. Installed from a pre-built `ghidra_12.0.1_PUBLIC_*_ghidra-amiga.zip` in `~/Downloads` — no local source checkout, so its own repo URL isn't confirmed; don't invent one | HUNK executable loader, bundled Amiga NDK 3.9 datatypes (`amiga_ndk39.gdt`) for accurate struct typing, WHDLoad-lineage support. Ships its own `ghidra_scripts/` (`ApplyRegBase.java`, `CopperList.java`, `ExportFunctionsHeadless.java`). Confirmed working — real project history exists (`~/Development/ghidra-projects/blackcrypt`), including successful headless exports on other platforms via the bundled script. Built for 12.0.1; runs fine under 12.1.2. Owned operationally by the `amiga-disasm` agent, not `ghidra-disasm` — see `amiga.md` |
| MCP bridge | `GhidraMCP` | pre-built from `~/Development/ghidra-mcp` | See the `ghidra-disasm` agent for how to actually connect a session to it — it's not registered as this session's MCP server by default |
| — | `Jython` | official optional extension zip | Enables `.py`-script execution in Ghidra's Script Manager. Required by the Atari PRG import script and by the PSP NID-resolver scripts (Python 2 syntax) below — Ghidra 12.x no longer ships Jython by default, the default scripting runtime is PyGhidra (Python 3) |

SNES support (`ghidra-snes`) is also installed — adds the 65816 processor
module Ghidra doesn't ship natively, which is also what Apple IIGS needs (see
Gaps below). See `snes.md` for radare2's own M/X flag-width blind spot, which
this doesn't fix — this is purely the CPU language module for Ghidra.

## General user scripts (not extension-bundled — live in `ghidra_scripts/`, need Jython)

| Script | Platform | Purpose |
|---|---|---|
| `ImportAtariPRG.py` | Atari ST | GEMDOS `.PRG` loader. No compiled-extension equivalent exists; see `atari-st.md` |
| `SonyPSPResolveNIDs.py` | PSP | Resolves NIDs against the bundled `ppsspp_niddb*.xml` / `500_psplibdoc_191008.xml` databases |
| `SonyPSPMapHWRegisters.py` | PSP | Maps hardware register addresses |

## `Loader.ImporterSettings` — the Ghidra 12.x API break to know about

Ghidra 12.x changed `AbstractLibrarySupportLoader.load()`'s signature from
the old six-parameter form
(`load(ByteProvider, LoadSpec, List<Option>, Program, TaskMonitor, MessageLog)`)
to a single consolidated `load(Program program, Loader.ImporterSettings settings)`,
where `ImporterSettings` is a record exposing `.provider()`, `.loadSpec()`,
`.options()`, `.monitor()`, `.log()` plus new fields (`project`,
`projectRootPath`, `mirrorFsLayout`, `consumer`). This broke `ghidra_sega_ldr`
and `ghidra-ctr-loader` on first build attempt (both fixed this session — see
their source under `~/Development/ghidra-extensions/`, both fixes are a
handful of lines: add the `Loader.ImporterSettings` import, change the method
signature, pull the old parameters off `settings` at the top of the method
body). If a **new** loader extension fails to build against 12.1.2 with an
error about `load()` not overriding/implementing anything, check for this
exact pattern first — it's now proven twice and is the most likely cause.

A smaller, unrelated 12.1.2 drift: `ByteProvider.length()` no longer declares
`throws IOException`. This broke `Ghidra-Switch-Loader`'s `NXOAdapter.java`
(an invalid `try/catch` around a call that can no longer throw) — fixed by
just removing the dead catch.

## Gaps

- **PS3 (SELF/SPU)** — skipped this pass. [GhidraSPU](https://github.com/aerosoul94/GhidraSPU)
  exists for the Cell SPU processor module (PPU side is stock PowerPC) but is
  upstream work-in-progress with missing vector instructions; not installed.
  `ps3.md` covers the from-scratch PKG/EDAT decryption path, which is
  independent of this gap.
- **Apple IIGS** — no OMF executable loader exists anywhere in the public
  ecosystem. `ghidra-snes` gives you the raw 65816 processor module (same CPU
  family), but there's no loader to parse an IIGS OMF binary's segment
  headers — a raw-binary import loses all of that. Confirmed gap, not
  something worth re-searching without new information.
- **PS Vita, PS5, Saturn, DS, N64** — not requested/installed this pass, but
  loaders exist and were verified to exist at survey time (not verified
  buildable against 12.1.2): [VitaLoaderRedux](https://github.com/CreepNT/VitaLoaderRedux),
  [GhidraProspero](https://github.com/astrelsky/GhidraProspero) (pair with
  [libNidResolver](https://github.com/astrelsky/libNidResolver)),
  [Ghidra-SegaSaturn-Loader](https://github.com/VGKintsugi/Ghidra-SegaSaturn-Loader)
  (no `saturn.md` exists yet), [NTRGhidra](https://github.com/onepiecefreak3/NTRGhidra),
  [Ghidra-RSP](https://github.com/Random06457/Ghidra-RSP) (RSP coprocessor
  only, main CPU is stock MIPS).
- **PS2 `.mdebug` symbols** — [ghidra_mdebug](https://github.com/astrelsky/ghidra_mdebug)
  recovers real function/variable names from a build's STABS debug info when
  present; not installed, worth adding if a PS2 target turns out to have
  shipped with `.mdebug` intact.
- **Any platform, delinking** — [ghidra-delinker-extension](https://github.com/widberg/ghidra-delinker-extension)
  delinks an executable back into relocatable object files (ELF/PE); not
  installed, the enabling step if a project ever needs to recompile or relink
  extracted functions.

Source for the original survey: `awesome-game-file-format-reversing`
(surveyed 2026-08). Installed-extension rows above are verified by actually
building and installing them this session, not just surveyed; unlisted rows
in Gaps are leads only — check against the repo before relying on a stated
capability.
