# In a shared/polymorphic record table, a column's role can vary by row subtype — and community field names are scoped to the rows the fans studied

**When it bites:** a single record table serves several entity kinds at
once (characters AND classes AND NPCs in one asset registry; units and
props in one placement table), a community template/editor names its
columns, and you are about to interpret a column's value for a row subtype
*different* from the ones the community tooling was built around —
especially when the community name is semantically loaded
("ngplusHair", "DLCOutfit", "sothisFusedID").

Confirmed on Fire Emblem: Three Houses (`chimera`, Switch): the 600-row
AssetID table serves playable characters, NPCs, *and* class models with one
8-field record. Its first int16 — community-named `ngplusHair` (Progenitor)
/ "NG+ Hair?" (010 template) — is a self/row-index on named-character rows
(where the fans looked), but on **class-asset rows** the same column holds
the paired hair/head-variant id for that class body (Enlightened One's rows
carry 71/72 = Byleth's fused-green hair; generic classes carry generic-hair
ids 197–515). Its seventh field — named `sothisFusedID` / `DLCOutfit`
(the community's two guesses, both from Byleth-adjacent rows) — is a
per-character special-appearance hair id across all 27 timeskip-aging
characters, not a Byleth-specific body. Both names actively misled two
passes: one shipped a refuted `+3049` body-pack resolution partly because
the name said "a special Byleth body should exist".

**Fix:** before trusting a column reading on row subtype B, re-derive it
from subtype-B rows alone — dump the column for each subtype separately and
check whether the value distribution/role is even the same (a self-index on
one subtype and a foreign key on another have very different shapes). Treat
community field names as scoped observations ("this is what the column
means on the rows this editor edits"), not schema. The cross-subtype join
is also an opportunity, not just a trap: the same value appearing on a
character row's field and on a structurally different row's field
(endgame-class rows, alt-person rows) is exactly the two-independent-
sources agreement that pins the field's real semantics — that join is what
cracked `sothisFusedID` after the name-led reading failed.

Sibling files: `community-table-name-mismatches-semantic-content.md` (a
whole *table's* name mischaracterizes its content); `per-object-field-dual-
role-identity-vs-transient-scratch.md` (the runtime-struct version — one
byte offset, different roles per object state/type).
