# A short measured byte-repeat period is the row stride, not a clue to chase separately

**When it bites:** a numpy/statistical scan (shifted-byte-difference,
autocorrelation) finds a short, strong, unexplained repeat period in a
blob suspected to be planar/interleaved bitplane pixel data, and every
width tried so far has been *wide* (a large divisor of the file size, or
a "reasonable" screen/sprite width like 96-384px) with only comb/striping
renders to show for it.

The period **is** the answer, directly: for row-interleaved planar data,
one scanline is `bytesPerRow * planeCount` bytes, and that is exactly what
a byte-repeat-period scan measures when it locks onto the row boundary.
`width = (period / planeCount) * 8` falls straight out — no further
searching needed. The trap is treating the period as one more clue to
explain *after* finding the width some other way, rather than as the
width measurement itself.

Confirmed on Desert Strike (Amiga)'s terrain tileset (`disk3-01/08/12`,
41,600 bytes each): two independent passes measured a strong 10-byte
period via a shifted-difference scan and could not explain it, then swept
chunky-8bpp and row-interleaved-planar renders at every *wide* width that
divides 41,600 evenly (320px and others) — every attempt showed only
"vertical comb/striping", because a wide-width guess reads the planar
interleave completely out of phase. The 10-byte period was staring at the
answer the whole time: `10 = 2 bytes/row * 5 planes`, i.e. width = 16px —
a width nobody tried, because every sweep implicitly assumed "the real
image must be wide" and walked divisors from large to small (or just
never went below ~64-96px). At width 16 the file decodes cleanly as a
260-tile, 16x16px sprite sheet.

**The fix:** the moment a short (single- or low-double-digit-byte) period
is measured on suspected bitplane data, compute `candidateWidth =
(period / planeCount) * 8` for every plane count you're already
considering (not just the one you assumed) and render that width
*first*, before continuing a wide-width sweep. A "vertical comb" failure
pattern at every wide width tried is itself evidence the real width is
*narrower* than anything tried, not a reason to try even wider divisors —
narrow tile-sheet widths (16px, 32px) are an easy blind spot precisely
because "an 8-16px-wide image" doesn't intuitively read as a plausible
sprite/screen width the way 96-384px does.

**Addendum — the same measurement, run on a real screenshot instead of
the extracted asset, is a strong independent oracle for a decode you
already believe you've solved.** Once a tile/icon's pixel dimensions are
already derived from disassembly or structural evidence, autocorrelating
a clean patch of an *actual game screenshot's* rendered output (not the
extracted file) at the location where that tile should repeat is a cheap
confirming — or falsifying — cross-check, and can also discriminate
between two competing draw-mechanism hypotheses when more than one is
consistent with the disassembly. Confirmed on Phantasie III (Amiga,
`nicodemus` project): disassembly had found two plausible per-cell draw
loops writing to overlapping screen regions for the dungeon view — one
stepping 5px per column against an 8px-wide icon (genuine overlap), one
stepping a clean 8px/5px per cell (no overlap) — and it wasn't obvious
from the code alone which one dominates the visible frame. Autocorrelating
a real emulator screenshot's background-texture patch found a sharp peak
at exactly 8px horizontally and 5px vertically, both with no evidence of
the other loop's fractional 5px-into-8px overlap — confirming the
non-overlapping loop is what's actually on screen (the overlapping loop
only paints a thin strip the other loop fully repaints over), while also
independently reproducing the icon's already-known 8×5 dimensions to the
pixel. Same technique as the base lesson, different purpose: there, the
period *finds* an unknown width; here, it *arbitrates* between finished
hypotheses using ground truth neither hypothesis was built from.

**Addendum — comb-striping that persists across every width tried,
including the period-derived one, can mean the data isn't pixel data at
all.** Confirmed on Wizardry 6 (SNES): a region flagged by a byte-density
census as graphics-shaped (right byte count, adjacent to other tile data)
produced strong, regular vertical white streaks under *every* tile width
tried, with no width making the streaks go away. Rather than one more
width to find, this turned out to be the tell that the underlying data was
never pixel data in the first place — it was a periodic **2-byte `[tag]
[id]` record table** (a maze/dungeon compose-list-shaped structure), whose
fixed 2-byte period happened to interact with the 4bpp tile decoder's
per-row bitplane-pair layout to produce a stripe every output column,
regardless of declared tile width. The tag byte's high bit pattern
recurring every other byte is what a bitplane decoder reads as "column N
is always lit", at any width. If a measured short period (per the base
lesson above) produces persistent striping at its own derived width too —
not just at wide guesses — stop trying pixel widths and check whether the
period itself is a **non-pixel record stride** (hex-dump a raw window and
look for a structured tag/value pattern) before spending more render
attempts.
