# Amiga hardware specifics

**When it bites:** decoding EHB (half-bright) colour, computing blitter sizes/modulos, or scaling 12-bit colour — don't trust memory, verify against `amigadocs` via the openground MCP (see Tooling map in `game-re.md`).

- EHB half-bright is computed **on the nibble**: `(nibble >> 1) * 17`, never
  `(scaled_8bit) >> 1` — the latter is off by up to 8/channel on odd nibbles.
- `BLTSIZE = (height << 6) | width_in_words`.
- Blitter modulos are per-row byte offsets, and can be negative.
- Rows are word-aligned.
- 12-bit colour scales as `nibble * 17`.
