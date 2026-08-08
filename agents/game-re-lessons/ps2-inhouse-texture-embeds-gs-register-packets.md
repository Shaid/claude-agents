# An in-house PS2 texture format can store literal GS register-write packets instead of a pixel-format struct

**When it bites:** an unfamiliar proprietary PS2 texture container resists
struct-offset field guessing — no combination of candidate offsets for
width/height/PSM/palette-size produces consistent values across samples,
even though the file clearly has *some* fixed-shape header region.

Some in-house PS2 engines don't serialize a clean "here's the width, here's
the pixel format" struct for textures at all. Instead they embed a literal,
byte-exact sequence of the real **GS (Graphics Synthesizer) privileged
register write packets** the game issues at runtime to DMA the texture into
GS local memory — `BITBLTBUF`/`TRXPOS`/`TRXREG`/`TRXDIR` (register
addresses `0x50`-`0x53`), each wrapped in a small GIFtag + custom framing
qword. Confirmed on Cavia Inc.'s `wZIM` format (Drakengard/Drakengard 2):
what looked like unstructured binary noise after the magic was actually two
full register-group sequences (one for the indexed pixel data, one for the
palette/CLUT), each a real, decodable hardware packet.

**Diagnostic, not a guess:** scan the payload for the literal 8-byte
little-endian value equal to a known GS register address (`0x50` =
`BITBLTBUF`, `0x51` = `TRXPOS`, `0x52` = `TRXREG`, `0x53` = `TRXDIR`) sitting
in the "address" half of a 16-byte A+D (address+data) GIF packet entry — i.e.
search for `50 00 00 00 00 00 00 00` etc. as raw bytes, not via a struct
offset. A hit confirms the packet-embedding hypothesis immediately; decoding
the surrounding `BITBLTBUF.DPSM` field (bits 56-61 of the paired 8-byte data
half) then gives the real GS pixel-storage-mode enum value directly (`0x13`
= `PSMT8`, `0x14` = `PSMT4`, `0x00` = `PSMCT32`) — a value you can cross-
check against the real, publicly documented PS2 GS enum, not an arbitrary
guess.

**Two counterintuitive findings once the packets are found, both worth
checking independently rather than assuming either:**
- The **pixel payload** following the packet setup is not guaranteed to be
  GS-block-swizzled just because it's PS2 — `wZIM`'s indexed pixel data
  turned out to be plain row-major/linear (applying a block-unswizzle
  algorithm from a *different* PS2 title's texture format, tried first,
  produced a visible 2×2-tiled corruption artifact; reading it straight was
  correct).
- The **CLUT/palette**, separately, still needed the standard PS2 "CSM1"
  256-entry index unswizzle (palette-index bits 3/4 swap) — the same
  algorithm used by an unrelated PS2 title's own texture format
  (`~/Development/valkyrie/tools/shared/ps2-fis-image.ts`'s
  `csm1UnswizzleIndex`), reusable verbatim. Pixel-data swizzle and
  palette-data swizzle are independent facts about the same file; don't
  assume they travel together in either direction.

**A related scanning-robustness bug worth guarding against directly:** once
you're locating register groups by scanning for their address bytes, a
second/third group's scan must be able to **skip past** a coincidental false
match found inside the *previous* group's own raw pixel/palette payload
bytes, not abort the whole scan on the first non-register-shaped hit. The
first implementation aborted on any such collision, silently truncating
discovery to only the first (pixel) group whenever raw pixel data happened
to contain the scanned byte pattern — invisible until run at corpus scale,
where a nontrivial fraction of real files hit it.
