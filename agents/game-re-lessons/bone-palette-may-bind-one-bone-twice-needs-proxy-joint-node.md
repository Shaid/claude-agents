# A per-submesh bone palette may bind one bone twice with different matrices — glTF needs a proxy joint node, not a dedupe

**When it bites:** exporting a format that uses **per-submesh matrix
palettes** (a small per-draw-call array of bone bindings that vertices index
locally — near-universal on PS2/PS3/Wii/Switch-era engines, e.g. Koei Tecmo
G1M's `BoneBind` sets) into glTF by emitting one skin per palette. Also: any
`DUPLICATE_ELEMENTS` validator error pointing at `/skins/N/joints/M`.

## What went wrong

Mapping each palette to its own glTF skin is the natural, correct
representation — `joints[k]` and `inverseBindMatrices[k]` come straight from
palette slot k, so a vertex's raw local bone index needs no remapping at all.
But glTF requires `skin.joints` to contain **unique node indices**, and a
real palette may legitimately list the same bone in two slots with two
*different* bind matrices (a body binding and a cloth binding for the same
bone, say). The exporter then emits the bone's node twice and the validator
fails with `DUPLICATE_ELEMENTS`.

Both obvious reactions are wrong:

- **Deduping the slots** breaks the whole point of the mapping — slot indices
  must stay aligned with the vertex attribute's values, and the two slots
  carry different matrices that cannot be merged.
- **Falling back to a whole-skeleton skin** for those palettes throws away
  the real bind matrices, which is the bug this representation exists to fix.

## The fix

Give the repeat an **identity-transform proxy node parented to the real bone
node**. A glTF node with no `translation`/`rotation`/`scale` has the identity
local transform, so its world matrix equals its parent bone's exactly — the
skinning result is unchanged — while being a distinct node index that
satisfies uniqueness:

```
if (usedNodes.has(boneNode)) {
  jointNode = nodes.push({ name: `bone${bone}_alias${k}` }) - 1;
  (nodes[boneNode].children ??= []).push(jointNode);
}
```

## Why it will not show up in a sample

This occurred in **3 packs out of 1,257** across three games — 0 in two of
them. It surfaced only on a full-corpus in-process validator sweep, having
passed every spot check beforehand. That is the same lesson as
`external-validator-sample-insufficient-cli-spawn-slow.md`: for a validator
cheap enough to run in-process, run it over everything, because the
interesting conformance failures are the rare ones that depend on unusual
source data rather than on your code path. Related:
`gltf-joint-zero-weight-filler-duplicate-fear-untested.md` (the *other*
glTF joint-uniqueness rule, and why guessing at validator semantics instead
of testing them is expensive).
