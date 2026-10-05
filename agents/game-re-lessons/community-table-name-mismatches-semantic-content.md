# A community/fan table name can be exactly right about which file it is and still wrong about what it holds

**When it bites:** a community naming convention or 010-template gives an
undecoded gamedata table a plausible, semantically-loaded name (e.g.
"GrowthData"), and a task brief or prior pass builds an a-priori hypothesis
about the table's *content* — correlating it with a sibling table's
already-decoded field, expecting per-entity data — before any real bytes
have been read.

This is distinct from `community-format-name-mismatches-real-magic.md`
(which is about a name pointing at the *wrong file/magic entirely*). Here
the file identity is correct — right DATA0 index, right container, right
byte layout, template matches the confirmed record stride exactly — but the
name mischaracterizes what the records actually mean.

Confirmed on Fire Emblem: Three Houses (`chimera` project): a task
explicitly prioritized decoding "GrowthData" on the hypothesis that it held
per-character stat growth rates correlating with `PersonData`'s own
`baseGrowths` field. The community's own 010 Editor template (found and
matched byte-exact, no correction needed) revealed the real content: a
41-record combat-EXP-percentage-multiplier table indexed by *level
difference* (not character identity) plus a 98-record global EXP-to-next-
level curve. Both are engine-wide constants with **zero connection** to any
per-character field — the hypothesized correlation with `PersonData` was
false, and no amount of byte-matching would have found one, because the two
tables don't share an axis (one indexes by character, the other by level or
level-difference).

**Fix, generalized**: treat a community table name as a lead for *finding*
the right file (DATA0 index, filename-map entry, template to try) — never
as a description of its semantics until the actual decoded fields confirm
it. Read the template's own field list and the real decoded values before
building or reporting any hypothesis about how a table relates to another
one. When a name-implied correlation turns out false, that's still a real,
reportable finding (worth stating explicitly, as this pass did) — not a
failure to find data that should exist.
