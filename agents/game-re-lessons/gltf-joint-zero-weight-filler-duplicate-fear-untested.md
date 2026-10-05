# A zero-weight glTF JOINTS_0 filler slot can safely repeat any real joint (including 0) — the duplicate-index validator rule only fires on nonzero-weight collisions

**When it bites:** a skinned-mesh -> glTF exporter has to fill a vertex's
unused `JOINTS_0`/`WEIGHTS_0` slots (fewer than 4 real bone influences) and
picks a filler joint index by hunting for one "not already used" by that
vertex's real (nonzero-weight) pairs — on the theory that reusing an
already-used joint (especially `0`) would trip `gltf-transform validate`'s
`ACCESSOR_JOINTS_INDEX_DUPLICATE` check. Also: reviewing/inheriting such a
"hunt for an unused slot" heuristic from an existing exporter without
having actually run the validator against the simpler alternative.

## What went wrong

Fire Emblem: Three Houses' G1M mesh exporter (`chimera` project,
`g1m-gltf.ts`, shared with two sibling Koei Tecmo titles) filled a vertex's
leftover zero-weight `JOINTS_0` components by searching for the lowest
joint slot index not already occupied by a real (nonzero-weight) pair on
that same vertex, with an explicit code comment justifying it: reusing
joint 0 would supposedly make the validator flag it as a duplicate of a
real slot. That theory was never actually tested against the real
validator — it was a plausible-sounding assumption carried into the code
as a permanent workaround.

Rebuilding the full mesh corpus and running `gltf-validator` (the
`@gltf-transform/cli` / `gltf-validator` npm package, in-process via
`validateBytes`) found the "unused slot hunt" version produced **12,261
`ACCESSOR_JOINTS_USED_ZERO_WEIGHT` warnings** on a single 30-submesh mesh
alone (the rule: a `JOINTS_0` component with zero weight but a *nonzero*
joint value is itself flagged, precisely because picking a distinct
nonzero filler index to avoid one problem creates this different one).
Switching the filler to always be joint `0` — matching a sibling exporter
(`wmb-gltf.ts`, WMB3/PlatinumGames, already independently confirmed clean
corpus-wide) — produced **0 warnings and 0 errors of any kind** across the
same corpus, including on vertices whose real, nonzero-weight pairs
*already* used joint 0 themselves.

The actual `ACCESSOR_JOINTS_INDEX_DUPLICATE` rule (checked directly in the
`gltf-validator` package's own `ISSUES.md`): "Joints accessor element ...
has value ... that is already in use **for the vertex**" — this is
triggered by *any* repeated index per the validator's literal wording, but
empirically (confirmed by the 0-warning corpus-wide result above) it does
not flag a duplicate between a zero-weight filler slot and a real
nonzero-weight slot sharing the same joint. The two rules trade off
against each other in exactly the way the original workaround was trying
to avoid — but got backwards, treating the (harmless) duplicate as more
dangerous than the (flagged) zero-weight-nonzero-index case.

## The fix

For any unused `JOINTS_0` component (weight `<= 0`), set the joint index
to `0` unconditionally — never hunt for an "unused" index. Weight `0`
means the value is inert regardless of which joint it names, and the real
validator has no rule punishing that specific repetition. This is also
simpler code (no per-vertex "used" set to build) and matches the glTF
ecosystem's de facto convention.

**General principle:** when a decode/export workaround exists specifically
"to satisfy validator rule X," don't assume the causal story behind it is
correct just because the code has been shipping without error — the
absence of rule X's failure doesn't confirm the story, it's also
consistent with rule X never having been at risk in the first place. Test
the simpler alternative against the real validator before trusting an
inherited or self-authored avoidance heuristic.
