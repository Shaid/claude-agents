# Tooling — compression identification

`Read` this when a payload looks compressed and the magic is unfamiliar.

- **`ancient` CLI** (`ancient identify`/`ancient decompress <in> <out>`) —
  identifies/decompresses dozens of retro compressors (PowerPacker, RNC,
  XPK, ...) byte-exactly. Try it whenever an unfamiliar magic's payload
  still resembles a known compressor family — studios sometimes just rename
  the magic (`renamed-magic-container.md`) — before disassembling a depacker.
- **Window initial state is part of the codec.** Before assuming an LZSS/LZ77 window starts zero-filled (or space-filled, as Okumura does), look for the clear loop in the game's routine. If there isn't one, the window holds whatever the previous call left. Find streams whose back-references reach positions not yet written in that call. They decode differently offline, and their correct output depends on load order (emulate the preceding decode, or capture it). Also copy the game's offset masking (`andi.w #$7ff`) instead of throwing on out-of-range offsets, so the decoder behaves the same on every stream. Urban Strike (MD) Strike-LZSS: no clear, 3 streams read stale window bytes.
