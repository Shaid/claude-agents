# A left-handed-to-right-handed coordinate conversion formula must be numerically derived and verified, not recalled from memory or copied unchecked

**When it bites:** exporting geometry/skeleton/animation data from an
engine with a different coordinate handedness than the target format (most
commonly: any left-handed source — Unity, DirectX-family engines — into
glTF, which is right-handed), and about to apply a remembered "mirror X,
negate y/z of the quaternion" -style formula from memory, prior code, or a
tutorial, without deriving or checking it against the specific source
engine's actual conventions.

## What went wrong (the confirmed-good version of this technique)

Fire Emblem: Engage (Unity, `chimera` project) needed its first-ever
Unity-to-glTF coordinate conversion in this project family (every other
game's source engine was already right-handed, so this class of bug had
never been hit before). Rather than trust a remembered "Unity->glTF is
mirror-X plus negate q.y/q.z" rule, the conversion was **derived
numerically**: build a rotation matrix from a quaternion using the
standard formula, conjugate it by the reflection matrix `diag(-1,1,1)`
(mirror-X), and check which candidate quaternion formula reproduces that
conjugated matrix exactly, across several independent random test
rotations (all candidates: `(x,-y,-z,w)`, `(-x,y,z,w)`, `(-x,y,z,-w)`).
`(x,-y,-z,w)` (equivalently the sign-flipped-but-equal `(-x,y,z,-w)`)
matched with `0.0` matrix error on every trial; the other candidate did
not. The same numeric-conjugation approach was extended to a full affine
4x4 (needed for inverse bind matrices): `M4 * A * M4` for `M4 =
diag(-1,1,1,1)` simplifies to "negate row 0 and column 0, leave `(0,0)`
alone" — verified against the matrix-multiply result including a
translation component, not just rotation.

Mirroring one axis also reverses triangle winding (a right-handed-front-
face mesh becomes left-handed-front-face and vice versa) — the
compensating fix (swap the last two triangle-index corners) was itself
verified against real corpus data, not assumed correct: recomputing 500
randomly sampled triangles' geometric face normals and comparing them
against the (also-mirrored) vertex normals gave 500/500 agreement, i.e.
the exported mesh renders right-side-out.

## The fix / general principle

Never apply a coordinate-handedness conversion formula from memory alone,
even one that "sounds right" or matches a formula seen in an unrelated
codebase — different engines pick different specific axis/quaternion-sign
conventions, and a plausible-but-wrong formula produces output that still
*looks* structurally valid (correct vertex/bone counts, passes a naive
glTF validator) while being subtly mirrored or inside-out in ways only a
visual inspection or an independent numeric check would catch. Instead:
(1) derive the formula by conjugating a known-correct transform (a
rotation matrix, an affine matrix) by the reflection you're applying, and
check the result against candidate formulas numerically with several
independent random test cases — this costs a few minutes with any
scripting tool (numpy is enough) and produces a formula you've *proven*
rather than *assumed*; (2) verify the winding-compensation separately,
against real decoded geometry (face-normal-vs-vertex-normal agreement is a
cheap, strong, corpus-scale check — see the `wmb-gltf.ts`
`pickTriangleWinding` precedent for the general technique, though that
case needed a per-triangle vote for an *ambiguous* authoring convention;
this case is a *known* engine-family transform, so one global rule, not a
vote, is both correct and simpler).
