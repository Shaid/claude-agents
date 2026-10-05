# Palette storage quirks

**When it bites:** a palette decode looks incomplete, you can't find a palette in the same file as the pixels, you're about to blind-search a large binary for one, a confirmed palette resource has trailing bytes past the RGB array you've been calling "unexplained"/"padding"/"truncated," or only ONE same-corpus candidate file exists for a "byte-identical across siblings" cross-check (so that technique alone can't discriminate it).

- Palettes often store only the base half (32 stored + 32 computed
  half-bright).
- May live in a **different file** than the pixels — wyrm's donor-palette
  system: `dunes`→`intds`, `icone`→`onmap`.
- **When the loader/renderer code has no CPU-driven full-palette upload
  loop at all (checked and ruled out), check a sibling/auxiliary file
  family for a byte-identical shared table instead of continuing to trace
  the executable.** Confirmed on Epic (Amiga): the main executable writes
  exactly one hardware colour register (`COLOR00`) via 16 instructions,
  all flash/flicker effects reading a runtime variable — no loop writing a
  full 16- or 32-entry palette to `COLOR00`-`COLOR1F` exists anywhere in
  194KB of code (absolute-addressing writes, `LEA`-then-loop patterns, and
  an embedded copper-list palette were all checked and ruled out). The
  real palette turned up instead in a completely different file family
  (`.IGD`, not the `.3D` model files or the executable): decompressing all
  25 files in that family and comparing their first ~18 words byte-for-byte
  showed **zero mismatches** — a 16-colour RGB4 table baked identically
  into every one. Byte-for-byte identity across many independently-loaded
  sibling files is itself strong positive evidence of "this is the global/
  shared resource", found without any code tracing at all — cheaper than
  continuing to search the executable once a direct hardware-write search
  has already come up empty. Cross-check candidates: other files sharing
  the same container/header shape as the asset you're decoding, not just
  files that "look graphical."
- **On attribute-RAM hardware (C64 multicolor/hires bitmaps, ZX Spectrum,
  MSX2) the "palette" may be per-cell attribute blocks inside the same
  payload — not a register set, and not a separate file.** Two WIME C64
  sessions (`middilgard`) hunted a portrait palette as unknown
  `$D021`/`$D022`/`$D023` register values; the colours were in the file the
  whole time — the 5,000-byte payload was 4,000 bitmap + 500 screen-RAM +
  500 colour-RAM, each picture carrying its own colours. The byte ratio is
  the tell (8:1:1 = 8 bitmap bytes vs 1+1 attribute bytes per cell):
  `payload_size − bitmap_size` dividing cleanly by the cell count is the
  same invariant trick as the PAL_HDR case below. On such hardware only
  `$D02x`-class registers (background/border) are set by code; everything
  else is data.
- **When a tile/sprite format has NO embedded palette at all (confirmed by
  its own header shape — no reserved region for one), search the same
  corpus for a DIFFERENT file that shares the tile's likely on-screen
  neighborhood (border/frame chrome around the same viewport, UI overlay
  drawn alongside it) and DOES carry an embedded palette in the family's
  standard header shape — then corroborate the candidate via a sibling
  title in the same engine family that already has this exact resource
  CONFIRMED by an independent mechanism.** This is the single-candidate
  cousin of the "byte-identical across many siblings" technique above: it
  applies when only one plausible same-corpus donor file exists, so
  cross-title agreement substitutes for cross-file agreement. Confirmed on
  Champions of Krynn (Amiga, `crawl`): the `8X8D0/1/2.DAA` wall-tile bank
  format's own 9-byte header has no room for an embedded palette (plane
  data starts immediately after it — unlike Death Knights of Krynn's
  sibling tile format, which reserves a 64-byte palette per entry).
  `DUNGCOM.DAA` (byte-identical to `BORDER.DAA`, the on-screen border
  chrome drawn around the same first-person wall-art viewport) DOES carry
  an embedded 32-entry palette in the standard format — and Death Knights
  of Krynn's OWN `DUNGCOM.daa` file (same filename, sibling title, same
  engine family) embeds a near-identical palette whose entries 16-31 match
  DKK's independently-confirmed real wall palette exactly. That agreement,
  even with no code-level trace confirming the mechanism (an exhaustive
  disassembly found no `LoadRGB4`/hardware-register-write/Copper-list
  anywhere in Champions' executable — a genuine, LVO-provenance-checked
  negative, not a missed search), was strong enough to ship as a RENDERED
  (not CONFIRMED) default palette, replacing a synthetic grey ramp.
- May start at an unexpected offset — Dune's palette starts at byte 2, since
  the "header" bytes are actually the first palette command.
- Sprites may carry a `pixelBase` offset into a shared palette region.
- **A blind byte-pattern search for a palette is nearly useless against
  sparse bitplane/sprite corpora.** Searching for an AGA `LoadRGB32` header
  longword, or "N consecutive words all `<= 0x0FFF`", against real image
  data returns thousands of hits — long runs of zero bytes in sparse
  graphics satisfy loose numeric constraints constantly, so the search
  isn't selective enough to find anything (Jungle Strike AGA: both
  searches were run corpus-wide and produced noise, not a candidate).
  Prefer tracing the loader/renderer code, or checking whether a small
  self-contained loader executable embeds its own sample instance of the
  format (cheaper to statically analyze than a large raw code overlay with
  no known load address) before resorting to a blind scan.
- **If a compressed/data stream consumes a file to its exact last byte
  with zero leftover**, that's a positive structural proof there's no room
  left in that file for a separate header/palette/table — worth stating as
  evidence ("stream runs offset 4 to EOF with 0 bytes remaining") rather
  than just reporting "palette not found there."
- **Trailing bytes past a palette resource's RGB array are not automatically
  padding — check for a clean arithmetic invariant before writing them off.**
  A palette header with pointer/offset-looking fields beyond the basic
  `numColours`/`RGB-array-offset` pair is a strong hint those fields are
  real sub-table locations, not reserved space. Confirmed on EOB3/Dungeon
  Hack (AESOP/16): a 26-byte palette header's 11 trailing `u16` fields had
  been read only as "further fade-index-array offsets, not decoded" for an
  entire prior RE pass, with the RGB array's own size (`numColours*3`)
  clearly smaller than the resource's total size and the gap left
  unexplained. The actual structure (confirmed against real interpreter
  source, `DEFS.H`'s `PAL_HDR` struct) is 11 real per-colour brightness/
  light-falloff lookup tables, each exactly `numColours` bytes, placed
  contiguously right after the RGB array — `total size == header +
  numColours*3 + 11*numColours` holds with **zero deviation** across every
  palette resource in two different games' containers, a clean-enough
  invariant that should have prompted checking well before source access
  confirmed it. Whenever a struct's own header has multiple offset/pointer-
  shaped fields pointing past a variable-length array, try `total_size -
  (header + primary_array_size)` divided by the field count and by the
  primary array's own element count — a whole-number match either way is
  strong evidence of a real per-element sub-table, not filler.
