# FK distance-preservation (parent-child bone distance == known static length) is a self-contained, no-external-oracle verification for a rotation/animation track decode

**When it bites:** a bone/joint hierarchy's *hierarchy* (parent links) and
*static lengths* (e.g. a per-bone `translationZ`/length scalar) are already
confirmed, and the only missing piece is per-frame *rotation* data — but
once a byte grammar, an Euler/quaternion-to-matrix formula, and a
hierarchical composition (forward kinematics) are all reverse-engineered
together, there is no external ground truth (no emulator screenshot, no
reference decoder, no sibling port) available to check the *combination*
is right. Getting any one piece wrong (byte layout, angle scale, matrix
formula sign, composition order) typically still produces plausible-looking
but subtly wrong output — not an obvious crash or garbage render.

**The check:** rotation matrices preserve vector length. So for every
parent-child bone pair, after composing world transforms for a given
frame, `|world_origin[child] - world_origin[parent]|` must equal
`|boneLength|` (or whatever static per-bone length field is already
confirmed) if and only if the ENTIRE chain — byte grammar, per-axis angle
decode/scale, the rotation-matrix-construction formula (including sign
conventions on individual terms), and the parent-to-child composition
order — is correct simultaneously. Any single wrong piece anywhere in the
chain breaks this distance for at least some frames/bones, because an
incorrect rotation is generically NOT length-preserving relative to the
true static length once composed through the hierarchy. This makes it an
extremely strong combined oracle: it requires no external reference,
generalizes to every bone/frame/clip in a corpus for free (once the
decoder function exists, checking becomes "loop over everything and
diff"), and its failure mode is quantitative (a numeric error, not a
subjective "does it look right").

**Confirmed** on Parasite Eve (PSX, `~/Development/parasite`): after a
`ghidra-disasm` trace produced a byte grammar, an Euler->3x3-matrix formula,
and a hierarchical GTE-based composition order, this check ran across
106,444 sampled (bone, frame) pairs spanning 821 models / 2,415 clips /
5,805 frames and found **0 exceptions**, max floating-point error
~2.27e-13 — strong enough to independently resolve the ONE line the
tracing agent itself flagged as its lowest-confidence guess (a matrix
term's sign): the wrong sign is generically non-orthonormal on its own
(confirmed separately via a 2,000-trial `det=+1`/unit-row sweep) AND would
have failed this distance check hard across the corpus, so passing it at
machine-epsilon precision is decisive confirmation, not coincidence.

> **Correction — the check is not as complete as "any single wrong piece
> breaks this" claimed above.** A later pass on this same project found a
> real bug this check cannot detect by construction: a uniform WRONG-INDEX
> read (bone `i` fed the rotation track that really belongs to a
> *different* bone, e.g. `i+1`) still uses some real, valid, orthonormal
> rotation matrix — and any orthonormal matrix preserves length regardless
> of *whose* real angle data produced it. The distance invariant is watching
> magnitude, not "is this the semantically correct value for this slot";
> it is decisive for the byte-layout/angle-scale/matrix-formula/composition-
> order errors described above, but structurally blind to a track/record
> *index* misassignment. Confirmed on this exact corpus: a track-index
> off-by-one (see `length-invariant-blind-to-track-index-misalignment.md`)
> passed this check across all 106,444 samples with the same 0 exceptions
> reported above, while producing an anatomically wrong pose (one leg
> pointing sideways instead of down). Pair this check with a DIRECTIONAL
> oracle too whenever the corpus has any repeated/mirrored substructure
> (see that file's "mirror-pair direction plausibility" technique) — don't
> treat a clean FK-distance pass alone as ruling out an index-assignment
> bug.

**Applicability beyond this project:** this generalizes to any skeletal
animation, IK chain, or hierarchical-transform format where (a) the
hierarchy and (b) at least one static per-bone scalar are already
independently confirmed, and only the per-frame rotation encoding is in
question. It does NOT verify translation-only or non-rigid (scaling/
shearing) transforms — those don't preserve distance by construction, so a
wrong decode there wouldn't necessarily fail this check. Pair it with a
secondary sanity check for *plausibility* (not just correctness) — e.g. a
frame-to-frame joint-rotation-delta distribution across many real clips:
real animation data shows a heavily right-skewed distribution (most joints
barely move most frames, median well under a few degrees, with a rare
tail of larger changes for fast motion), while a wrong decode tends to
produce a much flatter or more uniform-looking distribution.
