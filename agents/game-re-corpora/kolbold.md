# kolbold — D&D SoM + ToD (CPS2), Knights of the Round (CPS1), Golden Axe (System 16), Black Tiger (1987)

**Project root:** `~/Development/kolbold` · **Full history/evidence:** `game-re-corpora/details/kolbold.md` (read on demand) · **Open work:** `docs/<game>/TODO.md` per game (Golden Axe: `docs/goldenaxe/sys16/TODO.md`)

First MAME arcade-romset project in the account (data = `data/<game>/<platform>/<set>.zip`); general workflow in `game-re-tooling/mame-arcade.md`.

## Games
- D&D: Shadows over Mystara — `ddsom`/`cps2` — engine, music, stats, items, rooms, dragons solved; Green Dragon spawn unlocated
- D&D: Tower of Doom — `ddtod`/`cps2` — CPS2 stack reused; palette page 1, combat stats solved; pages 0/2/3 open
- Knights of the Round — `knights`/`cps1` — unencrypted; tiles, boot palette, OKI audio, task kernel, roster solved
- Golden Axe — `goldenaxe`/`sys16` — memory map, tiles, palette 0-511, uPD7759 solved; sprite palette, music open
- Black Tiger — `blktiger`/`arcade` — gfx, palette 896/1024, i8751 MCU, BGM grammar, dialogue solved

## Solved formats → where documented
- Romset container: every set CRC32-matched to MAME `ROM_START` — confirmed (each game doc)
- CPS2 68000 Feistel opcode cipher + 20-byte key — confirmed — `docs/ddsom/cps2/data-structure.md`, `docs/ddtod/cps2/data-structure.md`
- CPS1/CPS2 planar tiles + CPS2 unshuffle; CPS2 sprite Y-bit code extension, scroll bank mapper 3-way atlas split; sprite-blob `flag&3` bank, animation VM (§3.8) — confirmed — ddsom doc
- CPS1 palette word; ddsom 8 banks, ddtod page 1, knights boot table (`0x1554`) — confirmed; which bank is live per screen open — `docs/knights/cps1/data-structure.md` §2.3/3.3
- QSound signed-8-bit PCM, Z80 mailbox, CPS2 music sequences (1846/1846 tracks), ADSR tables — confirmed; base pitch-select open — ddsom §4.2.x
- ddsom content: class stats, HP table, boss name bridge 21/23, 10 pool names, stage-node tables, item icons, SCROLL3 room fill — §6.x; ddtod HP-init/player HP §7
- knights: OKI MSM6295 78 phrases §5, task kernel §2.5, name roster §6, scroll tilemap word
- Golden Axe `docs/goldenaxe/sys16/data-structure.md`: 315-5195 map, 3bpp tiles, 4bpp sprites, resistor-DAC palette, uPD7759 directory inside Z80
- Black Tiger `docs/blktiger/arcade/data-structure.md`: xBRG_444 palette §4, MCU table, YM2203 BGM grammar §2.1, dialogue (2nd alphabet page, not a cipher), shop price gate, PROM `bd02.9j`

## Engine-family / cross-project links
- `decodeTile()`/`GfxLayout` is a MAME `gfx_element::decode()` port — engine-agnostic (Black Tiger reused unmodified)
- ddtod reuses ddsom code except its pool finder (ddsom's signature misses 4 ddtod pools)
- `~/Development/vgmtrans` CPS1/CPS2 modules + per-game romset DB: check first (its ROM address space differs from ours)
- Oracles: MAME driver source, `historic-mame` key table (trust modern formula on `upper`), MacDonald's `s16b.txt`, published rosters
- Golden Axe Musashi harness follows crawl's `tools/bcdft_decompress/emu.c` pattern

## Reusable code in this repo
- `@seer-project/arcade` (`~/Development/seer/packages/arcade/src/`): `mame-zip`, `capcom/{decrypt,gfx,palette,rom-regions,qsound,qsound-driver,oki-adpcm}`, `sega/{system16-gfx,upd7759-adpcm}`. The details file's `src/assets/formats/*.ts` paths are stale
- Local `tools/shared/cps2/*` + `mame-zip.ts` remain (ddtod imports them); new CPS title only needs `tools/<game>/rom-map.ts`
- `tools/goldenaxe/emu/` — Musashi whole-program 68000 harness (MCU waits stubbed)

## Know before you start
- CPS2: decrypt raw un-byteswapped ROM; reset vector is opcode-space, data reads/tables come from the data image
- r2 z80 prints raw `jr`/`djnz` displacement — recompute targets; put `-a` before `--`
- Narrow censuses gave repeat false negatives: widen to absolute-long, all registers, `jmp`; bound caller censuses at the next dispatch entry
- Golden Axe: paletteram `$140000`, spriteram `$200000` (earlier swap overturned); i8751 programs the mapper; sprite segmentation is heuristic
- ddsom: debug-menu `BOSS`/`ESHL WORK` labels conflict with traced pool roles, unresolved
- No MAME/live capture; oracles are static (source, vgmtrans, decoded-audio stats)

## Key lessons
- `cps2-decrypt-input-must-be-raw-rom-bytes.md` — CPS2: decrypt raw un-byteswapped ROM bytes
- `m68k-reset-vector-is-opcode-space-other-vectors-are-data-space.md` — CPS2 reset vector is opcode-space; tables come from data image
- `cps2-gfx-needs-extra-unshuffle-pass.md` — CPS2 tiles render as grid noise without the unshuffle
- `r2-arch-flag-before-dashdash-file-separator.md` — r2 z80/MCU: put `-a` before `--` or reads go flat
- `narrow-opcode-form-census-false-negative.md` — narrow censuses gave repeat false negatives here
- `unbounded-caller-census-crosses-sibling-routine-boundary.md` — bound caller censuses at the next dispatch entry
- `engine-implements-cooperative-task-kernel.md` — zero direct callers: knights runs a task kernel
- `debug-menu-label-vs-traced-consumer-conflict.md` — ddsom `BOSS`/`ESHL WORK` labels conflict with traced roles
- `reference-tool-own-loader-address-space-differs-from-yours.md` — vgmtrans CPS ROM address space differs from ours
- `negative-from-addressing-root-not-shapes.md` — static-only oracles: "no reader" claims need addressing-root search

Full list: `details/kolbold.md` § "Lessons sourced from this corpus (full list)".
