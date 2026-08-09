# A per-group spread-from-its-own-centroid metric can't distinguish rigid-transform candidates

**When it bites:** testing several candidate matrix/direction readings
(row-major vs. column-major rotation, forward vs. inverse) against grouped
points to find which one correctly maps a point set into some object's own
local/canonical space, and every candidate — including "do nothing" —
scores identically on a clustering-tightness check.

Valkyrie Profile 2 (PS2)'s per-bone skinning matrix looked like an
inverse-bind transform (a prior pass had ruled out treating its raw
translation column as a comparable world position, correctly diagnosing
"probably an inverse-bind matrix" but not proving which reading of the
matrix was right). The natural first test: group mesh vertices by which
bone they're rigidly bound to, apply each of 4 candidate transforms (2
rotation-reading conventions x 2 directions) plus the untransformed
baseline, and measure each group's RMS distance from **its own recomputed
mean** after the transform — expecting the *correct* transform to cluster
each bone's vertices tightest. All 5 candidates, including the raw
baseline with no transform applied at all, produced the exact same
number. This isn't a coincidence or a bug: RMS distance from a group's own
centroid is mathematically invariant under any rigid transform (rotation +
translation) applied to that group — a rotation can't change pairwise or
centroid-relative distances between points, and translation doesn't either
(it's a pure shift, and the whole point of measuring from the group's
*own, recomputed* mean is that the shift cancels out of the metric by
construction). The check can only reveal "yes, these points still form a
rigid group" — true for every candidate, including doing nothing — never
"and this specific candidate placed them where they should be."

The fix: measure distance from a fixed **external reference point** implied
by the hypothesis, not from the data's own centroid. Here, the hypothesis
was "this matrix maps world/mesh space into *this bone's own local
coordinate frame*" — so the correct transform should collapse each bone's
bound vertices to a *small magnitude near that frame's own origin*
`(0,0,0)`, while wrong candidates (and the untransformed raw baseline)
stay scattered at whatever distance that bone happens to sit from
world-space origin. Recomputing the same 5 candidates against distance-
from-origin instead of distance-from-group-mean separated them
immediately and decisively (correct candidate: mean RMS ~7.4; every wrong
candidate and the raw baseline: 47-61), and the result generalized cleanly
across 6 more real records.

General rule: before trusting a "which candidate transform clusters
tightest" test, ask what the *reference point* of the tightness metric
is. If it's the transformed group's own recomputed centroid/mean, the
metric is blind to any transform class closed under that reference choice
(any rigid rotation+translation, at minimum) — it can only test "does
this still look like a rigid group," not "is this the *right* rigid
transform." Anchor the metric to a point the hypothesis itself predicts
(a frame's own origin, a known landmark, an external oracle value) instead
of a quantity recomputed from the very data being transformed.
