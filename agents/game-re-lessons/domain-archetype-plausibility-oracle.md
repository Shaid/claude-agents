# A licensed property's own well-known rules are a cheap, strong oracle for stat-block data

**When it bites:** a stat-block-shaped table (RPG class/character stats,
monster stats, a sports-roster stat line, any tabular data from a game
built on a licensed property with public, well-known rules) has been found
via text search or disassembly, no fan walkthrough/bestiary is available
(so `published-walkthrough-numeric-oracle.md` doesn't apply), and you need
verification stronger than "the numbers look plausible."

The license's *own* source material already publishes the rules the data
must obey — use that directly. This is stronger than generic plausibility
because it's checking many independent, specific, falsifiable predictions
at once, not one vague "looks reasonable" judgment.

Confirmed on D&D: Shadows over Mystara (CPS2, `kolbold`): a `strings` scan
of the plain (undecrypted) maincpu data region found a 6-row ASCII table
labelled `LEVEL/AGE/HIT POINTS/STRENGTH/DEXTERITY/INTELLIGENCE/
CONSTITUTION/WISDOM/CHARISMA` — unambiguously a D&D ability-score block by
its own column labels, but the *row-to-class* assignment and the general
"is this real, human-authored game data" question still needed
verification. D&D's own published class archetypes gave six independent,
specific, falsifiable predictions, and every one held:

- the **fighter** has the highest HP (47) and ties the highest STR (12);
- the **magic user** has the lowest HP (15) and lowest STR (5) but the
  highest INT (17);
- the **thief** has the highest DEX (16);
- the **dwarf** has the highest CON (12);
- the **elf** has by far the highest AGE (101, vs. 24-60 for every other
  class — matching D&D's long-lived-elf trope specifically, not just "a
  higher number").

Six archetype checks across 6 classes and 9 stat columns, all consistent —
this is not something unrelated binary data or a monotonic counter could
produce by chance (contrast
`monotonic-integer-table-mimics-smooth-color-gradient.md`, where smoothness
alone was a weak, easily-faked signal; here the signal is many *specific*,
independently-falsifiable cross-row inequalities, not one smooth trend).

**How to apply it elsewhere:** identify the license's small number of
well-known, essentially undisputed rules (a superhero's signature power
level, a real sports league's positional stat conventions, a licensed
franchise's canonical character strengths/weaknesses) and turn each into a
specific, falsifiable prediction about the decoded table — not "does this
seem right" but "does row X beat row Y on field Z, as the source material
requires." The more independent predictions that hold simultaneously, the
stronger the confirmation; one match is coincidence, four to six matching
across different characters/fields is not.

**Boundary with `published-walkthrough-numeric-oracle.md`:** that lesson is
for byte-exact numeric values sourced from a fan transcription of the
game's own internal tables (strong when available, but requires a fan
community to have done the transcription work). This lesson applies even
with zero fan community involvement, because the "oracle" is the public
domain rules of the licensed property itself — weaker on exact values (it
confirms *relative* ordering/archetype-fit, not that "47" is definitely the
correct fighter HP rather than "46"), but available for any licensed
property, not just games with an active romhacking/strategy-guide fandom.
