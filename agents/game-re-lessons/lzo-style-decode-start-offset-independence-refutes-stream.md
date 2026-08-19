# A variable-length compressed-stream decode whose natural stop point is start-offset-independent is a random walk, not real decompression

**When it bites:** a magic tag or filename convention suggests a known
variable-length, self-terminating compressed codec (LZO1x, Huffman, other
LZ-family formats with an in-band EOF marker), you don't know the exact
header size before the compressed body starts, and every header-size guess
you try either throws a length-mismatch error or produces plausible-looking
partial output — before concluding "wrong header size, keep guessing,"
run the decisive control test below.

`rle-decode-succeeds-on-garbage.md` already establishes that "the decoder
didn't crash" is not verification for byte-oriented RLE. The same is true,
via a different mechanism, for LZ-family codecs with an in-band terminator:
random bytes fed to the decoder as if they were real tokens will
occasionally produce a "clean" stop (hitting the algorithm's own
rare multi-byte EOF sentinel purely by chance) after decoding a
statistically-average number of bytes, without ever throwing. A single
run "succeeding" at a plausible-looking length is exactly as weak a signal
here as it is for RLE.

**The decisive control, specific to this codec class**: build a decoder
variant that stops at the algorithm's own natural EOF marker instead of
requiring a target output length, then run it from several different
plausible start offsets within the same data (varying by tens of bytes is
enough). A genuinely real compressed stream's natural stop position
depends on where decoding started — different leading bytes produce a
different token sequence and a different eventual terminator position. If
the **stop position is instead byte-for-byte identical across every start
offset tried**, that is the fingerprint of a random walk through
non-compressed bytes converging on the same rare terminator pattern after
a roughly constant statistical distance — not real decoding, regardless of
how plausible the partial output looked.

Confirmed on NieR (2010, PS3, `flower` project): `.MDP` files carry an
`"lzo\0"`-tagged wrapper, and a prior pass's docs recorded "probably plain
LZO1x" as an untested hunch. A real LZO1x decoder (reused from a sibling
game's already-cracked codec) run from 7 different header-size guesses
(24-64 bytes) always threw a length mismatch, but only after producing a
suspiciously *consistent* ~196,608-byte output every time — already a weak
tell. The decisive test: a second decoder variant that stops at the
algorithm's own EOF marker instead of requiring a target length, run from
10 different start offsets 8-64 bytes apart within one physical page,
converged on the **identical** stop file-offset in all 10 cases. This
outright refuted the LZO1x hypothesis (a real stream's natural end can't be
start-position-invariant) rather than leaving it merely unconfirmed — the
real structure turned out to be fixed-size physical pages of mostly
uncompressed data with small per-page metadata records, not a compressed
block chain at all, confirmed byte-exact across 5 samples on 2 platforms.

**Fix:** before spending more effort hunting for "the right header size,"
run this offset-independence control once. A "yes, identical stop
position" result is fast, decisive, and — unlike a plausible-but-unverified
"successful" decode — actually falsifies the hypothesis rather than just
failing to confirm it, freeing you to look for the real structure instead
of continuing to vary header-size guesses against a codec that was never
there.
