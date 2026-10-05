# A statistical proxy check that only exercises part of the corpus/body can still pass while a real visual defect remains

**When it bites:** A prior pass fixed a decode bug, verified it with a
corpus-wide statistical proxy test (a regression test asserting a threshold
on an aggregate metric — median cosine similarity, percentile distance, error
rate), and declared the result "confirmed correct" or "coherent" based on
that metric plus a spot-check screenshot. A later, independent re-verification
using the SAME kind of screenshot (not a different, weaker method) finds the
defect is still present — just in a different part of the data (a different
body region, a different subset of records) that the proxy metric doesn't
weight or doesn't cover at all.

## What happened

Parasite Eve (PSX, `parasite`)'s animation-clip decoder had a real
track-index off-by-one, fixed and verified via a new "mirror-pair direction
plausibility" regression test (645 sibling bone-chain pairs, median cosine
similarity 0.73 → 0.996) plus a Playwright screenshot claimed to show
"coherent, connected, non-collapsed figures" across 5 models and their real
clips.

An independent re-verification — using the exact same method (real headless
Chromium, the real offline viewer) — found the claim only partially true:
the fix genuinely eliminated the OLD failure mode (a fully collapsed clump),
but every model still rendered the lower body (hip/leg chain) as coherent
while everything above the waist exploded into a mass of disconnected,
wildly-displaced fragments. This was a SECOND, independent bug (multi-root
skeleton composition — 775/830 models have more than one bone with
`parentIndex === -1`, and every one beyond the true root was being treated
as an independent world-rotation root instead of composing onto the true
root's orientation), not a symptom of the first.

The mirror-pair-cosine test — the very thing that "confirmed" the fix — is
**structurally incapable of catching this second bug**: a secondary root's
own left/right mirror children move wrong TOGETHER, in the same way, so they
still mirror each other correctly even while both point in a completely
wrong absolute direction relative to the rest of the body. The test measures
relative agreement between siblings, not absolute correctness relative to
the skeleton root — and a bug that corrupts a whole subtree uniformly is
invisible to any check built only on relative agreement within that subtree.

## The generalizable pattern

A numeric/statistical proxy for "is this correct" is built to detect ONE
specific failure shape (here: two mirrored chains disagreeing on direction).
It says nothing about failure shapes orthogonal to what it measures (here: a
whole subtree — including both mirrored halves — being wrong in the same
way). This is the same root lesson as `length-invariant-blind-to-track-index-misalignment.md`
and `fk-distance-preservation-verifies-rotation-decode.md`'s corpus, but a
distinct concrete instance: it is not enough to ask "does my regression test
still pass" — ask "what failure SHAPE would this test be blind to", and
specifically check whether a uniform/systemic error across the exact
population the test compares (both siblings, both mirrored chains, both
halves of a symmetric structure) could still average out to a passing score.

## The fix

Treat a full-body visual inspection (every major body region, not just the
region the last bug happened to live in) as a mandatory complement to any
numeric proxy, every time a skeletal/pose decode is touched — not just once
after the "big" fix. When re-verifying an already-"confirmed" visual claim,
don't stop at reproducing the same screenshot the prior pass took; crop/zoom
to check regions the prior screenshot's framing might have let slide by
(here: the upper body was visible but easy to under-scrutinize at a small,
un-zoomed screenshot scale).
