# Merging a second content source into an already-populated content-addressed manifest needs explicit source precedence, not last-writer-wins

**When it bites:** an asset pipeline promotes a *second* data source
(DLC, an expansion pack, a patch, a sibling release) into a manifest
already populated from a *first* source, using the same "upsert by name"
merge convention the pipeline already relies on for idempotent re-runs of
a single source.

Confirmed on Drakengard 3 (PS3, `flower` project): the base-game pipeline
and a new DLC pipeline both write into the same `manifest.json`, keyed by
`<package>__<object>` — a name derived purely from content, with no
source tag baked in. UE3's cooked-seekfree packaging duplicates some
shared dependency packages **byte-for-byte identically into both the base
disc dump and one or more DLC packs** (a results-screen UI icon pack, a
boss AnimSet reused across a scenario DLC's own cutscenes) — real,
confirmed, not a hypothetical edge case. Because the DLC pass always runs
after the base pass, its promotion of these shared packages silently
overwrote the base game's own already-correct manifest entries under the
exact same name, real bytes just as valid but now mis-tagged with the
DLC's own metadata (`source: "dlc"`, a `dlcId` that only applies to one of
the two places this content actually ships). Caught only by noticing the
merged manifest's total entry count was smaller than the sum of what each
source's own promotion pass reported — a silent, symptom-free bug
otherwise (both versions of the content are equally valid PNGs/meshes; the
only wrongness is the *metadata* now claims a narrower scope than reality).

**The fix**: when a manifest's key doesn't include a source discriminator
(and adding one would be a bigger schema change than the bug is worth),
give the merge step **explicit source precedence** instead of trusting
insertion order: decide which source is authoritative for a same-name
collision (here: the disc dump, since it's the project's primary,
independently-verified source per its own docs) and skip the upsert when
a lower-priority source's entry would clobber a higher-priority source's
already-present entry, while still allowing same-source-to-same-source
upserts (idempotent re-runs) and a *higher*-priority source refreshing a
stale lower-priority entry. Verified the collision was real, not
theoretical, before writing the fix — grep the *before* merge's raw
per-source counts against the *after* merged total; a gap is the signal.
