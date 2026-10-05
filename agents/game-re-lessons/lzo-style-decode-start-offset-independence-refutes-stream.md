# A variable-length compressed-stream decode whose natural stop point is start-offset-independent may just share one wrong framing assumption across every offset tried — not proof the codec is absent

**When it bites:** a magic tag or filename convention suggests a known
variable-length, self-terminating compressed codec (LZO1x, Huffman, other
LZ-family formats with an in-band EOF marker), you don't know the exact
header size before the compressed body starts, and every header-size guess
you try either throws a length-mismatch error or produces plausible-looking
partial output — before concluding "wrong header size, keep guessing," run
the offset-independence control below, and **before trusting a "converged"
result as refuting the codec entirely**, read the correction block below —
a real, confirmed case where this exact control gave a false "not this
codec" verdict because every tested offset inherited the same underlying
framing bug.

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

Tried on NieR (2010, PS3, `flower` project): `.MDP` files carry an
`"lzo\0"`-tagged wrapper, and a prior pass's docs recorded "probably plain
LZO1x" as an untested hunch. A real LZO1x decoder (reused from a sibling
game's already-cracked codec) run from 7 different header-size guesses
(24-64 bytes) always threw a length mismatch, but only after producing a
suspiciously *consistent* ~196,608-byte output every time — already a weak
tell. The decisive-looking test: a second decoder variant that stops at the
algorithm's own EOF marker instead of requiring a target length, run from
10 different start offsets 8-64 bytes apart within one physical page,
converged on the **identical** stop file-offset in all 10 cases — read at
the time as outright refuting LZO1x (fixed-size physical pages of mostly
uncompressed data with small per-page metadata records, not a compressed
block chain at all).

> **Correction (2026-09-09, `re-codebreaker`):** `.MDP` **is** plain LZO1X
> after all — the refutation above was wrong, not the LZO1x hypothesis. All
> 10 "different" start offsets shared the *same* systematically-wrong
> framing (a 16-byte page record where the real one is 12 bytes of three
> big-endian `u32`s, and a fresh per-page output buffer where pages really
> share one 64 KB match window file-wide). Varying the start offset by
> 8-64 bytes inside a single wrong framing convention doesn't test
> LZO1x-vs-not; it tests whether *that one wrong convention* is
> offset-sensitive, and a systematically wrong record size can desync the
> token stream identically regardless of which nearby byte you start
> reading from — producing the same false "converged, therefore not
> LZO1x" verdict every time. See `individually-failed-fixes-may-combine-
> cleanly.md`: three separately-plausible framing errors (record size,
> match-window scope, mandatory-vs-optional compression) were each
> independently sufficient to break every attempt, and the offset-
> independence control never distinguished "genuinely not LZO1x" from
> "LZO1x, but every offset tried inherits the same structural bug."
> Full corrected spec: `docs/nier/ps3/data-structure.md` §4.4.5 (`flower`
> project).

**Revised guidance:** the offset-independence control (below) is still a
fast, useful test for "is this a random walk hitting a rare terminator vs.
a real compressed stream," and it correctly rules out the specific,
narrow claim "decoding from these offsets under this exact framing is a
random walk." It does **not** rule out the codec family itself. Before
trusting a "converged, so it's not codec X" verdict, ask whether every
offset tested shares one un-varied assumption (record/header size, window
scope, whether compression is even applied to this file) — if so, vary
*that* axis too (see the escalation-ladder note on sweeping the full
cross-product of independently-varying axes) before writing off the codec
family entirely.

**Fix:** before spending more effort hunting for "the right header size,"
run this offset-independence control once. A "yes, identical stop
position" result is fast and worth having — but it falsifies only the
specific framing tested, not the codec family. Don't stop varying framing
assumptions (record size, window scope, optional-per-file compression)
just because one offset-independence run came back "converged."
