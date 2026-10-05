# Binary-weighted resistor-ladder palette DACs are inherently near-linear (unlike R-2R)

**When it bites:** A palette/color DAC's RGB scale is documented (or about
to be documented) as "hypothesis: linear approximation, not the real
non-linear resistor-ladder curve" — and it's unclear whether porting the
emulator's real DAC formula is worth the effort, or whether a real capture
will look meaningfully different from a linear stand-in.

## The finding

Many arcade/console palette DACs (MAME calls the helper
`compute_resistor_weights()`/`combine_weights()`,
`src/emu/video/resnet.cpp`/`.h`) drive each color channel through a small
set of resistors, one per bit, each roughly half the previous one's
resistance — e.g. Sega System 16B's `{3900, 2000, 1000, 500, 250}` ohms for
a 5-bit channel (`src/mame/sega/segaic16.cpp`). This is a **binary-weighted**
resistor ladder: resistor `k`'s conductance contribution is proportional to
`2^k`, exactly mirroring bit `k`'s numeric weight — so the resulting DAC
curve is **inherently very close to linear**, not meaningfully non-linear.

Confirmed on Golden Axe (System 16B, `kolbold` project): porting
`compute_resistor_weights()`/`combine_weights()` verbatim and diffing the
resulting 32-entry (5-bit) LUT against the naive `round(v/31*255)` linear
approximation showed the two curves **agree at most of the 32 values** and
differ by exactly **1 LSB** at a handful of others (e.g. 5-bit index 11:
real DAC = 91, naive linear = 90). Not a dramatic re-color — a rounding
nuance.

**This is a property of binary-weighted ladders specifically.** An R-2R
ladder, or a resistor set that *isn't* a clean halving sequence, does not
get this same near-linear guarantee — don't assume it transfers without
checking the actual resistor values in the emulator source.

## The actionable upshot

Don't leave a linear approximation in place indefinitely just because "the
real curve is non-linear so an approximation is fine, or not worth
chasing." Porting `compute_resistor_weights()`/`combine_weights()` is cheap
and mechanical (a single-network, no-pulldown/no-pullup case is a ~20-line
function — see `computeResistorWeights()`/`combineWeights()` in
`src/assets/formats/segas16-gfx.ts`, kolbold project, for a worked example)
and turns a "hypothesis, approximately right" caveat into a byte-exact
"confirmed, matches MAME's own formula" one — worth doing whenever the
reference emulator's source is available, since the real cost is low and
the confidence upgrade is total.
