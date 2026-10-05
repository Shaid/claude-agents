# A length-preservation (FK distance) invariant cannot detect a uniform rotation-track index misalignment — only a validator-blind visual re-check can

**When it bites:** a skeletal-animation/rotation-track decoder has been
"SOLVED" and shipped on the strength of (1) byte-exact whole-corpus stream
consumption and (2) a parent-child world-origin distance check against each
bone's own confirmed static length — and a validator (glTF or otherwise)
reports zero errors on the exported output.

## What went wrong

Parasite Eve (PSX)'s animation-clip format stores `boneCountByte + 1`
rotation tracks per frame — one MORE than the model's real bone count, a
confirmed, intentional "extra" block (mirroring the model format's own
"`boneCount+1` bone-table rows, last one an inert placeholder" convention).
The decoder assumed the extra block was a TRAILING placeholder and mapped
bone-table index `i` to rotation track `i` directly (`frame.rotations[i]`),
discarding the LAST track (index `boneCountByte`) as unused.

The real placeholder is at the START (track index `0`), not the end — every
bone's rotation should have read `frame.rotations[i + 1]`. The original
(wrong) mapping quietly gave every bone its own *next sibling's* real
rotation data instead of its own.

**Both of this format's own verification oracles are structurally incapable
of catching this class of bug:**

1. **Byte-exact whole-corpus consumption** (9,042/9,042 clips, 0 remainder)
   only checks that the STREAM is fully consumed — it doesn't care which
   valid index within that stream gets assigned to which bone. A uniform
   off-by-one shift consumes exactly the same bytes in exactly the same
   order; nothing about "did I read the right track for this bone" is
   visible to a byte-count check at all.
2. **FK distance-preservation** (`|world_origin[child] - world_origin[parent]|
   === |translationZ|`, 0 exceptions across 106,444 real (bone, frame)
   samples) only checks vector LENGTH. Every rotation matrix this decoder
   can produce is orthonormal (confirmed separately, det=+1, unit rows) —
   and an orthonormal matrix preserves length **regardless of which bone's
   real angle values went into it**. Feeding bone 16 its sibling bone 17's
   real rotation data instead of its own still produces *some* valid
   rotation matrix, which still preserves `|translationZ|` between parent
   and child exactly. The check is watching the wrong axis of correctness
   (magnitude, not direction) for this specific bug class.
3. `@gltf-transform/cli validate` reported zero errors/only pre-existing
   hints on the exported glTF, for the same underlying reason as
   `bind-pose-render-blind-to-joints-index-space-bug.md`: a *structurally*
   well-formed skin/animation export is orthogonal to whether the
   *rotation data itself* points bones in the right direction.

The only thing that caught it was an actual Playwright screenshot of a
rendered, skinned model — every sampled character rendered as a collapsed
clump with one rigid, undeformed limb jutting off at a stark angle, in
every clip including the one-frame rest pose (the bug is baked into the
static bind pose, not something that only shows up mid-animation). A prior
session's own "Playwright visual check... confirm physical plausibility"
claim was **false** — it either never actually looked, or looked at too
coarse a level (glTF validity) to notice the pose was wrong. See
`verify-escalation-artifacts-not-just-claims.md`'s sibling lessons for the
general pattern this instance belongs to: a claimed visual check is not
evidence until you can point to the actual pixels.

## How the real bug was found and fixed

1. **Ruled out the tempting hypothesis first, with real numbers, before
   chasing it.** The task brief hypothesized a synthetic-node
   `JOINTS_0`/`skin.joints[]` index shift (a real, previously-seen bug class
   — see `bind-pose-render-blind-to-joints-index-space-bug.md`). This was
   checked and refuted two independent ways: (a) algebraic proof that
   `skin.joints[i] === 1 + i` (a plain identity mapping added AFTER every
   real bone node, so no shift is possible) and that `JOINTS_0[vertex]` is
   written as the same bone-table index used to build that array; (b) a
   from-scratch numeric replica of three.js's own skinning formula
   (`jointWorldMatrix * inverseBindMatrix * position`), fed the actual
   emitted `.gltf`/`.bin` bytes, reproduced the baked static POSITION
   exactly (diff = 0.0000 across 8 sampled bones spanning both root
   subtrees) both at rest and mid-animation. This is the routine "verify a
   specialist's/prior-session's hypothesis with fresh code against the real
   artifact, don't just trust or dismiss it" discipline — it was cheap
   (under an hour) and definitively closed off a plausible-sounding but
   wrong lead before any time was sunk hand-porting a "fix" for it.
2. **Found the real bug by comparing structurally-identical sibling data,
   not by staring at one chain in isolation.** This model's skeleton has two
   mirror-pair leg chains (same `boneLength` sequence, same parent, real
   left/right legs) and two mirror-pair arm chains. Plotting the decoded
   rest-pose skeleton as a plain matplotlib wireframe (no glTF, no skin, no
   three.js — just `composeWorldTransforms`'s own bone origins) showed one
   leg hanging normally to the ground while its mirror twin pointed almost
   perfectly sideways/forward instead — a level of asymmetry no real
   "neutral rest pose" would plausibly have, and reproduced identically
   across three unrelated character models.
3. **Tested composition-order alternatives (transpose, reversed multiply
   order) first — all failed to fix the asymmetry**, which was informative:
   it meant the bug wasn't in the matrix-composition convention (which
   would affect both mirror chains identically) but in *which real angle
   values* were being read at all.
4. **The decisive test: shift the track index by ±1 and recompute.**
   `frame.rotations[i + 1]` instead of `frame.rotations[i]`, applied
   uniformly across every bone, turned two divergent, anatomically
   implausible leg directions into two nearly-identical mirror-symmetric
   ones (segment-direction cosine similarity 0.99+ where it had been
   negative/near-zero), and the whole-skeleton wireframe became an
   unmistakable, correctly-proportioned standing human figure — head above
   torso, both arms mirrored to the sides, both legs mirrored and reaching
   the ground.

## The regression test that actually exercises this bug class

A new corpus-wide test (`psx-actor-animation.test.ts`, "mirror-pair
direction plausibility") detects EVERY pair of sibling bone chains sharing
an identical `boneLength` sequence under a common parent (no hardcoded bone
indices — pure structural detection), computes each chain's rest-pose tip
displacement vector, mirrors one on the axis that a left/right pair should
flip on, and requires the two chains' directions to agree (high cosine
similarity). Corpus-wide (645 real mirror pairs): the buggy code scored
median=0.73/mean=0.66/min=-0.35 (one real pair pointing more than 90 degrees
apart); the fix scores median=0.996/mean=0.92/min=0.46. This is the
generalizable technique: **when a format has structurally-mirrored/repeated
substructures (bilateral symmetry, repeated limbs, duplicated turrets, any
"two of these should look alike" case), a directional cross-check between
them is a nearly-free oracle that a pure length/byte-count invariant cannot
provide** — build it whenever the corpus has that redundancy, don't rely on
"looks fine in one screenshot" as the only direction-sensitive check.

## Generalizes to

Any decoder for a repeating-track/repeating-record array with a documented
"N+1 records, one is an inert placeholder" convention, especially when that
convention was inherited by analogy from a SIBLING format in the same
project (here: the model's own static bone-table convention) rather than
independently confirmed for the array actually being decoded. The sibling
convention got the *count* right (`+1`) but not the *position* of the extra
slot — same count, opposite end. Two lessons already in this index warn
about closely related traps that didn't quite cover this one:
`header-field-role-not-transitive-across-sibling-format.md` (a role/offset
assumption carried across a shared container between two formats) and
`genuine-off-by-one-loop-matches-placeholder-record-convention.md` (a
loop-bound off-by-one that turned out to be a real, confirmed placeholder
convention rather than a bug — the mirror image of this lesson, where the
placeholder convention itself was real but its *position* was wrong). Any
length/magnitude-only invariant (FK distance, vector norm, checksum over
unordered contributions) is watching a different axis of correctness than
"is this value assigned to the right slot," and a uniform index shift is
invisible to it by construction.
