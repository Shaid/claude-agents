# A single extreme (but correctly-decoded) real value can defeat a bounding-box-based visual verification

**When it bites:** rendering/screenshotting many real, composed transforms
(scene assembly, batch mesh preview, any "fit the camera/viewport to the
extents of everything currently loaded" auto-framing) as the visual half of
a verification pass, especially right after wiring up a *new* per-instance
transform/scale field a prior pass never read.

A bounding-box-fit camera (or any "frame to extents" visualization) is not
robust to a single real, correctly-decoded outlier — one placement with a
genuinely huge scale/position swamps the box, so every other correctly-
positioned object collapses to an invisible speck near the frame center.
This looks exactly like a decode bug (everything stacked at one point) even
when the underlying transform math is byte-exact correct — confirmed on
Drakengard 3 (`flower` project): assembling a real Level's placed
`StaticMeshActor` instances into a three.js scene, the first screenshot
showed one giant flat plane dominating the frame with a tiny cluster of
real geometry barely visible at its center. The transform pipeline itself
was already independently numerically verified (cross-checked against an
external reimplementation); the actual cause was one real placement whose
`DrawScale3D` was `(26, 4293, 7702)` in the game's own raw Level data —
0.03% of a 3,143-placement sample, reproduced verbatim (not a decode
artifact) — almost certainly a disabled/debug placeholder actor. Don't
assume a "looks broken" bounding-box render means the decode is wrong
before checking whether one real value is an extreme statistical outlier.

**Fix**: before trusting (or debugging) a bounding-box-fit visual
verification of many composed real values, compute the percentile
distribution of the relevant derived numeric property (scale magnitude,
translation distance from centroid, bbox diagonal) across the whole
population. A real, load-bearing gap between a high percentile (p99, p99.9)
and the population max is decisive evidence of one-or-few genuine outliers,
not a widespread problem — exclude them via a threshold derived from that
real gap (comfortably above the highest *legitimate* value seen, comfortably
below the outlier), not a guessed magic number, and count the exclusion
explicitly (a real, quantified field) rather than silently dropping it.
Confirmed on the case above: p50=1.0, p90=2.7, p99=6.0, p99.9=18.3, then a
sheer jump straight to the single outlier's 7,701.9 — a threshold of 50 (2.8x
the real p99.9, 154x below the outlier) cleanly separated the one bad value
from every legitimate one, and re-rendering after excluding it produced an
immediately recognizable, physically coherent scene.
