# A synthetic incrementing/patterned fill can pass a naive entropy or byte-diversity scan as "real data"

**When it bites:** a whole-file entropy/byte-diversity sweep (nonzero-byte
percentage, unique-byte count, "looks like real varied data") is used to
decide how far real game content extends on a disk/archive, and a large
tail (or interior) region scores as "busy"/high-diversity under that sweep
even though nothing has actually identified its content yet.

Nonzero-byte-percentage and unique-byte-count are proxies for "this looks
like real data, not blank space" — but they cannot distinguish genuinely
varied game content from a **synthetic, mechanically-generated fill
pattern** (an incrementing counter, a repeating tag+counter stride, a
diagnostic test pattern) that a disk-imaging, duplication, or mastering
tool writes into unused/blank tracks. Such a pattern is by construction
"high diversity" — an 8-bit counter alone touches all 256 byte values over
its cycle — so it clears the same bar real data would, and gets silently
folded into "this is unexplored real content" instead of being recognized
as filler.

Confirmed on Zeewolf (Amiga, `hunter` project): the last 264 of 1760
logical blocks (132 KB, ~15% of the disk) scored 70-99% nonzero and up to
256 unique bytes per 4 KB window under a coarse entropy sweep — indistinguishable
from the disk's genuinely-real game-data regions by that metric alone. A
second, targeted pass — printable-ASCII-ratio computed **per 512-byte
block** rather than in coarse multi-KB windows — showed a suspiciously
*perfect, mechanically regular* alternation between "looks like text"
and "looks binary" every single block, hundreds of blocks in a row. That
regularity (not the ratio value itself) was the tell: real mixed content
doesn't flip category on a clean period for hundreds of consecutive
blocks. The actual bytes were a 4-byte-stride `'D' 'O' <byte> <counter>`
pattern with the counter cycling `0x00`-`0xff` — printable ASCII only
covers roughly the middle third of a byte's range, so a linearly-
incrementing counter mechanically alternates a fixed-size window between
"mostly printable" and "mostly not" every time the counter crosses that
band. A whole-disk scan for the exact 4-byte stride confirmed it: 33,790
hits, first appearance and last appearance both inside one single
unbroken run from that boundary straight to end-of-file.

**Takeaway:** a periodic, near-perfectly-regular flip in *any* per-chunk
classification (printable ratio, entropy, unique-byte count, even a
simple checksum) across many consecutive chunks is itself strong evidence
you're looking at a counter/pattern generator, not content — real game
data's statistics vary irregularly chunk-to-chunk. Before trusting an
entropy/diversity sweep's "real data continues here" verdict for an
unidentified tail or gap region, additionally: (a) look for exact-stride
byte-pattern repetition (a cheap sliding scan for `data[i] == data[i-N]`
for small `N`), and (b) check whether the region's start boundary is
suspiciously exact/round (a track or block-count boundary) — both point
at synthetic filler rather than truncated real content.
