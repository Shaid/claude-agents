# wyrm — Dune, KGB (Cryo)

**Project root:** `~/Development/wyrm`

HSQ in-place LZSS (20-bit headers, checksum), bank/sprite/room formats, donor
palettes, `dir.0` catalogs, manifest-driven builds.

**Dune ships on both Amiga and DOS VGA, one shared Cryo container format
across both** (confirmed: identical frame directory, palette-command-stream
position, and character animation/place-list bytecode; `src/formats/cryo-image.ts`
`parseCryoImage(data, { endian: 'be' | 'le' })` decodes both from one
codebase). The two ports are **not** a pure byte-order flip of the same
struct, though — see
`~/.claude/agents/game-re-lessons/platform-port-swaps-adjacent-header-fields.md`:
DOS's 4-byte sprite frame header swaps the trailing `[height][paletteBase]`
byte order relative to Amiga's `[paletteBase][height]`, and DOS's
`paletteBase` is a full unmasked byte (256-colour VGA palette) where Amiga's
is masked to a low nibble (32-colour hardware palette). Solved formats, full
byte-exact verification evidence, and remaining open items (DOS room
backgrounds, DOS donor/base-palette identity):
`docs/dune/dosvga/sprite.md`, `docs/dune/dosvga/palette.md`,
`docs/dune/TODO.md`. Amiga reference (already solved, same container):
`docs/dune/amiga/*.md`.
