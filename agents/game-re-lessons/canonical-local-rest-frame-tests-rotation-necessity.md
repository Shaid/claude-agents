# A bone-local vertex-extent measurement can cheaply prove per-bone rotation is structurally required, before attempting a translation-only assembly

**When it bites:** a hierarchical-skeleton model format has confirmed
parent-child bone links and a per-bone length/offset scalar, but no
obviously-labeled per-bone rotation field, and the plan is to try
translation-only forward kinematics (stack each bone's mesh at its parent's
end point, no rotation) to see if it produces a recognizable pose before
concluding rotation data is required and searching for where it might live.

**The generalizable move:** before running that FK attempt (or after it
collapses everything into an unrecognizable blob and you're deciding whether
that's a bug or a structural fact), measure each bone's own vertex cloud's
extent along the bone's declared length axis, for two or more *structurally
different* bone/limb types (e.g. an arm segment and a leg segment, or a
torso segment and a neck segment). If every bone type shows the identical
pattern — vertices consistently spanning from ~0 to ~`-boneLength` (or
whatever axis/sign the length field implies) regardless of what direction
that limb actually points in the finished body — the meshes are authored in
a **canonical local rest frame**: a fixed per-bone local coordinate system
where a specific axis is always "the distal direction," independent of the
bone's real orientation once posed. This is a decisive, cheap (one
measurement pass, no rendering needed) proof that translation-only assembly
*cannot* work and real per-bone rotation is structurally required — you
don't need to run the FK attempt first and watch it fail to know this; the
measurement predicts the failure and also tells you the failure is a real
structural fact, not a bug in your traversal order or a missing field you
haven't found yet.

Confirmed on Parasite Eve (PSX)'s actor models: bone-table entries have a
confirmed hierarchy (`parentIndex`) and a `boneLength` scalar whose only
other confirmed role is `translationZ == -parent.boneLength` (fully
redundant with the parent's own length, carrying zero extra directional
information). A translation-only FK attempt in an earlier session collapsed
every limb onto the torso with no anatomical spread. This session measured
vertex extent along local Z for both arm-type and leg-type bones and found
both consistently spanning `~0` to `~-boneLength` — proving the meshes are
pre-authored in a canonical "elongate along local -Z" rest frame regardless
of real body direction, which structurally rules out translation-only
assembly rather than leaving it an open possibility pending a retry with a
different traversal order. This let the session move directly to hunting
for a rotation source (four candidates checked and refuted — see the
project's own doc for that trace) instead of re-litigating whether
translation alone might work under a different bug fix.

This generalizes to any hierarchical mesh/skeleton format (not just
PS1-era): a canonical local rest frame is a common authoring convention
because it lets an artist build each bone's geometry once in a neutral pose
without worrying about the character's final silhouette, and the same
"measure extent along the declared length axis, compare across dissimilar
limb types" test cheaply confirms or refutes it before investing time in a
translation-only shortcut or a bigger rotation-hunting effort.
