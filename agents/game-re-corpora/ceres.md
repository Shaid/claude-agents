# ceres — Final Fantasy VI, IV, V (SNES)

**Project root:** `~/Development/ceres` · **Full history/evidence:** `game-re-corpora/details/ceres.md` (read on demand) · **Open work:** `docs/<game>/TODO.md` per game (`ffvi`, `ffiv`, `ffv`)

Per-game decoders live in `tools/<game>/`; format docs in `docs/<game>/snes/data-structure.md` (cited below by §).

## Games
- Final Fantasy VI (SNES, US "FFIII" Rev 1 `0xc0fa0464` + JP `0x45ef5ac8`) — `ffvi` — near-complete: gfx, maps, text, music, battle engine
- Final Fantasy IV (SNES, US "FFII" Rev 1 `0x23084fcd` + JP `0xCAA15E97`; **LoROM**) — `ffiv` — text, gfx, stats, SPC harness done
- Final Fantasy V (SNES, JP-only `0xc1bc267d`) — `ffv` — text, gfx, stats, music, EventScript VM done

## Solved formats → where documented
- FFVI LZSS (2KB ring, compressed-length header) — confirmed — §4; FFV LZSS is **not byte-compatible** (decompressed-size header, reversed token packing) — `docs/ffv/snes/data-structure.md`
- FFVI US text: DTE dialogue + separate fixed-length name alphabet — confirmed — §5; control codes `:b`/`:w` consume parameter bytes (`tools/ffvi/text.ts`)
- JP text systems: FFIV-J flat kana; FFV-J kana + 72-entry MTE; FFVI-J MTE + 2-byte kanji (`tools/ffvi/jp-dialogue.ts`, `jp-text.ts`) — confirmed — §15.3, §15.10
- FFVI graphics: portraits (tile-formation reorder) §6; monster/Esper stencil-trimmed tiles §8.1; field sprites + walk/flip frames (`field-sprites.ts`) §13; field maps/tilesets (`maps.ts`) §9; world map + minimap/sprites/Mode 7 backdrop (`world-map.ts`) §10; battle sprites §16 — confirmed by render + invariants
- FFVI data: `MonsterProp`, `MagicProp`, `ItemProp`, AI/battle-event/attack-animation script banks — confirmed — §8, §12, §16-17
- AKAO SPC700 drivers: FFIV V1, FFV V3, FFVI V4 (`AKAOSNES_V4_FF6`, not N-SPC); sequence decoders + real SPC700 boot-harness renderers (`tools/<game>/akao-spc-render.ts`) — confirmed — FFVI §18-19, FFV §12-13, FFIV §13; `docs/spc700-emulation.md`
- FFVI battle engine (ATB, AI, damage formula, status timers, counters, commands) — `tools/ffvi/battle-*.ts`, `attack-data.ts` — §20, `docs/ffvi/battle-engine-plan.md`
- FFIV: text pools/DTE, portraits, window font, battle char gfx §9, `CharProp`/`AttackProp`/`MonsterProp` (pointer-indexed, overlapping records) §10-12, JP-vs-US diff §8 — `docs/ffiv/snes/data-structure.md`
- FFV: MTE/kanji dialogue, monster gfx (big-endian pointer packing), job battle sprites §9, battle-stat tables §10, overworld EventScript VM (`tools/ffv/overworld-gfx.ts`) §11.2 — `docs/ffv/snes/data-structure.md`

## Engine-family / cross-project links
- Oracles: `github.com/everything8215/ff4`/`ff5`/`ff6` rebuild these exact ROMs byte-for-byte (CRC-matched). Each repo may hold a JSON rip definition **and** a full labelled 65816 + SPC700 disassembly (`sound/`, `notes/*-spc.asm`, `src/sound/ff*-spc.asm`) — check for both; clone and run its own rip (`make rip`, `decode-ff4.js`) as a byte-exact diff oracle.
- `vgmtrans/vgmtrans` `AkaoSnes/` (read the whole dir, incl. `AkaoSnesTrackLfo.cpp`) for driver signatures; it parses SPC rips, not ROM blobs.
- AKAO trilogy: V3/V4 share the 6-entry `InitTfrSrcTbl`/`InitTfrDestTbl` boot table; FFIV V1 uses plain IPL blocks; JP text complexity rises FFIV→FFV→FFVI — never carry a scheme over from a sibling.
- `ff6hacking.com` wiki used as a third cross-check source.

## Reusable code in this repo
- SNES tile/palette decoders (formerly `tools/shared/snes-ppu.ts`) now live in `@seer-project/snes` (`~/Development/seer/packages/snes/src/ppu.ts`, also `spc700-cpu.ts`)
- `tools/<game>/rom.ts` (`loadRomByCrc` — CRC32 allowlist ROM pick), `rom-addressing.ts` (LoROM/HiROM mapping)
- `tools/ffvi/battle-rng.ts` etc. — deterministic battle engine; all RNG through `FfviBattleRng`

## Know before you start
- Rip-definition `range` fields are LoROM **CPU addresses**, not file offsets (`((a&0xFF0000)>>1)+(a&0x7FFF)`). A correct table address in a rip JSON doesn't guarantee a correct record shape (FFIV `MonsterProp`).
- US vs JP builds: resolve records via their own pointers, not fixed offsets; constants pointing into **code** (e.g. FFVI bank `C0`, 0xCE shift) differ between releases — byte-diff renders, don't eyeball.
- SPC harness: force-call a source-confirmed idle-loop head (frequency histogram picked a subroutine interior on FFIV); per-channel vol/pan has no cold-boot default; ROM song blobs carry a 2-byte transfer-length prefix that SPC-rip parsers omit.
- radare2's SNES plugin returns `0xFF` for HiROM banks outside the header window — see `game-re-tooling/snes.md`.
- Hand-typed test expectations can encode the same wrong model as the code — re-derive from source order (FFVI damage pipeline, FFV VM).
- Multiple `.sfc`/`.smc` in one `data/` dir: always select by CRC.

## Key lessons
- `decoder-address-reuse-across-rom-release.md` — US/JP builds: constants pointing into code (bank C0) differ
- `fixed-offset-diff-across-builds-hides-pointer-shift.md` — resolve US/JP records via their own pointers, not offsets
- `multi-region-dir-ambiguous-rom-pick.md` — several `.sfc`/`.smc` per `data/` dir — always pick by CRC
- `session-persistent-channel-state-has-no-cold-boot-default.md` — SPC harness vol/pan stayed zero: no cold-boot default
- `reference-tool-parses-runtime-image-not-rom-blob.md` — ROM song blobs carry a 2-byte prefix SPC-rip parsers omit
- `test-fixture-encodes-same-wrong-model-as-implementation.md` — hand-typed FFVI damage/FFV VM expectations encoded the bug
- `escape-code-parameter-bytes-silently-misdecoded.md` — FFVI `:b`/`:w` control codes consume parameter bytes
- `variable-width-cpu-operand-width-is-the-instruction-site-mode.md` — 65816 battle math: width comes from REP/SEP at use site
- `tile-formation-table-not-raster-order.md` — FFVI portraits/monsters need the tile-formation reorder
- `romhacking-community-tools-first.md` — everything8215 rebuilds are byte-exact oracles — check them first

Full list: `details/ceres.md` § "Lessons sourced from this corpus (full list)".
