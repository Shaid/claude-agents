# A resolved numeric archive index for DLC/post-launch content can be a genuinely-empty reserved slot — the real asset ships as a loose, name-addressed file in an update-patch layer instead

**When it bites:** a gamedata table's ID resolution chain (assetId → some
per-kind table → a numeric archive index) is structurally confirmed correct
— the arithmetic is right, corpus-wide, for hundreds of other rows — but a
specific subset (usually the newest/DLC-added characters or a handful of
post-launch "refreshed" ones) resolves to an archive entry with
`decompressedSize === 0` (or the platform-equivalent "declared but empty"
marker). The instinct is to treat this as a data gap or a formula edge
case. It is neither: the content is real, it just isn't *in* the numeric
archive at all.

## The pattern

Post-launch content (a paid DLC cast, a bug-fix character-model refresh)
is frequently patched in as **loose files inside the update's LayeredFS/
patch-override tree**, addressed by their own **original filename**, not
folded back into the base numeric archive's index space. The container/
codec format is typically identical to whatever the base archive already
uses for that content class — no new format to reverse-engineer, just a
new *location* and a new *addressing scheme* to check.

Confirmed on Fire Emblem: Three Houses (`chimera`): the Ashen Wolves DLC
cast (Yuri/Balthus/Constance/Hapi)'s `resolveModelAssets()`-computed body/
head indices (e.g. `bodyPost=3233`) were all genuinely-empty DATA0 slots —
verified directly against the archive (`decompressedSize === 0` for all
eight resolved indices across all four characters). Their real geometry,
and separately Anna's own post-launch face refresh, ship only as loose
`nx/action/model/MC1xx_<Name><A|B>_0_P_{Body,Face}.bin.gz` files inside the
v1.2.0 update's `patch4` LayeredFS layer — the exact same "PACK" container
shape (`u32 sectionCount` + `{ptr,size}` table + an `_M1G` G1M section) the
base archive's numeric `pack_<N>` entries already used, decoded by the
*same* parser completely unmodified. This wasn't limited to the 4 brand-new
characters either: **7 other already-numerically-resolvable base-game
characters** (Catherine, Leonie, Gilbert, Death Knight, Jeritza, Edelgard,
Ferdinand) had their own post-launch model-refresh files sitting in the
identical patch tree, untouched by mesh export — an existing texture-only
scan (`build-assets.ts`'s `scanPatchDir()`) had found these files' embedded
textures months earlier, but nobody had pointed the already-solved mesh
*decoder* at them, because nothing about "the mesh format is solved" implied
"check the patch tree for loose files in that format too."

## What to do

1. **When a resolved numeric index comes back empty for DLC/post-launch
   content, don't stop at "the arithmetic reached an empty slot" — search
   every discovered update-patch/DLC layer for loose files matching the
   same content-family filename convention** (a directory name, an
   extension, a community-documented naming scheme like `nx/action/model/`
   here). If a texture-only or partial scan of that same patch tree already
   exists in the project, check what it *didn't* extract (geometry,
   audio, whatever the texture scan skipped) — the gap is often exactly
   the missing content.
2. **Bridging the two ID spaces needs an explicit lookup table, not a
   formula.** A loose file's name and a numeric archive index share no
   derivable key — build a small hardcoded map (character/record ID → file
   stem) rather than searching for a nonexistent arithmetic relationship.
3. **A same-content-family filename suffix pair (A/B, v1/v2, ...) with no
   documented meaning may be genuinely unrecoverable this pass.** Don't
   guess-and-silently-ship: gather what circumstantial evidence exists
   (structural differences between the variants confirm they're distinct,
   not near-duplicates; population-level frequency across other
   single-variant instances of the same naming scheme), pick the
   best-supported assignment, and **surface the uncertainty all the way to
   the visible output** (a UI status string, not just a code comment) —
   confirmed necessary here: no community documentation, disassembly
   trace, or emulator/screenshot capture existed to settle which of two
   naming-suffix variants was which semantic timeskip phase.
4. **A container-directory-and-loose-file redundancy is itself informative.**
   When the same character also has a working base-archive entry (e.g.
   Anna's body, or the 7 refreshed characters above), the loose file is
   additive/corrective, not a replacement — resolve the base archive first
   and only fall back to the loose file for genuinely-missing pieces, unless
   there's a reason to believe the patch's copy supersedes the base one
   (not established for every character checked this pass — left as an
   explicitly separate, lower-priority open question, not assumed).

Related: `bootstrap-catalog-boundary-not-content-boundary.md` (a different
flavor of "the catalog says less than the real content"),
`update-patch-ships-a-revised-struct.md` (the *table-structure* sibling of
this same "the update is prior art you haven't read yet" family — that one
covers a record layout changing shape, this one covers content existing at
all only in the patch layer), `executable-resource-path-registry-names-asset-ids.md`
(a different mechanism for the same underlying lesson: don't assume the
base/obvious source is the complete one).
