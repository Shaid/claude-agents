# Two id spaces overlapping numerically is not a binding — check the MISS pattern's shape and the hits' semantics, not the hit rate

**When it bites:** you are testing whether an already-decoded field in table A
(`assetId`, `modelId`, a class/character id) *is* the id consumed by
subsystem B, because both happen to live in a similar numeric range, and a
direct lookup "resolves" for a good fraction of rows — say 55-75% — against
B's own real membership set. The field itself is not in doubt (it decodes
cleanly, it is confirmed elsewhere); the question is only whether B is the
table it addresses. **The single-instance variant bites just as hard with
only one data point**: a UI display-string table and an unrelated internal
gameplay-mechanism id table happen to assign the *same specific small
integer* (e.g. both use id 13), and the string's label ("Magic") reads as a
tempting, plausible name for what the mechanism id gates — before writing
that up as an answer, trace the ONE call site that actually consumes the
mechanism id with that literal value and check its real behavior against
the label, the same falsifier as the corpus-wide case below, just applied
to n=1. Confirmed a second time on Valkyrie Profile (PSX, `valkyrie`):
battle command-menu text id 13 spelled "Magic", and a command-category id
13 was independently under suspicion as "the id that opens the spell
list" — tracing that one `CATEGORY_CHECK(unit, 13)` call site found a
physical-projectile-targeting routine, not menu code, refuting the
coincidence outright. Two unrelated id spaces (a UI string table's own
ordinal, an internal per-unit category enum) had simply landed on the same
number by chance.

Distinct from the three sibling regimes, which all assume the target table is
right and ask about the *field*: `partial-resolution-rate-is-noise.md`
(40-70% = a missing whole-field transform), `weak-single-offset-fit-signals-
missing-indirection.md` (80-95% = an unopened indirection layer),
`dense-range-offset-fit-needs-identity-oracle.md` (~100% but the acceptance
test could not fail). This file is the case where the field is fine and the
**target space is simply a different space that shares a numeric range**.

## What happened

Fire Emblem: Three Houses (`chimera`, Switch). FE3H's class combat motion is
selected by a "motion-set id" — 223 distinct ids, 74-505, enumerated by the
`u32[]` id tables in the eleven `nx/action/motion/*_PACK.bin` containers.
Nothing in the gamedata tables was known to carry it. `ClassData`'s
`maleAssetId`/`femaleAssetId` (values 100-179) sit squarely inside that range,
and a direct test looked encouraging: **32/49** male and 29/49 female class
asset ids resolved to a real motion-set member.

Three cheap checks refuted it outright:

1. **Semantics of the resolved targets.** The packs are weapon-typed by
   filename (`KB_L_100`, `KB_L_300`, `KB_L_600`, `_R` = mounted). Under the
   hypothesis, Myrmidon — a sword class — landed in `KB_L_600`, and Soldier —
   a lance class — in `KB_L_100`. A binding that scrambles a property the
   target's own names encode is not a binding.
2. **Shape of the misses.** They were not scattered: asset ids **148-179**, a
   perfectly contiguous block that happens to be exactly *every advanced
   class*, missed 100%. Random overlap produces scattered misses; a structured
   miss block means you are looking at the boundary between two independently
   allocated spaces, not at gaps in one.
3. **Coverage the other way.** 165 of the 223 motion-set ids are referenced by
   no class asset id at all. Two spaces that were the same space would be
   roughly co-extensive.

## The rule

When two id spaces overlap numerically, the hit rate is the *weakest*
available evidence, because sequentially-allocated id blocks overlap by
construction. Before spending a pass on the "binding" you think you found:

- resolve 2-3 hits whose semantics you can independently name (a weapon type,
  a character, a rendered model) and check the target actually matches;
- plot the misses in id order — a contiguous block is a refutation, not noise;
- check the reverse direction's coverage.

And when it *is* refuted, that is real progress: it converts "we have a
candidate binding" into "no gamedata table carries this id", which is what
justifies moving the search to the executable.
