# A UE3 `Type'Package.Group.Name'` object-reference literal doesn't reliably name a separate file to open

**When it bites:** resolving a UE3 (or UE1/UE2) object-reference literal —
the T3D-style quoted syntax a decompiled `defaultproperties` block, a
generic `UObject.Decompile()` dump, or any other UELib/umodel text output
uses (`StaticMesh'BG50_20_UTZ_ld16_ILCA.Model.SMO_BG50_ground_LD16_001_ILCA'`,
`Sqex03DataGamePawnEdParam'prm_bs04.pdt_bs04'`) — and about to treat the
first dot-segment (`Package`) as the literal base filename of a separate
`.upk`/`.XXX` file to go open next.

Confirmed both ways on Drakengard 3 (PS3, `flower`), same engine, same
project, two different real outcomes: `game-re-lessons/
script-corpus-defaultproperties-reference-chain.md`'s boss-identity work
followed `prm_bs04.pdt_bs04` to a **real, separate, on-disc file**
(`PRM_BS04_SF.XXX` genuinely exists). But a later pass following
`StaticMesh'BG50_20_UTZ_ld16_ILCA.Model.SMO_BG50_ground_LD16_001_ILCA'`
found `BG50_20_UTZ_LD16_ILCA.XXX` **does not exist anywhere on disc** — the
referenced `StaticMesh` object is a real *export* inside the *referencing*
file itself (confirmed via `umodel -list` on that same file), and
`BG50_20_UTZ_ld16_ILCA` is a synthetic `Package`-typed object nested in the
export tree, purely a namespace/group label preserving the asset's
original pre-cook source package name. "Cooked seekfree" packaging
routinely inlines a level's own dependent assets directly into the file
that uses them (the same duplication behavior already established for
textures/materials in this project, confirmed here to extend to meshes
too) — when that happens, the `Package` segment of the reference is
metadata about where the asset *used to* live, not where to find it now.

**The generalizable rule**: a `Type'Package.Group.Name'` reference always
gives you the **bare object name** reliably (useful for a name-keyed
lookup against an already-built corpus-wide index), but the `Package`
segment is only sometimes a real separate file — it can equally be a
same-file namespace artifact of cooked/packed asset duplication. Don't
build filename-resolution logic that assumes one or the other
unconditionally; either (a) check the referencing file's own export table
first for an object of that bare name before trying to open a separate
file, or (b) sidestep the ambiguity entirely by indexing whatever corpus
you're resolving against by bare object name only (case-insensitive),
preferring an observation from the same file/package when multiple exist
and falling back to any match otherwise — the same "prefer same package,
fall back to any" shape already useful for cooked-seekfree texture/
material name collisions generalizes cleanly to this case too.