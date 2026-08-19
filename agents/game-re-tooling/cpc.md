# Amstrad CPC targets

Worked example for everything here: WIME CPC (`middilgard`,
`docs/wime/cpc/engine.md`, `tools/wime/cpc/extract-dsk.py`).

- **Extended DSK container**: per-track 256-byte `Track-Info` header, then
  packed sector data. Each 8-byte sector descriptor stores the **actual
  data length in bytes 6–7** — on protection-preserving dumps it can exceed
  `128 << size_code`, and the packed data uses the stored length; read it,
  falling back to the size code only when it's zero. The disk-header byte
  table at `0x34` is a per-track *size* table in 256-byte units (track
  header + sector data), not a sectors-per-track count.
- **No AMSDOS directory ⇒ fastloader.** Don't hunt for a file table: the
  boot code's load-call argument sets `(dest, first track, last track)` ARE
  the disk map (WIME: five `CALL $BEBE` sites gave the complete track →
  memory map; the suspected "file table" data block was FDC command
  buffers). Verify a derived load base for free by rendering a full-screen
  region at a predicted `&C000` screen address — a legible title/victory
  screen confirms the whole map in one shot. Big art is often stored as raw
  uncompressed screen dumps this way.
- **Screen-byte pixel layouts are bit-interleaved per pixel, never packed
  bit-pairs.** Mode 0 (2 px/byte, 16 pens): pixel 0's pen bits are
  `b7,b5,b3,b1` (LSB→MSB order `b7=bit0, b3=bit1, b5=bit2, b1=bit3`),
  pixel 1's are the same pattern one bit right. Mode 1 (4 px/byte, 4 pens):
  pixel *i* takes bit `7−i` as its high bit and bit `3−i` as its low bit.
  A "packed 2bpp MSB-first" reading is not a CPC screen format and cost a
  full WIME session a wrong "confirmed" decode.
- **Palettes are Gate Array hardware colour values in code/data** (WIME:
  stored pen-15-first, installed by a loop counting the pen index down),
  not a file-level structure. Map HW value (`& 0x1F`) → firmware ink
  number → RGB with 3-level (0/128/255) components. Mode-0 pixels are 2:1
  wide — render at 2× horizontal or the aspect looks wrong.
- **Serpentine software blitters are common** (sequential source reads,
  alternating column direction per scanline) — see lesson
  `serpentine-row-order-mimics-mirrored-rows.md`. The CPC has **no hardware
  sprites**, so any "hardware sprite plane" interpretation is wrong by
  construction.
