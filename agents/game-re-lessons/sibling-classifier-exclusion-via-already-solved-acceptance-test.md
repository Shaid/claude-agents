# A coarse "contains a nested resource of type X" gate needs an exclusion pass against every other already-solved format that could legitimately embed an X too

**When it bites:** an asset-extraction pipeline's population gate for
category A is a broad structural test ("this container holds >=1 nested
sub-resource of type X anywhere inside it"), and the resulting population
looks suspiciously large, or specific members of it overlap TOC/directory
slot ranges another, already-solved format B in the same project also
claims — especially when B is a completely different content class (a room
background, a 3D model bundle) that only incidentally embeds its own
type-X sub-resource for an unrelated reason (its own texture store, its own
material).

Confirmed on Valkyrie Profile (PSX, `valkyrie`): `collectBattleSpriteBundles`
classified a TOC slot as a "battle sprite bundle" whenever it was a
`raw-other` container with at least one nested `SLZ`-wrapped TIM texture
found anywhere in a multi-block scan. This is a real, deliberate superset
(the collector's own doc says so) meant to also catch battle-arena
backgrounds reusing the same bundle shape — but it had no exclusion at all
against two *completely different*, already-fully-solved formats in the
same project that also happen to satisfy the identical test: every
composited room slot (§ 9.6.11-18) carries its own `regionType` 2 TIM
texture store for its tile art, and every object-model bundle slot
(§ 9.6.2/9.6.4) carries its own material texture. Re-deriving the
population fresh from raw disc bytes found exactly 1,123 slots (a range
this project's docs had already flagged as "the classifier over-collects
these") passing the old gate, partitioning **exactly** into 1,118 real
rooms + 5 object-model slots + 0 residue — a real classifier false
positive that had been shipping mislabeled manifest entries, not just an
inflated-but-harmless count.

**The fix that generalizes**: don't try to add a new positive
discriminator to the offending classifier (there may be no clean field to
key on — a room's texture store and a battle bundle's texture sheet are
byte-for-byte the same `SLZ`-wrapped TIM shape). Instead, reuse the
*already-established, already-verified* structural acceptance test the
sibling format's own collector uses, and exclude any candidate that passes
it. Here that meant literally calling the same `regionType`
2-TIM-plus-`regionType`-0-header/scroll/layer-directory-plus->=1-
composited-layer test `collectRooms` already uses (factored into an
independent predicate function so the room pipeline itself needn't be
touched), plus checking membership in the object-model collector's own
already-confirmed slot set. This is cheap because the sibling acceptance
test already exists and is already trusted — the fix is exclusion by
membership in a population you've already solved, not a fresh
discriminating-field hunt inside the format you're trying to fix.

**General takeaway**: whenever a project ships more than one collector
keyed off the same coarse structural signal (any nested resource of a
common, low-specificity container type — a texture, a string table, a
generic record block), audit each collector's population for overlap with
every *other* collector's already-solved slot range before trusting either
one's count. A large "still unclassified"/"over-collects" residual quoted
in a project's own docs is worth re-checking with exactly this technique
even when it's already been characterized as "known, low priority" — the
fix is often a fast, mechanical exclusion pass, not new format work.
