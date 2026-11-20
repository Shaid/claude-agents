# Archive: crunched-size-mistaken-for-decrunched-size-invariant-mismatch.md

Original strike text: see git history before 2026-11-20.

## 2026-11-20 — lucina (3DS): LZ13 outer size is an in-place buffer size

Add a paragraph:

**A third size: the in-place buffer.** An outer wrapper around a compressed stream may record the size of the buffer the game allocates so it can decompress in place. That is max(decompressed size, compressed length + the decoder's peak write-ahead slack), so it equals the decompressed size on most files and is larger on the rest. A doc that calls it "the decompressed size" looks right on samples and is wrong on a minority.
- Check: per file, compare the outer size with the inner stream's own size header, and with compressed length + 4.
- Size output from the inner header.
- Before reporting "output padded or truncated", confirm that the decoder actually uses the outer field. In lucina it never did: only the comments were wrong.

Example: FE Awakening/Fates "LZ13" (`0x13` + u24 + LZ11). Outer ≠ inner on 853/4,914 Awakening and 1,480/13,455 Fates files; outer > inner and outer ≥ fileLength-4 on every mismatch.
