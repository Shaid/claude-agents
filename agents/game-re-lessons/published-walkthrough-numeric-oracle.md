# A published fan walkthrough/bestiary can be a decisive numeric-data oracle, not just a screenshot source

**When it bites:** a stat or table field (HP, damage, price, resistance, drop rate) in a well-known commercial game has survived 2+ disassembly-only negative passes. Search the web for a walkthrough, bestiary or guide that claims **data-table** provenance before running another pass. Also: you're validating a decoded flag/enum field, a skill-effect record, or a name/roster table.

Fan communities often transcribe a game's internal tables by hand (debugger, save editor, leaked design doc), even for games with no romhacking tools. That makes them a byte-exact oracle independent of disassembly. This differs from `cross-platform-decode-oracles.md` (other ports of this game) and from `romhacking-community-tools-first.md` (fan code and tools).

**Check / fix:**
- **Look for an explicit provenance claim** in the page text, e.g. "taken from the internal data tables on the Wizardry disk, and checked against actual gameplay". Gameplay ranges ("hit me for about 40-60") are colour, not an oracle.
- **Decode first, then compare. Never copy the page's numbers into a record.** The page is ground truth for *values*, not layout. Treat every third-party artifact (walkthrough or GitHub repo) as one input, because they have their own errors.
- **Flags, bitmasks and type enums:** prefer *defining-mechanic identity* facts (the ability a player knows the item for) over prices or stats. Numbers drift across ports and editions. Defining traits don't.
- **Skill records shaped like `{property, value, condition}`:** check several parallel, well-documented skills that differ in one enum value. That confirms the byte position across the enum's range, not just one lucky match.
- **Name/roster tables:** test exact set membership against any published boss/enemy list. No provenance claim is needed, because you're checking membership, not trusting a number. Decoded extras not in the list are "role unconfirmed", not spurious.
- **A gameplay-observed source can still be decisive** when it gives a *precise* number and enough independent detail (other characters' qualitative traits) to rule out chance.

**Canonical example:** Wizardry 6 (Amiga). Monster HP/alignment survived 10 disassembly-only negatives (RollDice-caller census, death-message census, SUB/ADD mutation census, runtime attack-array trace, several refuted candidates). Snafaru's walkthrough (zimlab.com) claims data-table provenance. Fields decoded from the project's own bytes matched it 19/19 HP dice specs, 13/13 "number appearing", 80/80 AC-block bytes, 26/26 named resistances, 13/13 XP values and 9/9 percent gates. A full named row also fixed the order of the 13-element resistance array. The GitHub project `ndouglas/wiz6` read the 32-bit XP field as `u16` and mislabelled two dice fields.

**Variants:**
- FFVI (SNES, `ceres`): three sources gave 100/1200/10000 GP for the Tent. Ten defining-mechanic facts (Genji Glove dual-wield, Economizer 1 MP, Gale Hairpin preemptive, Excalibur Holy, four field-effect relics) mapped 10/10 onto single bits.
- Warriors of Legend (`middilgard`): a played-and-reported blog said "Brand started with only 20 strength". A 5-byte all-≤20 window shared across the 4 characters had exactly one candidate, and the other three's values matched the blog's class guesses.
- Knights of the Round (CPS1, `kolbold`): a 25-entry ROM name table contained 8/8 published bosses and 12/12 common enemies. 3 extras (ally, obstacle, boss alias) were kept as unconfirmed.
- Fire Emblem: Three Houses (`chimera`): `Death_Blow`/`Fiendish_Blow`/`Darting_Blow` ("+6 Str/Mag/Spd when initiating") decoded to `CombatPlus_*`, value 6, `DuringAfter_PP_Combat`. `Vantage` decoded to `Foe_Initiates_HP_Under_50`.

**History:** 5 recorded instances (Wizardry 6, ceres, middilgard, kolbold, chimera): full log in `_archive/published-walkthrough-numeric-oracle.md`.
