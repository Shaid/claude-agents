# Plane-major bitplane data can pad each plane to a round buffer size, not pack tight

**When it bites:** a plane-major bitplane decode is already confirmed correct on layout/order (legible text, right composition, right silhouettes) but still shows speckle/noise that gets worse plane-by-plane, or the file has "extra" bytes beyond `rowBytes*height*planes` that get explained as one inert trailing block.

Don't assume `planeStride == rowBytes * height` (tightly packed, no gap
between planes) just because plane order and bit order are both already
confirmed correct — those two controls only test how already-fetched bits
are interpreted, not *where* each plane's data is read from in the file.
A separate, structurally plausible-looking bug — each plane individually
padded to a fixed, rounder buffer size (e.g. 8192 instead of a real 8000
bytes of content) — produces exactly this signature: plane 0 decodes
correctly (its slot starts at offset 0 either way), and each subsequent
plane reads progressively more of the *next* plane's padding-then-data as
its own tail, so image quality visibly degrades plane-by-plane while the
overall composition still reads as "roughly right, but speckled." The
file's leftover byte count (real size minus `rowBytes*height*planes`) is
consistent with *both* hypotheses (one trailing block, or N per-plane
padding gaps that sum to the same total) — the byte count alone can't
distinguish them structurally.

**Diagnostic:** if the file's leftover-byte count divides evenly by the
plane count, individually-padded planes at a round stride (often a
power-of-two like `0x2000`) is at least as likely as one trailing block —
test it. A per-bitplane brute-force offset search against a confirmed
ground truth (see `cross-platform-decode-oracles.md`) settles it cheaply
and precisely: search each plane's best-fit start offset independently
rather than only testing whole-image offsets, and check whether the
best-fit offsets form an arithmetic progression with a common difference
larger than the naive tight-packed plane size.

Confirmed on Wizardry 6 (Amiga/DOS `.EGA` full-screen images, 320x200x4bpp
plane-major): the real per-plane stride is `0x2000` (8192) bytes, not the
tightly-packed `8000` (`320/8*200`) that had been assumed for two prior
passes. The "768 extra bytes" earlier explained as one trailing padding
block are actually four 192-byte per-plane gaps (`4*192=768`,
`4*8192=32768`=the whole file, no separate trailer at all). Independently
corroborated by disassembly: the literal `0x2000` constant was hardcoded
in the game's own screen-blit code as the real display's per-plane
bitplane pitch, confirming it as a genuine engine buffer-sizing
convention rather than a coincidence. Fixing the stride resolved what a
previous pass had logged as "leading hypothesis: genuine period-accurate
dithering, not pursued further" — that conclusion was half right (some of
the residual speckle, after the real fix, remained and was then provably
genuine source dithering) but had been reached without ruling out the
stride bug, because the two controls actually run (reversed plane order,
reversed bit order) were structurally incapable of catching it.
