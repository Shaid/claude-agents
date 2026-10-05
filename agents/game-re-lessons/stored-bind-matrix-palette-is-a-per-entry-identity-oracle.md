# A stored bind-matrix palette gives a free per-entry identity oracle — and the entries that FAIL it are the signal, not noise

**When it bites:** a skinned-mesh format ships both a skeleton and a separate
matrix palette (an array of 4x4 matrices indexed by a per-bone-binding id —
Koei Tecmo G1M's `MM1G`, and the equivalent "matrix palette" / "inverse bind
pose array" in most console engines), and you need to work out which record
field is the bone, which is the matrix, what index space each lives in, or
whether a remap table applies. Also: any time such an invariant comes back
"holds for 92% of entries" and the 8% looks like a decode failure to chase.

## The oracle

For any vertex stored in **model space** (which is how ordinary body geometry
is authored), rendering at bind pose must reproduce the stored position. That
forces, per bone-binding entry:

```
world[resolveBone(entry)] x palette[entry.matrixId] == identity
```

This is exact, per entry, needs no external ground truth, and is cheap. On
Fire Emblem: Three Houses' 569 PACK models it held for **108,510 of 117,842**
bindings to full float precision (max deviation `0.0000`, worst case `0.0003`
float noise).

## The failures are the answer

The 9,332 entries that did *not* compose to identity were not errors — they
were exactly the bindings for **cloth and hair driven by a physics chain**
(`NUNO`/`NUNV`/`NUNS` sections), whose vertices are deliberately stored in a
*bone-local* space and need the real, non-identity bind matrix to reach the
body. Treating the non-identity minority as noise would have discarded the
one piece of information the whole format ships this palette for. A clean
partition — "identity" vs "a large, coherent rigid transform" — is a
classification result, not a residue.

## Using it as a hypothesis discriminator, not just a post-hoc check

The same invariant *derives* the resolution rule. Score every candidate
reading by its identity rate and the right one separates by a mile rather
than by a margin. On FE Warriors' `C_Camilla`, four readings of the bone id
were swept against the pack's real 245-bone rig:

| Candidate reading | Identity rate (per geometry block) |
|---|---|
| raw id, direct `bones[]` | 0/242, 0/96, 0/88, 0/24 |
| raw id, via `boneIndices[]` remap | 0/242, 0/96, 0/88, 0/24 |
| `id & 0x7FFFFFFF`, via remap | 3/242, 70/96, 60/88, 0/24 |
| **`id & 0x7FFFFFFF`, direct `bones[]`** | **218/242, 96/96, 88/88, 24/24** |

Every wrong reading scored ~0 and the right one scored ~100% (the shortfall
in the first block being the genuine cloth bindings). No render, no emulator,
no reference decoder involved. The same sweep also answers "which sibling
skeleton do these ids resolve against" and "does bit N of this field belong
to the index" in one pass — see
`bind-pose-render-blind-to-joints-index-space-bug.md` for why a render
cannot answer any of those.

**Generalizes to:** any format storing a redundant pair of "transform" and
"the thing the transform is relative to" — inverse bind matrices vs bones,
per-object world matrices vs parent hierarchies, precomputed normal matrices
vs rotations. Whenever the engine stores something your code could otherwise
recompute, the agreement between the two is a free, exact, per-record oracle,
and any systematic disagreement is a second content class you have not
identified yet.
