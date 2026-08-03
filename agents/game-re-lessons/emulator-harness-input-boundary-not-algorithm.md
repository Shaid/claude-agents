# An emulator harness running far longer than a bigger confirmed job means the input boundary is wrong, not the algorithm

**When it bites:** a musashi-style (or similar) harness that runs a game's own
decompression/decode routine on a *new* buffer (not the one it was originally
verified against) either never reaches its completion signal or produces a
"structured but wrong" partial result — plausible-looking repeating records,
not pure noise — and the instinct is to keep patching the harness (bigger
cycle budget, a smarter stop condition, another register-reuse bug) rather
than question whether the buffer you handed it was ever a valid input at all.

Confirmed on Conan the Cimmerian (Amiga): a working harness decompresses
`Game`'s own DATA hunk (191,032+34,356+4 bytes across 3 passes) in ~30.6
million emulated cycles — verified independently via legible recovered game
text. A variant of the same harness, reused to decompress a `.L32`
loader-asset's much *smaller* pixel region (a ~27KB buffer, targeting a
~40KB output — roughly a fifth the real job's size), never reached its
completion signal even after 400 million cycles (13× the cost of the entire
larger, confirmed-correct job) — despite two real, distinct bugs already
found and fixed along the way (a baked-in "compressed length − 1" immediate
that needed re-patching per input buffer, and a false-positive stop
condition from a register being legitimately reused for unrelated
arithmetic mid-subroutine). The partial output was not noise: 61% nonzero,
with a clean repeating 12-byte record and a byte counting down by exactly
1 each record — exactly the kind of "looks like *something* real" result
that invites one more patch. Escalating instead of patching further found
the actual defect: the premise was wrong from the start. The `.L32` file's
"pixel-data region" was never a compressed stream fed to this engine at
all — it was a misread resource-fork header field (a `mapLength`/`mapOffset`
pair mistaken for a decompressed-size/pixel-offset pair), and the real
format is an ordinary resource fork the project's existing, unrelated
decoder already handled correctly. No amount of harness fixing was ever
going to produce a correct decode, because the bytes being fed to the
engine were never meant to go through it.

**The diagnostic, cheap and available before escalating:** compare the new
job's cycle cost against a similar-shaped job you've already verified,
scaled by relative output size. A decompression that costs 13× more cycles
than an entire confirmed multi-pass job, to produce a *smaller* target, is
evidence the algorithm is chewing on data it was never designed to consume
— not that it needs more budget. Pair this with the existing
`rle-decode-succeeds-on-garbage.md` family: a "structured but wrong" partial
decode (recognisable small-scale repetition, not pure noise) is exactly as
untrustworthy as a clean-looking wrong decompressed size — both are the
algorithm mechanically processing bytes it was never meant to see, just
with more visible intermediate structure. Before spending more engineering
effort on the harness itself, re-derive where the "compressed region"
boundary came from and whether it was ever independently confirmed (a
declared size field cross-checked against something else, not just assumed
from "this looks too small for raw pixels").
