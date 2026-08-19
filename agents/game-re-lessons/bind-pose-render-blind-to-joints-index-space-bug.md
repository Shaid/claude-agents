# A bind-pose-only glTF render or validator pass cannot detect a JOINTS_0-index-space bug

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
