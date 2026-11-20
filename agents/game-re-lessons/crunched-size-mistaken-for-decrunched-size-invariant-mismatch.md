# A size invariant that "doesn't add up" may be checked against the wrong one of a compressed resource's sizes

**When it bites:** a code-derived byte-count invariant (a loop's total consumption, a buffer bound) is compared against "the file's size" on a compressed-at-rest resource and comes out larger, prompting "this routine must be working on a different, larger buffer". Also: a wrapper's outer size field is documented as "the decompressed size" and you are about to size output from it.

A compressed-at-rest asset has several legitimate sizes, and docs and manifests often cite one without saying which:
1. the **on-disk (crunched) size**;
2. the **decompressed size** the game's code actually operates on;
3. an **in-place buffer size**: an outer wrapper may record how much to allocate so the game can decompress in place, which is max(decompressed size, compressed length + the decoder's write-ahead slack). It equals the decompressed size on most files and is larger on the rest, so calling it "the decompressed size" looks right on samples and is wrong on a minority.

A zero-slack match against the right size reads as "far exceeds the file's size" against the wrong one, and becomes a standing false negative.

**Check / fix:**
- When a size invariant fails, re-derive and label every candidate size (decompress and measure) before concluding a mismatch. Don't trust a size cited elsewhere without checking which one it is.
- For a wrapper with both an outer size and an inner stream header: per file, compare the outer size with the inner stream's own size, and with compressed length + header. If outer ≥ inner on every mismatch, it is a buffer size. Size output from the inner header.
- Before reporting "output padded/truncated by the wrong field", confirm the decoder actually reads that field. Often only the comments are wrong.

**Canonical example:** Jungle Strike (Amiga AGA, `strike`). `LAB_0365` consumes 9,100 bytes from the buffer loaded from `weapons`. A prior session wrote that this "far exceeds `weapons`' 2,836-byte file size" and theorised a separate scratch buffer. 2,836 was the **crunched** (LR88/PowerPacker) size; decrunching gave exactly 9,100 bytes. The wrong comparison had blocked the file's pixel decode across several sessions.

**Variants:**
- Fire Emblem Awakening/Fates (3DS, `lucina`): the "LZ13" wrapper (`0x13` + u24 + LZ11 stream) was documented as `0x13` + decompressed size. The outer u24 differs from the inner LZ11 size on 853/4,914 Awakening and 1,480/13,455 Fates files, and on every mismatch it is > inner and ≥ fileLength − 4: an in-place buffer size. The shared decoder already sized output from the inner header, so only the docs were wrong.

**History:** 2 recorded instances (`strike`, `lucina`).
