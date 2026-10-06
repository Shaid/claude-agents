# hunter — Hunter, Carrier Command, Epic, Wings, Frontier: Elite II, Midwinter 1/2, Gunship 2000 AGA, Embryo, Zeewolf, Virus (Amiga; Hunter also Atari ST)

**Project root:** `~/Development/hunter` · **Full history/evidence:** `game-re-corpora/details/hunter.md` (read on demand) · **Open work:** `docs/explore/<Game>/TODO.md` per game (Hunter: `docs/hunter/TODO.md`)

Registered viewer ids (`src/game-id.ts`): `hunter`, `carrier-command`, `epic`, `wings`, `frontier`, `midwinter`, `midwinter2`, all `amiga`. Others are docs/tools only.

## Games
- Hunter (Amiga + Atari ST) — OB 3D format confirmed; ST file table, FIRE depacker, saves solved
- Carrier Command (Amiga) — 3D pipeline/BSP confirmed; 4 static models; spawn callback needs live capture
- Epic (Amiga, Ocean 1992) — `.3D`/`.IGD` display-list bytecode confirmed; colour args open
- Wings (Amiga, Cinemaware) — `.BOLT` archive, Mode-B codec, palettes, `pilot.dat`, dogfight renderer solved
- Frontier: Elite II (Amiga) — model bytecode + scene graph + glTF shipped; savegame solved
- Midwinter (Amiga) — NDOS disk, resource table, terrain seed+fractal confirmed; vehicle models open
- Midwinter 2 (Amiga) — dir files, `.cmp`/`.mcp`/`.fsd` codecs, island sections, terrain solved; audio samples open
- Gunship 2000 AGA — `.PIX` (RNC1 ILBM), `.cat` catalog, roster partial, SFX engine
- Embryo (Amiga, 1994) — XOR-obfuscated CrM2 container + file catalog solved; 3D engine exe not found
- Zeewolf — boot catalog + custom disk layout; 64% of disk uncharacterised
- Virus — reasoned negative: no stored 3D model format (fully procedural)
- Also present, not in details file: ArmourGeddon 1/2, Guardian AGA, Zeewolf 2 (`docs/explore/<Game>/`)

## Solved formats → where documented
- RNC1 (`tools/hunter/rnc1.py`, byte-verified; reused for Gunship `.PIX`) and FIRE backwards LZ77, no Huffman (`tools/hunter/fire-depack.py`)
- Hunter "OB" objects (Amiga = ST layout) — confirmed code-level — `docs/formats/hunter-ob.md`, `docs/3d-object-format.md`, `tools/hunter/ob-format.mjs`; ST file-descriptor table + checksums — `docs/data-format-reference.md` (§2.8 verifier)
- Carrier Command 3D/BSP/entity pools — `docs/explore/CarrierCommand/data-structure.md`
- Epic `.3D`/`.IGD` 25-opcode display list — confirmed — `docs/explore/Epic/epic-3d-format.md`, `tools/epic/epic_oplist.py`
- Wings `.BOLT` (trailer-pointer directory, Mode-B LZ, `flags1` 0x00 palette/0x05/0x06/0x12), `pilot.dat` — confirmed — `docs/explore/Wings/data-structure.md`, `tools/wings/bolt_{parse,decompress,palette}.py`
- FE2 savegame (self-keying cipher + zero-RLE) — `docs/formats/fe2-savegame.md`; Frontier models (32-opcode bytecode, 8 vertex encodings) + scene graph — byte-exact vs oracle — `docs/explore/Frontier/data-structure.md`, `tools/frontier/frontier_models.py`, `frontier_scenegraph.py`, `build-gltf.mjs`
- Midwinter terrain (50x50 seed, midpoint displacement) — confirmed — `tools/midwinter/terrain.py`; Midwinter 2 `.cmp` nibble-RLE (312/415 frames; `LAB_0BAF` variant open), `islandNN.bin` sections, `mw2map.bin` diamond-square — `tools/midwinter2/`, `docs/explore/Midwinter{,2}/data-structure.md`
- Gunship `.cat` catalog, `roster.dat` — `docs/explore/Gunship2000AGA/data-structure.md`
- Embryo CrM2 (XOR'd header) — `tools/embryo/crm2.py`, `docs/explore/EmbryoHr/data-structure.md`

## Engine-family / cross-project links
- Hunter Amiga↔ST share load base `$800` and source: map one from the other by anchor matching (`cross-platform-decode-oracles.md`).
- Braben lineage: Frontier stores models, Virus is purely procedural — don't transfer formats by lineage. Midwinter 1/2 share terrain-expansion shape, sprite-container shape and place-name strings, but are different codebases.
- Oracles: `watsonmw/fe2-intro` (spec only, no licence — no code copied; needs `-orig` patch for our exe), DOS-port fan decode (Midwinter), `ancient` (`tools/hunter/ancient`) for CrM2, WinUAE/amiberry `newcpu.cpp` for `.uss` savestates.
- Shared WHDLoad library + amiberry configs: `~/Development/amigagames`.

## Know before you start
- **Amiberry live capture needs explicit user approval; the repo owner banned it for Midwinter work.** Breakpoints kill the IPC socket — see `amiberry-live-capture-workflow.md`.
- Carrier Command: `data/explore/CarrierCommand/carrier.asm` is the compressed file — use `carrier-decompressed.asm`/`.cnf`.
- IRA `.cnf` forced `CODE` ranges: `ORG+offset` file math is invalid past hunk0, and labels are not literal addresses. For multi-hunk or overlay exes use the Ghidra HUNK loader (`amiga-disasm`); `ira` may be absent.
- Hunter ST disk is a cracked compilation: file `100` is Cybercon III, Hunter's exe is file `800`; trust the in-game file-descriptor table over filename/content sniffing.
- Byte-count invariants don't prove copy semantics (Wings codec had 2 bugs behind 352/352 length matches).
- New games must be registered in `src/game-id.ts` + `tools/shared/game-config.ts` (Frontier sat unregistered).

## Key lessons
- `amiberry-live-capture-workflow.md` — live capture needs approval; breakpoints kill the IPC socket
- `cross-platform-decode-oracles.md` — Hunter Amiga↔ST share load base; anchor-match one from other
- `forced-code-range-address-comments-unreliable-past-boundary.md` — IRA `.cnf` CODE ranges: `ORG+offset` invalid past hunk0
- `ira-label-name-is-not-a-literal-address.md` — IRA label suffixes are not literal addresses
- `committed-ira-asm-silent-coverage-gap.md` — committed `.asm` grep may miss unclassified code
- `length-invariant-blind-to-copy-semantics.md` — Wings codec had 2 bugs behind 352/352 length matches
- `crack-redirects-io-to-resident-loader-stub.md` — Hunter ST cracked compilation: trust the file-descriptor table, not sniffing
- `high-entropy-trivial-cipher.md` — Embryo XOR header and FE2 save cipher looked like compression
- `trailer-offset-locates-real-header.md` — Wings `.BOLT` directory is located via a trailer pointer
- `static-xref-misleads.md` — no symbols on these exes; xrefs and jump tables mislead

Full list: `details/hunter.md` § "Lessons sourced from this corpus (full list)".
