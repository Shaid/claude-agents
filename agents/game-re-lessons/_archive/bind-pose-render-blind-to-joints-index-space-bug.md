# A bind-pose-only glTF render or validator pass cannot detect ANY skinning bug — joint order, joint field, or inverse bind matrices

**Strongest trigger — check this before anything else in this file:** if the
exporter *computes* its `inverseBindMatrices` from the same skeleton it just
built (`inverse(world[joint])`) instead of reading a bind-matrix palette out
of the source file, then every "it renders correctly" observation about
skinning is vacuous — not just about joint *order* but about which source
field was used as the joint at all. The bijection check this file originally
prescribed as "the test that actually catches this class of bug" passes
cleanly on that version. See "The deeper version" at the end.

**When it bites:** writing a skinned-mesh exporter (any format -> glTF/GLB)
that resolves each vertex's controlling bone to some kind of "global bone
index" (a skeleton array position, a hash, a runtime bone ID) and writes
that value straight into the `JOINTS_0` vertex attribute. Also: reviewing
or accepting such an exporter as "verified" on the strength of a rest-pose
render (a T-pose/bind-pose screenshot, a 2D vertex-position scatter plot)
plus `gltf-transform validate`/the official glTF validator reporting zero
errors.

## What went wrong

glTF's `JOINTS_0` attribute does not hold a bone ID, a skeleton array
index, or any format-native identifier — it holds each vertex's bone's
**position within that mesh's own `skin.joints[]` array**, and that array
is commonly built in tree-traversal (DFS) order for a clean parent-before-
children glTF node hierarchy, not in the source format's raw bone-index
order. A G1M (Koei Tecmo Warriors-engine) -> GLB exporter wrote the
source format's own resolved bone index (a field literally named
`matrixId` in the source data) directly into `JOINTS_0`. This is silently
wrong whenever the DFS traversal order differs from raw bone-index order —
confirmed on a real 187-bone skeleton, where the two orders diverge
starting at position 7.

**Every check run at the time passed anyway.** `gltf-transform validate`
(the official Khronos glTF 2.0 conformance validator) reported zero errors:
`JOINTS_0` values were still valid indices into an array of the right
length, with no duplicates, so nothing about the accessor's *shape* was
wrong. A 2D scatter plot of raw decoded vertex positions — done entirely
independently of the skinning code, as a structural sanity check on
position decoding — rendered a correct, recognizable T-pose humanoid
silhouette. Neither check can distinguish this bug from correct code,
**because at rest pose every joint's world transform composed with that
same joint's own inverse bind matrix is the identity matrix, for every
joint, always** — so picking the *wrong* joint index for a vertex still
applies an identity transform at rest, and the vertex lands in exactly the
same place either way. The bug is completely invisible until the model is
actually posed away from bind pose (i.e. animated), at which point vertices
skinned to the wrong joint tear away from the mesh incoherently.

## The fix, and the test that actually catches this class of bug

1. Build `skin.joints[]` in whatever order the glTF node hierarchy needs
   (DFS from the skeleton roots is typical).
2. Build the `inverseBindMatrices` accessor in that **same** order — a
   second, easy-to-miss instance of the identical index-space confusion:
   computing IBMs in raw bone-index order while `skin.joints[]` is in DFS
   order produces the same class of silent, bind-pose-invisible bug.
3. Build an explicit inverse map (bone/matrixId -> its position/slot within
   that DFS order) and use *that* — never the raw bone index — whenever
   writing `JOINTS_0`.
4. **Verify with a bijection check, not a render**: for every bone `b`,
   confirm `order[boneToJointSlot[b]] === b`. This is a pure structural
   check on the two index spaces' consistency — cheap, deterministic, and
   it is the one check that actually exercises the bug, unlike any
   render/validator check run at bind pose. (Confirmed 187/187 bones, 0
   mismatches, after the fix.)

This generalizes past glTF: any export target with a "skin/joints array,
referenced by vertex-local position rather than by the source engine's own
bone identifier" convention (Godot's `.gltf`/`.glb` importer, Unity's
`BoneWeight`/`bindposes` pairing, COLLADA's `<vertex_weights>` `joint`
input) has the same trap, and the same "rest pose can't distinguish
correct from wrong" blind spot applies to verifying against any of them.

## The deeper version: the bijection check above is NOT sufficient

A later pass on the **same exporter** (chimera's `g1m-gltf.ts`, now shared by
three Koei Tecmo titles) found a strictly worse bug that the fix above does
not catch and the bijection check certifies as clean. The exporter was using
the wrong *field entirely* as the joint: G1M bone-palette entries are
`{matrixId, clothId, boneId}`, and `matrixId` — which indexes the format's
own `MM1G` inverse-bind-matrix palette — was being read as the bone index,
while `boneId`, the actual bone, went unused. The `boneToJointSlot`
round-trip was still a perfect bijection, `gltf-validator` still reported
zero joint errors corpus-wide, and real Playwright screenshots of several
named characters still looked right.

**Why nothing caught it:** the exporter also *derived* each inverse bind
matrix as `inverse(world[joint])` from whatever joint it had chosen. For any
joint `j`, `world[j] x inverse(world[j])` is the identity, so the bind-pose
skinned position equals the stored vertex position **for every possible
joint assignment**. The renders were not weak evidence — they were zero
evidence, and would have been identical if joints had been assigned at
random.

What finally exposed it was the one class of geometry that cannot survive a
wrong bind matrix: **cloth and hair driven by a physics chain** (Koei Tecmo
`NUNO`/`NUNV`/`NUNS`, and the equivalent in most engines) store their
vertices in a *bone-local* space, so they need a genuinely non-identity bind
matrix to reach the body. Discarding the stored matrices left them at raw
local coordinates — Manuela's robes and Rhea's hair rendered heaped on the
ground at `y ∈ [-13.8, 15.7]` while the body reached `y = 159.4`. Reading
the real palette moved 642 of 10,614 Three Houses primitives onto the body
and left the other 93.95% bit-identical.

**Additional checks worth running, in order of strength:**

1. **Does the source format ship bind matrices at all?** Grep the container's
   subsection/chunk list for a matrix palette (G1M's `MM1G`, and the
   equivalent in other engines) before writing any code that reconstructs
   IBMs from the skeleton. A format that stores them stores them for a
   reason. A doc note calling such a section "raw bind matrices (not used —
   world transforms are recomposed from local bone transforms instead)" is
   this bug already written down.
2. **Use the stored palette as an oracle** — see
   `stored-bind-matrix-palette-is-a-per-entry-identity-oracle.md`. It settles
   joint field, index space and matrix in one pass, per entry, with no
   external ground truth.
3. **Pose the model.** If no bind matrices ship, applying any real animation
   clip (or even a synthetic per-joint rotation) is the minimum bar; a
   bind-pose image is not a skinning check under any circumstances.

## Third instance, same exporter: the vertex index itself was mis-decoded

A 2026-09 pass found yet another bind-pose-invisible layer in the same
`g1m-gltf.ts`: the vertex's stored bone-index values are palette-slot **x3**
(engine byte-offset convention), read raw for three whole game corpora —
wrong slot for values 3..paletteSize-1, silent slot-0 fallback above that.
Same blindness mechanism (identity composites at bind), caught by a
corpus-wide divisibility census — see
`prescaled-joint-indices-divisibility-census.md` for the cheap decisive
test. Moral: joint *order*, joint *field*, and joint *value encoding* are
three independent index-space traps, and bind-pose evidence is blind to all
three.

## A sibling bug class with a different blind-spot mechanism

Parasite Eve (PSX)'s animation-clip decoder (`~/Development/parasite`) hit a
structurally different but equally invisible bug: a rotation-*track*-index
off-by-one (bone `i` read track `i` instead of `i+1`, an inherited-by-analogy
wrong guess at which end of a confirmed `+1`-record convention held the
placeholder — see `length-invariant-blind-to-track-index-misalignment.md`).
Unlike every case above, this one is **not** bind-pose-invisible in the
identity-composite sense — it corrupts the rest/bind pose itself, since the
wrong track gets read even for frame 0. What made it invisible instead was a
different oracle's blind spot: the format's own FK parent-child
distance-preservation check only verifies vector *length*, and any
orthonormal rotation matrix preserves length regardless of *whose* real angle
data produced it, so a uniform track-shift passes that check exactly as
cleanly as a correct decode. Filed as a separate lesson because the
underlying trap is orthogonal to joint-index-space confusion (it's a
data-source mixup, not a coordinate-space mixup) — but it belongs in the same
mental bucket: **whenever a skinning/rigging pipeline's only verification is
a single invariant that composite-identity or matrix-orthonormality can
satisfy independently of correctness, treat a real render (not bind pose, not
"passes at rest," and ideally posed away from rest) as mandatory before
calling it verified.**
