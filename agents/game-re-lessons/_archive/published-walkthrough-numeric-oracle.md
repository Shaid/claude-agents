# A published fan walkthrough/bestiary can be a decisive numeric-data oracle, not just a screenshot source

**When it bites:** a stat-block/table-shaped field (HP, damage, price, drop
rate, resistance, capacity, ...) has survived 2+ disassembly-only negative
passes on a well-known commercial game — before another disassembly pass,
`WebSearch`/`WebFetch` for a walkthrough, bestiary, or strategy-guide page
for the exact game that claims **data-table** provenance, not just
gameplay-observed provenance.

This is a distinct, stronger move than either existing oracle lesson: it's
not `cross-platform-decode-oracles.md` (that's about ports/disassembly of
*this* game on another platform) and it's not
`romhacking-community-tools-first.md` (that's about fan *tools/source code*,
which most games — especially non-console, non-speedrun titles — never get).
A fan community can publish a decisive numeric oracle even for a game with
zero romhacking tooling, as long as someone transcribed the internal tables
by hand (via a debugger, a save-editor, or a leaked design doc) rather than
just recording what they observed in play.

**The tell to search for:** an explicit provenance claim in the page's own
text, e.g. "taken from the internal data tables on the Wizardry disk, and
checked against actual gameplay" (Snafaru's Wizardry VI walkthrough,
zimlab.com). Gameplay-only walkthroughs ("this monster hit me for about
40-60") are still useful colour but are not a byte-exact oracle — a
data-table claim is what makes the difference. Confirmed cracking Wizardry
6 (Amiga)'s monster HP/alignment fields after 10 prior disassembly-only
negatives (RollDice-caller census, death-message-caller census, SUB/ADD
mutation census, runtime-attack-array trace, several refuted field
candidates): every candidate field was decoded from the project's own raw
binary bytes *first*, then compared against the published table — 19/19 HP
dice specs, 13/13 "number appearing" specs, 80/80 AC-block bytes, 26/26
named resistances, 13/13 XP values, 9/9 percent gates, all exact. The
oracle also positionally confirmed the order of a 13-element resistance
array (matching a full row of named values, not just a multiset).

**Verify by decoding-then-comparing, never by copying the page's numbers
into the record.** The walkthrough is ground truth for *values*, not for
*byte layout* — decode candidate fields from your own binary/data files
independently, then diff against the published numbers. This also catches
the walkthrough's own errors: cross-referencing a public GitHub project's
field table for the same game (`ndouglas/wiz6`) alongside the walkthrough
found it reads a 32-bit XP field as `u16` (silently truncating every value
above 65535) and mislabels two dice-spec fields — useful corroboration on
the fields it gets right, actively wrong on others. Treat any single
third-party artifact (walkthrough or repo) as one input to cross-check
against your own from-scratch decode, not a source to trust wholesale.

**When several fetchable sources disagree on the same numeric value, a
qualitative mechanic-identity fact is often a stronger and cheaper oracle
than chasing consensus on the number.** Confirmed on FFVI (SNES, `ceres`):
verifying a decoded item/equipment property table by GP price alone hit
exactly this problem — three different fetched sources gave three
different prices for the same item (a "Tent," variously 100/1200/10000 GP
depending on which port/version/edition each source actually described),
none confirmable as authoritative for *this specific* US SNES ROM without
more digging than it was worth. Ten *qualitative* real-game-mechanic facts
— "Genji Glove enables dual-wielding," "Economizer makes every spell cost
1 MP," "Gale Hairpin guarantees a preemptive strike," "Excalibur is Holy-
elemental," and four field-effect relics whose own names state their
unique defining ability — were each unambiguous, essentially impossible to
misremember (they're the *reason a player would recognise the item's
name*, not a number that varies by patch/region/port), and each mapped
directly onto a single confirmable bit in the decoded record: 10/10 exact
matches, decisive on the first try. **Prefer a defining-mechanic identity
check (an ability, a type, a unique named effect) over a price/stat-value
lookup whenever the field under test is a bitmask/flag/type enum rather
than a continuously-variable number** — a flag either matches the game's
best-known defining trait for that item or it doesn't, with no plausible
version-to-version drift to explain away a mismatch. This doesn't replace
`published-walkthrough-numeric-oracle`'s core technique for genuinely
numeric fields (HP, damage, price) where no such qualitative anchor
exists — it's a preference to reach for first when both are available for
the same table.

**A gameplay-observed (not data-table-sourced) walkthrough can still be
decisive when the claimed number is precise and you can triangulate with
independent corroborating detail, not the number alone.** Confirmed on
Warriors of Legend (`middilgard`): a 2025 fan blog review (no claimed disk-
data provenance, just played-and-reported) stated as a specific in-game
fact that "Brand started with only 20 strength," alongside its own
(admittedly uncertain) class guesses for the other 3 starting characters.
Brute-force-scanning a character record for any 5-byte, all-≤20 window
shared across all 4 named characters found exactly one candidate, and it
hit Brand's number exactly; the *other 3* characters' values at the same
field then independently corroborated the review's separate, qualitative
class guesses (a tied double-max on two fields matched "possibly a wizard,
high Int/Wis"; another character maxed on the same field as Brand matched
"likely a fighter too") — multiple independent hits, not one coincidence.
A single vague gameplay range ("this enemy hit me for about 40-60") still
isn't a byte-exact oracle on its own — the difference-maker is a precise
number plus enough independent corroborating detail in the same source to
rule out chance, not the source's stated provenance.

**A decoded name/roster TABLE (not a single numeric field) has its own
cheap, decisive variant: exact-set-membership against a published boss/
enemy/character list, via a plain `WebSearch`.** Confirmed on Knights of
the Round (CPS1, `kolbold`): a `strings` scan of the assembled (fully
unencrypted, unlike CPS2) maincpu ROM found a 25-entry name table with no
obvious semantic label attached (just a repeating `[2 header words][ASCII
name]['/']` record). Two independent web sources (an arcade walkthrough
site and a character-catalogue wiki) each separately published this
game's boss list and common-enemy list; every single documented name
(8/8 bosses, 12/12 common enemies) appeared in the decoded table, with
zero mismatches or "close but wrong" near-misses. Unlike the numeric case
above, the check here isn't one falsifiable value — it's "does the
decoded *set* of names equal (or is it a superset of) the published
*set*", which is stronger the more names there are (getting 20/20 exact
string matches by chance approaches zero) and doesn't require the fan
source to claim internal-data-table provenance the way the numeric oracle
does — a plain "here's the boss list" summary page is enough, because
you're checking membership, not trusting a specific number. Entries in the
decoded table that *aren't* in either published source (this session had
3: an ally/NPC name, an obstacle-object name, and an alternate boss alias)
are not falsified by this — a fan source's coverage is rarely perfectly
exhaustive — so keep them as real-but-unconfirmed-role rather than
concluding they're spurious.

**A "published-skill-effect oracle" variant applies to symbolic/enum
fields (which property, which trigger condition) inside a skill/ability
record, not just scalar numeric ones.** When a record encodes an
ability/perk system as `{property enum, magnitude value, condition enum}`
triples, a handful of distinctively-shaped, well-known real skills can
decisively confirm *which byte holds which enum* — often more decisive
than a plain numeric field, for the same reason the defining-mechanic-
identity variant above works for flags: a qualitative "does this skill do
X under condition Y" fact is nearly impossible to misremember or drift
across versions. Confirmed on Fire Emblem: Three Houses (`chimera`): three
parallel skills — `Death_Blow`, `Fiendish_Blow`, `Darting_Blow` — are
publicly documented as "+6 to [Strength/Magic/Speed] when the user
initiates combat," and decoded to `property=[CombatPlus_Str/CombatPlus_Mag/
CombatPlus_AS]`, `propertyValue=6`, `conditional=DuringAfter_PP_Combat` for
all three, exact match; `Vantage` ("attacks first when attacked below 50%
HP") decoded to `property=Vantage_Effect`,
`conditional2=Foe_Initiates_HP_Under_50`, also exact. Three same-shaped
skills differing only in which stat they buff is a stronger check than one
skill alone — it confirms the *byte position* generalizes across the
enum's whole value range, not just one lucky match.
