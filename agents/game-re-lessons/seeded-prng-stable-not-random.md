# PRNG-selected content is not "random per visit" — a deterministic seed makes it stable forever

**When it bites:** you've found a PRNG in a content generator (scene layout,
level dressing, encounter tables) and are about to describe the output it drives
as random, varying, or non-reproducible — especially if you're about to conclude
the content therefore can't be reproduced from static data.

Period generators almost never use an entropy source. The "random" content is a
pure function of a seed that is itself derived from position, index, or some
other stable quantity — so the same input reproduces byte-identical output on
every visit, forever. Calling that "random" in a doc leads the next reader to
believe reproduction is impossible and to reach for runtime capture.

Worked example (War in Middle Earth, Amiga, `middilgard` project): the scene
generator uses a Lehmer LCG, `state = (state * 125) mod 2796203`, and is seeded
**three** times per scene from different sources. The distinction that mattered:

- Scene objects and decorations are seeded from the **map tile position** —
  `(tileY << 16) | tileX` — so every one of the 16,160 tiles composes the same
  scene every single time.
- Only the clouds are seeded from a **free-running timer counter**, so only the
  clouds differ between visits.

A trace correctly recovered the mechanism but described the decoration placement
as "random per visit", and predicted that re-entering a location would show
different decorations. Emulator screenshots of the same location entered twice
refuted that immediately: pixel-identical scene geometry, only the clouds moved.
The trace was right; the word "random" was wrong, and it produced a wrong
falsifiable prediction.

**Fix:** whenever you find a PRNG driving content, trace the *seed* before
characterising the output, and write down which quantity each seeding uses. Then
say "PRNG-selected, stable per <seed source>" rather than "random". If more than
one seeding site exists, expect them to have different sources and different
stability — that split is often the whole answer.

**Cheap oracle:** capture the same location/level twice in an emulator, across
separate entries with real time between them. What is identical is
position-seeded; what differs is time- or state-seeded. That one comparison
partitions the content for you before you trace anything, and it costs two
screenshots.
