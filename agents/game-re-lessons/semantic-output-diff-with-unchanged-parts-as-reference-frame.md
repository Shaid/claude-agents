# Regression-proving a shared decoder: diff the semantic output, and let the parts that didn't change be the reference frame for the parts that did

**When it bites:** changing a decode/export library that several games'
already-shipped asset corpora depend on, where the fix is expected to alter
*some* output and leave the rest alone. A byte-diff of the regenerated files
is useless (buffer offsets, accessor indices and node ordering all shift),
and "the validator still passes / it still renders" cannot tell a fixed
asset from a newly-broken one.

## The two-part technique

**1. Diff the semantic quantity, not the file.** Pick the value that actually
determines what the user sees, recompute it from the output file before and
after, and compare per element. For a skinned glTF corpus that is each
primitive's *effective* bind-pose world-space bounding box — `sum_k w_k *
(jointWorld_k x IBM_k) * v` over every vertex, i.e. reproducing the renderer's
own skinning math rather than reading `POSITION` raw. That collapses every
representational change (different skins, different joint numbering, extra
nodes) and exposes only real movement:

| Game | Primitives unchanged | Moved |
|---|---|---|
| Three Houses | 9,972 / 10,614 (93.95%) | 642 |
| FE Warriors | 11,648 / 11,984 (97.20%) | 336 |
| Three Hopes | 1,308 / 1,308 (100%) | 0 |

A third corpus coming back **100% unchanged** is worth as much as the other
two: it is a null control showing the change is inert where it should be
(that game happens to ship no cloth submeshes).

**2. Judge the movers against the non-movers of the same file.** The hard
part is proving the 642 that moved moved *correctly*, with no external
oracle. Use the unchanged primitives of the same file as the reference frame:
they are, by construction, the geometry that was already right — for a
character model, the body. Then ask whether each moved primitive's centroid
now lies inside their combined bounding box:

| Game | Moved | Centroid inside before | After | Mean normalized distance outside |
|---|---|---|---|---|
| Three Houses | 642 | 345 (53.7%) | **642 (100%)** | 0.369 -> **0.000** |
| FE Warriors | 336 | 171 (50.9%) | **336 (100%)** | 0.012 -> **0.000** |

Going from roughly a coin flip to a clean 100%, with the residual distance
falling to exactly zero, is a decisive result that needed no emulator, no
reference decoder and no screenshot. Normalize the distance by the reference
bbox diagonal so files of different scales are comparable, and require the
"before" number to be genuinely poor — if the before-state already scores
near 100%, this oracle is not discriminating and you need a different one.

## Practical notes

- Snapshot the before-metrics to a JSON file **before** rebuilding anything;
  the old outputs get overwritten and are not recoverable.
- Report `added` / `removed` element counts alongside `moved` / `unchanged`.
  A nonzero count there is the signal that something structural changed that
  your semantic diff cannot see — investigate it rather than eyeballing the
  percentage (see
  `shipped-output-may-predate-uncommitted-producer-changes.md` for the
  most common innocent explanation).
- Skip files where either side of the partition is empty; a file with no
  unchanged primitives has no reference frame and needs judging some other
  way.
