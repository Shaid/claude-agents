# A game's own shipped item/skill/ability text can state the exact numeric constant a disassembled formula uses — a stronger, cheaper oracle than an external walkthrough

**When it bites:** you have already-decoded (or easily decodable) item,
skill, spell, or ability *flavor text* sitting in the same project, and a
disassembled formula reads a per-record byte and multiplies/adds it by
some constant whose semantic role is still hedged or unconfirmed — before
reaching for `WebSearch`/a fan wiki (`published-walkthrough-numeric-
oracle.md`) or accepting the field as merely "characterised, not solved."

This is a distinct, cheaper move than the external-walkthrough oracle:
it needs no internet lookup, no fan-community search, and no risk of a
wrong game revision/region — the text is already sitting in the same
disc image, often in the same TOC region as the code, and is frequently
*already extracted* by the project's own text/dialogue pipeline. RPGs and
many other genres routinely author self-documenting UI descriptions that
state their own formula's exact magnitude in bracketed or parenthetical
text (`"Raises INT [Skill LV x 30]"`, `"restores 50% of maximum DME"`,
`"Increases maximum DME [Skill LV x 200]"`). Where a walkthrough gives
you a plausible-range or thematic match, the game's own description text
gives you the **literal integer** the disassembled multiply/add
instruction should also contain — an exact match, not a plausibility
check.

Confirmed on Valkyrie Profile (PSX, `valkyrie` project): a 47-entry
per-character skill array had one byte (record `+0x84`) whose role was
narrowed to "contributes `+200 max HP` per unit" from the disassembled
formula alone, with no further confirmation. Cross-referencing all 14
stat-affecting skills' own already-decoded description strings against
`fcn.8005e5d8`'s raw multiplier constants found **14/14 byte-exact
matches, zero deviations** — including all four large, distinctive
multipliers (200, 30, 30, 20) that a coincidental field-alignment could
not plausibly reproduce by chance. Two of the fourteen rows also
independently re-confirmed a *different*, already-hedged field's name
(`record+0xCA` = RST): the skill whose description says "Raises RST"
is the only skill that writes that field, closing a name the project had
only inferred from an item's own thematic naming before.

**How to apply it:** once a candidate formula and a candidate item/skill
description corpus both exist, don't stop at "the numbers look
plausible" — literally grep or diff the description text's own stated
bracketed number against the formula's disassembled immediate/multiply
constant for every record you can pair up. A false alignment cannot
survive more than one or two matches on distinctive (non-1, non-obvious)
constants; getting a dozen-plus exact matches, including several large or
otherwise arbitrary-looking numbers, is decisive confirmation of both the
field's identity and the record→description pairing itself in one pass.
