# Amiga hardware specifics

**When it bites:** decoding EHB (half-bright) colour or sizing an EHB image's planes, computing blitter sizes/modulos, or scaling 12-bit colour — don't trust memory, verify against `amigadocs` via the openground MCP (see Tooling map in `game-re.md`).

- EHB half-bright is computed **on the nibble**: `(nibble >> 1) * 17`, never
  `(scaled_8bit) >> 1` — the latter is off by up to 8/channel on odd nibbles.
- **EHB plane count is not log2(stored palette entries).** An EHB image
  stores 32 colour registers but has **6** planes (plane 6 selects
  half-bright). A layout/size search that derives "32 colours => 5 planes"
  discards the right answer — when a 5-plane fit fails, retry with 6.
  Embryo `.pic` (hunter): 64-B palette + 352x283x6 row-interleaved,
  previously rejected for exactly this reason.
- `BLTSIZE = (height << 6) | width_in_words`.
- Blitter modulos are per-row byte offsets, and can be negative.
- Rows are word-aligned.
- 12-bit colour scales as `nibble * 17`.
