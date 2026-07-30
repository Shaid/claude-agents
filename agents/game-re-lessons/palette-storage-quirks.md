# Palette storage quirks

**When it bites:** a palette decode looks incomplete, or you can't find a palette in the same file as the pixels.

- Palettes often store only the base half (32 stored + 32 computed
  half-bright).
- May live in a **different file** than the pixels — wyrm's donor-palette
  system: `dunes`→`intds`, `icone`→`onmap`.
- May start at an unexpected offset — Dune's palette starts at byte 2, since
  the "header" bytes are actually the first palette command.
- Sprites may carry a `pixelBase` offset into a shared palette region.
