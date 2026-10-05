# A bit-classifier's case-index direction needs re-simulation + handler-semantics cross-check, not just "monotonic and unambiguous"

**When it bites:** A prior pass documented a multi-bit classifier (marching
squares, a flags-to-case dispatch, any "N input bits -> case index" jump
table) as confirmed with a stated direction ("index 0 = all X, index N =
all Y"), on the strength of "the bit-shuffle produces a clean, unambiguous
index" — and you're about to reuse that direction claim, port it, or build
on top of it, without independently re-deriving which end of the index
range actually corresponds to which input combination.

## What went wrong

Powermonger's `$F912` terrain-type classifier reads 4 corner heights,
tests each for `==0` ("water"), and via a `seq.b`/`add.w` (doubling)
/`lsr.w`/`andi.w` bit-shuffle produces a 0-15 case index used to jump into
one of 16 case handlers. A prior session's doc confirmed the *mechanism*
("marching squares... produces a clean, monotonic 4-bit index with zero
ambiguity") and then asserted a *direction* ("index 0 = all water, index
15 = all land") — but never actually checked that claim against anything;
it was an assumption stated alongside a genuinely-verified mechanism, and
the two got conflated as equally confirmed.

Directly re-simulating the exact opcode sequence in Python for all 16
input combinations showed the claim was backwards: the case index is
literally the water bitmask, MSB-first — **case 15 is all-water, case 0 is
all-land**, the reverse of the prior doc. Confirmation came two ways, not
one: (1) re-simulating the raw bit-shuffle bit-for-bit (not eyeballing the
instruction sequence and reasoning about it informally), and (2) checking
what the two *extreme* cases' actual handler code does — case 15's handler
is a trivial `clr.b` constant (consistent with uniform open water needing
no shading) while case 0's handler computes a real corner-height gradient
(only meaningful where slope varies, i.e. land) — the reverse of what the
prior direction claim would predict. Cross-checking the *semantic
plausibility of the handler bodies* against the numeric direction is a
second, independent signal beyond the bit simulation alone, and both
agreeing is what makes this a real correction rather than a coin flip.

A secondary risk was also checked and ruled out: the classifier's scratch
register is never explicitly cleared between per-cell loop iterations, so
a naive worry is "does leftover garbage from the previous cell's
classification leak into this cell's case index?" A Monte-Carlo sweep
(random garbage values x all 16 real corner combinations) confirmed the
final case index is invariant to that garbage in every case — the
multiple rounds of doubling shift prior garbage out of the bits the final
mask keeps. Verifying this took the same amount of effort as the direction
check itself and was necessary before trusting the classifier as a pure
function of its real inputs.

## The general technique

When a doc states both "the mechanism is confirmed" and "here's which end
means what" in the same breath, treat those as two separate claims with
two separate bars: mechanism confirmation (structural: it *is* a
classifier, dispatch table, etc.) does not imply direction confirmation
(semantic: which numeric value means which real-world state). Re-derive
direction from either (a) a from-scratch bit-for-bit re-simulation of the
actual opcodes for every input combination, or (b) independently checking
what the code at each extreme case *does* and asking which semantic
interpretation makes that code make sense — ideally both, since they're
cheap and mutually reinforcing.
