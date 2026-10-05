# Missing per-instance link metadata: test whether the resolution table is instance-invariant

**When it bites:** a format's decoder is already confirmed byte-identical across sibling games/containers, but *this* container gives no way to pair a decoded resource with the specific character/object instance it belongs to (no co-located sibling structure, no filename match, no embedded ID) — and the instinct is to treat this as an unclosable adapter gap.

Fire Emblem Warriors: Three Hopes centralizes every G2A animation clip (1,675 of them) into one shared package with zero co-located skeleton and no filename-based pairing, unlike its two sibling games (FE Warriors 2017 matches clip file to model file by name; Three Houses embeds clips in the mesh's own container). Before writing this off as "decoder transfers, pairing doesn't," a cheap test closed most of the gap: a G2A clip's `boneId` only becomes a real bone index by way of a skeleton-owned remap table (`G1MSkeleton.boneIndices`). Byte-diffing that remap table across the 9 highest-bone-count mesh skeletons in the corpus (one per playable character) found it **byte-identical across all 9** (0/1,105 entries differ), despite the skeletons' own bind-pose bone *positions* differing (different body proportions per character). That means `boneId` resolution is skeleton-independent game-wide — any one of those skeletons can stand in as a shared reference rig for the whole clip corpus. Using the single global "most bones" skeleton resolved 88.6% of all tracks in-range and gave every one of the 1,675 clips at least one resolved track, with zero new container structure discovered.

The general move: when a format's per-instance *linking* metadata is missing, don't stop at "no pairing recoverable." Check whether the *resolution mechanism* a instance-specific field depends on (a remap/lookup table, an index space, a bit-width convention) is itself invariant across the corpus's plausible instances. If it is, any single instance can substitute as a working reference even though which *specific* instance a given resource "really" belongs to stays unknown — worth shipping as a rendered, clearly-labeled best-effort result (not a false "confirmed per-instance" claim) rather than leaving the whole resource undecoded.

## Follow-up on the same game: when a real pairing does turn up, narrow it with a structural key

The substitute-rig result above is the floor, not the ceiling. A later pass
on the same corpus decoded the game's *other* animation format (G1A), and
those 356 clips **do** each share an `.fdata` package with a model. Two
refinements worth carrying forward:

- **Raw container membership is a candidate set, not an identification.**
  "Every model in this clip's package" gave 35,262 model references for 356
  clips, because bulk-prop packages hold 114-341 models each — technically a
  pairing, practically useless. Requiring the co-located model to *also*
  carry the exact structural key the clip already resolved against (here the
  same `boneIndices` topology signature) collapsed it to **exactly one
  candidate for 213 of 356 clips, and at most four for 271**. Whenever
  co-location hands you a set, intersect it with an already-decoded
  structural key — topology signature, format version, dimension, stride —
  before reporting the set as the answer.
- **A newly-known-correct pairing is a reason to re-run oracles you
  previously ran against a substitute.** The quaternion-conjugation question
  for the sibling G2A format had been settled using the *best-fit* rig; re-run
  against each clip's own co-located rig, the same bind-pose-proximity test
  came out **11.8x sharper** (mean 0.0363 rad as-decoded vs 0.4275 rad
  conjugated). The same setup also answers a question the substitute rig
  cannot: **81.6% of position tracks reproduced their bone's bind-pose
  translation exactly** (< 1e-3), which is what proves the tracks store
  absolute local TRS rather than deltas. Both are free once the right rig is
  known, and neither is trustworthy before that.
