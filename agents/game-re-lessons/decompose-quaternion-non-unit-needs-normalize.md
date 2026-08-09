# A matrix-decompose-extracted joint rotation isn't guaranteed unit length

**When it bites:** building a glTF (or any TRS-node) joint rotation by
decomposing a real, game-sourced 3x3/4x4 transform matrix (e.g.
`THREE.Matrix4.decompose()`), especially one derived from confirmed-real
in-game data (an inverse-bind matrix, a bone-palette transform) rather than
hand-authored — a real WebGL render can look fine while the Khronos glTF
validator (`npx @gltf-transform/cli validate`) flags `ROTATION_NON_UNIT`.

Confirming a source matrix's rotation *rows* (or columns) are each
individually unit-magnitude — a common structural verification step for a
skinning/bone-transform format — does **not** guarantee the whole 3x3 block
is exactly orthonormal to float32 precision. `decompose()`'s extracted
quaternion inherits that residual non-orthogonality; a live corpus run
produced quaternions that failed the validator's unit-length check on real
data (Valkyrie Profile 2 (PS2), `IDOM` bone-palette rotation bases — each
row independently confirmed unit-magnitude per the format's own
verification, § 3.12.2, but the extracted joint quaternion still came out
non-unit on some real records).

**The fix**: call `quat.normalize()` on the decomposed quaternion
unconditionally before writing it into the glTF node, regardless of how
confident the source matrix's per-row verification already is. This is
correct regardless of *why* the residual exists (quantization noise, a
genuinely non-orthonormal source value, or something not yet understood
about the specific game data) — a renderer treats a node's `rotation` as a
unit quaternion unconditionally either way, so normalizing defensively is
never wrong and costs nothing.

**The general principle**: "each basis vector individually measures unit
length" is a *necessary* but not *sufficient* condition for "this is a
clean orthonormal rotation matrix" — don't let the former stand in for the
latter when the output feeds a component (a quaternion, an Euler
decomposition) that has its own independent normalization requirement.
