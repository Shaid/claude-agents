# Recompilation landscape (native-port stretch goals)

> Moved verbatim from the always-loaded `game-re.md` during the 2026-10 restructure. `game-re.md` keeps the condensed rules; this file holds the full worked examples behind them. Read the section you need.

If a task's stretch goal extends past asset extraction to a **native
recompiled port**, don't re-derive the landscape from scratch — a growing
survey series already covers it, one doc per platform plus two
cross-platform technique docs, all in `~/Development/seer/docs/`:

| Platform / topic | Doc | Verdict |
|---|---|---|
| PS3 | `ps3-recomp.md` | Cell BE/SPUs are the hard part; `ps3recomp` is early-but-real general prior art |
| PS2 | `ps2-recomp.md` | OpenGOAL/Jak trilogy is a real success but franchise-specific; VU1 is the general blocker |
| PSX | `psx-recomp.md` | Most tractable of the "hard" platforms; mature per-title decompilation scene, no general tool |
| PS4 | `ps4-recomp.md` | Not a CPU problem (already x86-64/GCN) — Orbis OS/GNM is the obstacle; HLE emulation (shadPS4), not recompilation. Includes a Bloodborne case study |
| Amiga | `amiga-recomp.md` | Essentially unstarted; custom chipset (Copper/Blitter) undercuts the payoff |
| SNES | `snes-recomp.md` | Cartridge coprocessors (SuperFX/SA-1/DSP-1) are the hard part; `SNESRecomp` exists (alpha) |
| Genesis/Mega Drive | `megadrive-recomp.md` | Ahead of Amiga despite sharing 68k; `SegaGenesisRecomp` is real |
| Saturn | `saturn-recomp.md` | Likely behind even Amiga — Saturn's own accurate emulation is still unsettled |
| GBA | `gba-recomp.md` | Most tractable 32-bit platform surveyed; the `pret` decomp scene is extremely mature |
| Nintendo DS | `nds-recomp.md` | Rides GBA's momentum on decomp; behind on binary recompilation (dual CPU + real 3D engine) |
| GameCube / Wii | `gamecube-wii-recomp.md` | Likely the strongest decomp scene in the series — the original CodeWarrior compiler still runs |
| 3DS | `3ds-recomp.md` | Essentially unstarted; post-Citra-shutdown, mature emulation removes the incentive |
| Wii U | `wiiu-recomp.md` | Near-unstarted despite the PPC lineage — CodeWarrior advantage doesn't transfer; Cemu's success suppresses the need. One 11-commit proof of concept (`nWiiURecomp`) does exist |
| MS-DOS | `dos-recomp.md` | **Ahead of Amiga** and the most tractable substrate in the series — `M-HT/SR` ships four native commercial-game ports (Albion, both X-COMs, Warcraft) via LLVM. Real technique, no scene. Absent from GitHub's `static-recompilation` topic, which is why topic-only scans miss it |
| Switch | `switch-recomp.md` | First real ARM64 target in the series; also the most legally fraught platform (Yuzu/Ryujinx shutdowns) |
| Arcade (all eras) | `arcade-recomp.md` | Mostly a crosswalk to the docs above (same silicon as many home platforms); hardware-encryption CPUs and the JOTEGO/MiSTer FPGA scene are the genuinely arcade-specific parts |
| Engine-based porting (Unreal/Unity, any platform) | `engine-based-porting.md` | Technique doc, not platform-specific — rehost recovered assets/scripts on a real PC engine build instead of lifting binary code |

This only matters when the project's own corpus file
(`game-re-corpora/<project>.md`) says a recompilation stretch goal applies —
most tasks are pure asset-extraction work where none of this is relevant,
and this table isn't part of the mandatory-reads in §"Before you start."
