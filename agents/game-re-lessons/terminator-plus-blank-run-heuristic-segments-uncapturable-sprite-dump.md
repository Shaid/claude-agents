# A confirmed line-terminator sentinel + a tuned blank-run heuristic gets a raw, uncapturable variable-width sprite dump much further than a fixed-width filmstrip — and any real color (even wrong-bank) helps inspect the result

**When it bites:** a variable-width/height sprite or tile format's pixel
*encoding* is fully confirmed (byte/bit layout, transparency value, any
in-band line/row terminator), but the real per-instance frame *boundaries*
live only in runtime state (sprite RAM, a display list) that no live
capture or emulator can reach on the current machine — and the shipped
asset is currently just the raw byte stream reshaped into one arbitrary
fixed-width strip "for visual inspection," which a human reviewer correctly
flags as unusable. Also fires when a still-payload-only greyscale index
dump (any format) needs a quick, honest inspectability boost with no new
ground truth available.

## The segmentation technique

If the confirmed pixel format has an in-band sentinel value that terminates
a row/line on real hardware (e.g. Sega System 16's sprite format: pixel
value 15 both means transparent AND ends the current variable-width line),
that sentinel is free, exact ground truth for each row's REAL width —
scanning the raw decoded stream for it needs no live capture at all. This
alone is a real improvement over a fixed-width reshape: row boundaries stop
being an arbitrary guess.

Row width alone doesn't find sprite-to-sprite boundaries, but a second
signal often approximates it well enough to be useful: sprite art is
unlikely to be blank (every pixel value 0/background) for many consecutive
rows in the middle of real content, so a sufficiently long run of
consecutive all-blank rows is a plausible (not certain) inter-sprite gap.
Combine both: reconstruct rows at real width, then break the row sequence
into candidate chunks at long blank-run boundaries, filter out
near-empty/trivial chunks by a minimum content-row and minimum
non-transparent-pixel-count bar, and pack survivors into an atlas.

**Tune the blank-run threshold against the corpus's own histograms, don't
guess it.** Compute the real distribution of consecutive-blank-row run
lengths (percentiles, not just mean) and sweep candidate thresholds,
watching for two failure directions: too low over-splits into tens of
thousands of one-or-two-row fragments (mostly ordinary internal padding,
not real gaps); too high starts visibly merging clearly-distinct shapes
into multi-thousand-row mega-chunks. The right threshold usually sits just
past the "ordinary internal padding" bulk of the percentile curve (e.g.
p75-p90) — confirmed on Golden Axe (System 16): a threshold of 8 blank
rows, against a real distribution of p50=5/p75=8/p90=12/p95=15, took an
18,709-raw-chunk population down to 1,305 plausible candidates, while
thresholds of 16+ started merging obviously-separate art into single
multi-thousand-row blobs.

**Expect and measure a real "junk floor," and don't mistake it for a bug.**
A format like this is often dominated by short, repeating blank-padding
records — on Golden Axe, 68.9% of all 463,140 reconstructed rows were
exactly one word's worth of blank padding (`0x000F` repeated), and 87.25%
of all rows were blank by any definition. This is real ROM content, not a
decode error — the minimum-content filter exists specifically to discard
this floor before it drowns out genuine candidates, and a sanity check
during tuning should confirm the "candidate" bucket's own row-width/pixel-
count stats look qualitatively different from the excluded "padding"
bucket's, not just smaller in count.

**A single anomalously-long unterminated run is very likely a known dead
zone, not real content — cap it out before it poisons a chunk's bounding
box.** Any format with an in-band terminator can also contain a large
region with NO terminator at all (an unpopulated ROM gap, alignment
padding, a reserved-but-unused bank) — this decodes as one absurdly wide
"row." If such a row isn't isolated by a sanity width cap (something well
beyond any plausible real hardware line width) and force-boundaried on its
own, it silently becomes part of a real chunk's bounding rectangle,
blowing up the packer's output. Confirmed on Golden Axe: a single
~524,288-nibble "row" starting at exactly the sprite ROM's own already-
documented unpopulated `0x0C0000-0x0FFFFF` gap decoded with no interior
terminator, and needed a `ROW_WIDTH_SANITY_CAP` (set from the format's own
documented real-hardware max line width) that excludes any row past it from
grouping entirely and forces a hard boundary there.

**Report the result honestly as heuristic, not as a decode.** This
approach does not know where a real sprite starts or ends any more
precisely than "a long-enough blank run happened here" — it can both
over-split a real sparse sprite and under-split two real sprites separated
by a short gap. Label every output chunk a *candidate*, and spot-check a
handful of the largest/densest candidates by rendering them (not just
trusting the aggregate chunk count) before claiming the segmentation
"looks like real sprites" — on Golden Axe, the largest candidates rendered
as coherent, non-random, symmetric shapes (a light central band flanked by
two darker striped columns) very unlike either noise or the smeared
content of the old fixed-width filmstrip, which is real (if informal)
evidence the heuristic is finding genuine structure, not just splitting
noise consistently.

## The colorization side-finding: any real color helps inspection, independent of correctness

When no confirmed palette exists for the exact asset being rendered (here:
the confirmed boot-palette upload never reaches the sprite-palette region
at all), applying ANY other already-confirmed real ROM palette bank — even
one from a structurally unrelated asset (tiles, not sprites) and therefore
provably the WRONG colors — to the same greyscale index data measurably
improves a human's ability to visually separate structurally-distinct
regions, compared to a flat greyscale ramp. This was not subtle: a region
that read as flat grey horizontal bands in greyscale resolved into a
bright, clearly-bounded central shape flanked by two differently-colored
side regions once (wrong-bank) hue/luminance separation was applied. The
generalizable point: color separation aids inspection *by making adjacent
index values visually distinguishable*, a benefit that is completely
independent of whether the specific colors are correct — this is a cheap,
honest "quick win" for any other still-greyscale-placeholder index dump in
this account's projects, provided it's shipped clearly labeled as an
experiment/placeholder (never as a confirmed palette) so nobody mistakes
the resulting hues for real game colors.
