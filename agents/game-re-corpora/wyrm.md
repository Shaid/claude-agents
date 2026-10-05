# wyrm — Dune, KGB (Cryo)

**Project root:** `~/Development/wyrm` · **Full history/evidence:** `game-re-corpora/details/wyrm.md` (read on demand) · **Open work:** `docs/dune/TODO.md`, `docs/kgb/TODO.md`

## Games
- Dune (`dune`: `amiga`, `dosvga`) — shared Cryo container; DOS `.SAL` rooms 48/48 composited; ornithopter + strategic map traced
- KGB / "Conspiracy" (`kgb`: Amiga + DOS) — substantially solved: codecs, rooms, `.cma` script VM, dialogue graph; DOS `.M32` music open

## Solved formats → where documented
- HSQ in-place LZSS (20-bit headers, checksum) — `docs/dune/amiga/hsq.md`, `src/formats/hsq.ts`
- Cryo image/bank/sprite container, Amiga BE + DOS LE (`parseCryoImage(data, { endian })`) — confirmed — `docs/dune/amiga/{bank,sprite,palette,animation}.md`, `docs/dune/dosvga/{sprite,palette}.md`, `src/formats/cryo-image.ts`
- DOS `.SAL` vector room scenes (polygons/gradients/LFSR dither/sprite placements; bank slot = `0x13 + ((roomNo−1)>>4)`); `SKY.HSQ` 33 outdoor palettes — solved, 4 rooms screenshot-confirmed, 14 bank bindings inferred — `docs/dune/dosvga/room.md`, `src/formats/cryo-sal.ts`
- Amiga ornithopter view (corrected 2026-09): `ornycab` = dialogue-gated landmark illustration (4 gates), `dunes`/`dunes3` = software-scaled parallax scenery by travel mode, `ornypan` = travel/destination menu with blinking cursor, `orny`/`ornytk` = 4-frame subset / 23-frame takeoff arc — `docs/dune/amiga/ornithopter.md`
- Amiga strategic map: `command1.hsq` string pool (319 strings, cross-port identical), `map.hsq`/`map2.hsq` grids with width-398 wraparound, `tablat.bin` 99×8 row table, `onmap`/`attack` via self-patched trampoline; `globdata.hsq` and cell pixel decode open — `docs/dune/amiga/strategic-map.md`, `src/formats/cryo-strings.ts`
- KGB exe self-decruncher (bespoke LZ77/Huffman) — `tools/kgb/decrunch-hunk4.ts`, `docs/kgb/executable.md`
- KGB `LAB_0547`/`LAB_0559` LZ codec family (`.scr`, `.32x`/`.anc`/PAC) — byte-identical vs Python reimpl — `tools/kgb/cryo-lz.ts`
- KGB rooms composed at runtime from `PAC/chap{n}.pac`/`map{n}.pac` (44,440/47,680 px vs savestate); one fixed 32-colour exe palette — `docs/kgb/room-rendering.md`
- KGB `.cma`: 16-slot BE16 offset header (sort by offset), state-cell accessor `LAB_04DA`/`LAB_04DB`, 26-opcode script VM (8290/8290 blocks), `SAY` → `.phz` 96.9% — `docs/kgb/cma.md`, `tools/kgb/cma-script.ts`
- KGB dialogue graph (room+hotspot+actor+bytecode; `LAB_02C5` link = settled negative; `OBJ0`/`OBJ1` edge = candidate only) — `docs/kgb/dialogue-graph.md`, `tools/kgb/dialogue-graph.ts`
- KGB DOS `PAC` chunky pixels + `.SQX` container — `tools/kgb/dos-pixel.ts`

## Engine-family / cross-project links
- Dune and KGB are sibling Cryo engines. DOS ports swap adjacent header bytes (`[height][paletteBase]`) rather than pure endian-flip (`platform-port-swaps-adjacent-header-fields.md`).
- Amiga Dune community disassembly labels are not ground truth (`ira-label-name-is-not-a-literal-address.md`).

## Reusable code in this repo
- `src/formats/hsq.ts`, `cryo-image.ts`, `cryo-sal.ts`, `cryo-strings.ts` — Cryo decoders
- `tools/kgb/cryo-lz.ts` — KGB LZ codec family

## Know before you start
- DOS palette block list ends on `0xFFFF`, not Amiga's `start >= 0x80`; DOS `paletteBase` is a full byte.
- Dune DOS exe: `DS:0` = file `0xEEF0` (`DS = loadseg + 0x0ECF`) — `game-re-tooling/dos.md`.
- Asset shape alone misled the first ornithopter pass — read the real consumer code; a player's account is a strong prior worth re-verifying.
- Amiga Dune: zero blitter/Copper usage; screen loader `LAB_0BEC` caches IDs < 86, `LAB_0C95` handles ≥ 86.
- KGB runtime work: `data/kgb/derived/kgb-decrunched.{exe,asm}`; locate live file bases in savestates by multi-needle agreement.
- Two byte-shuffle dispatches with identical arithmetic belong to different subsystems (state-cell accessor vs hotspot id classification) — don't conflate.

## Lessons sourced from this corpus
`platform-port-swaps-adjacent-header-fields.md`, `palette-block-terminator-inherited-from-narrower-palette-port.md`, `command-discriminator-on-wrong-byte-closes-byte-exact-fakes-registry.md`, `same-name-cross-port-colour-mismatch.md`, `ira-label-name-is-not-a-literal-address.md`, `hand-traced-byte-shuffle-needs-independent-resimulation.md`, `multi-needle-agreement-arbitrates-runtime-base-address.md`, `documented-cross-table-pairing-is-not-a-length-bound.md`
