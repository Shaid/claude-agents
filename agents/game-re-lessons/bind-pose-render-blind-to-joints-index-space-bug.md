# A bind-pose-only glTF render or validator pass cannot detect ANY skinning bug — joint order, joint field, or inverse bind matrices

**When it bites:** you're writing or accepting a skinned-mesh exporter (anything → glTF/GLB) as "verified" on a rest-pose render, a vertex scatter plot, or zero errors from `gltf-transform validate`. Above all: the exporter *computes* `inverseBindMatrices` as `inverse(world[joint])` instead of reading a stored bind-matrix palette, in which case every render is zero evidence.

At bind pose, `world[j] × IBM[j]` is the identity for every joint. A vertex assigned to the *wrong* joint therefore lands in the same place, and the validator only checks that `JOINTS_0` holds in-range indices. If the IBMs are derived from the same skeleton, this holds for **any** joint assignment, even a random one. Three independent index-space traps are all invisible this way:
- **Joint order:** `JOINTS_0` holds the vertex's bone position *within that mesh's `skin.joints[]`* (usually DFS order), not the source engine's bone id or array index.
- **Joint field:** the wrong source field is used as the bone entirely.
- **Joint value encoding:** the stored index is pre-scaled (e.g. slot ×3) and read raw.

**Check / fix:**
1. **Does the source ship bind matrices?** Grep the chunk list for a matrix palette (G1M `MM1G`, etc.) before reconstructing IBMs. A doc note saying "raw bind matrices (not used; world transforms recomposed instead)" means this bug is already written down.
2. **Use the stored palette as a per-entry oracle.** It settles field, index space and matrix in one pass (`stored-bind-matrix-palette-is-a-per-entry-identity-oracle.md`).
3. Build `skin.joints[]` in hierarchy order, build `inverseBindMatrices` in the **same** order, and write `JOINTS_0` through an explicit bone → slot inverse map. Bijection check: `order[boneToJointSlot[b]] === b` for every bone. This is necessary but **not sufficient**: it passes when the wrong field is used.
4. **Check the index encoding:** run a corpus-wide divisibility census on the raw stored joint values (`prescaled-joint-indices-divisibility-census.md`).
5. **Pose the model** with a real clip, or at least a synthetic per-joint rotation. A bind-pose image is never a skinning check. Bone-local geometry (physics cloth/hair chains) is the natural canary, because it needs a genuinely non-identity bind matrix to reach the body.

The same trap applies to any target that references joints by vertex-local slot: Godot, Unity `BoneWeight`/`bindposes`, COLLADA `<vertex_weights>`.

**Canonical example:** chimera's `g1m-gltf.ts` (Koei Tecmo G1M, shared by three titles). Palette entries are `{matrixId, clothId, boneId}`. The exporter used `matrixId` (an index into the `MM1G` IBM palette) as the bone and ignored `boneId`, and it derived IBMs as `inverse(world[joint])`. The bijection round-trip passed, `gltf-validator` showed zero joint errors corpus-wide, and Playwright screenshots of named characters looked right. Cloth and hair (`NUNO`/`NUNV`/`NUNS`, stored bone-local) gave it away: Manuela's robes and Rhea's hair sat heaped at `y ∈ [-13.8, 15.7]` while the body reached `y = 159.4`. Reading the real palette moved 642 of 10,614 Three Houses primitives onto the body and left the rest bit-identical.

**Variants (same exporter):**
- Joint order: the raw `matrixId` was written into `JOINTS_0` while `skin.joints[]` was in DFS order. On a 187-bone skeleton the orders diverge from position 7. After the fix, 187/187 bijection, 0 mismatches.
- Value encoding: stored bone indices are palette slot ×3 and were read raw for three corpora. That gave the wrong slot for values 3..N-1 and a silent slot-0 fallback above N.

**Related, different blind spot:** Parasite Eve (PSX, `parasite`) had a rotation-track off-by-one. It *does* corrupt the bind pose, but the FK distance-preservation check passes because any orthonormal rotation preserves length (`length-invariant-blind-to-track-index-misalignment.md`). If the only verification is an invariant that identity composites or orthonormality satisfy regardless, require a posed render.

**History:** 4 recorded instances (chimera ×3, parasite): full log in `_archive/bind-pose-render-blind-to-joints-index-space-bug.md`.
