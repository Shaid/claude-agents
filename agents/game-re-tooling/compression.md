# Tooling — compression identification

`Read` this when a payload looks compressed and the magic is unfamiliar.

- **`ancient` CLI** (`ancient identify`/`ancient decompress <in> <out>`) —
  identifies/decompresses dozens of retro compressors (PowerPacker, RNC,
  XPK, ...) byte-exactly. Try it whenever an unfamiliar magic's payload
  still resembles a known compressor family — studios sometimes just rename
  the magic (`renamed-magic-container.md`) — before disassembling a depacker.
