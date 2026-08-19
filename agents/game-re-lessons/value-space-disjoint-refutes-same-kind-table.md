# Disjoint value spaces refute "the same table", never "the same format"

**When it bites:** an unidentified small blob has been filed as "probably a
terrain grid / tile map / index array / stat block" purely because its byte
pattern *looks like* one you already solved, and you're about to spend a
session hunting its dimensions or importing that format's semantics — **or**
you have just run the cheap value-set comparison below, got a disjoint
result, and are about to close the item as "not that format."

The cheap test is worth running. The strong conclusion people draw from it
is wrong, and it cost this exact project a wrongly-closed item.

## The test

Take `set(candidate_bytes)` and `set(confirmed_table)`; report the overlap
count, the overlap as a fraction of the candidate's distinct values, and
whether the confirmed table uses **any** value in the candidate's occupied
range. It costs one script — no rendering, no dimension search, no
disassembly.

## What the result actually licenses

A disjoint result refutes **"this is the same table, or a table covering the
same region"**. It does *not* refute "this is the same format."

The confound that matters is a **partitioned value space**. A well-designed
shared index space assigns contiguous bands to terrain types, biomes, or
roles — so two instances of one format covering *different regions of the
game world* are **expected** to be disjoint, not suspicious. The same
authoring tool emitting two same-purpose tables with no shared vocabulary
isn't just possible; on a banded tileset it is the normal case.

Before concluding "not this format," decide which kind of value space you
are in:

- **Global** — every instance draws from one flat pool (a string table, a
  single sprite bank, a monster roster). Disjointness is genuinely strong
  evidence here.
- **Partitioned** — the value space is carved into ranges by role, and
  instances occupy different ranges by design (tilesets, terrain bands,
  per-area palettes). Disjointness carries **almost no information**.

## The confirmed failure

Phantasie III (Amiga, `nicodemus` project). Four `D/PLN1`-`PLN4` files were
compared against the game's already-decoded overworld map (`phantasy.set`, a
50×75 array using 196 distinct values). The measurement was clean and
correct: **0 of `pln1`'s 11 distinct values and 0 of `pln2`'s 11 occur
anywhere in that 196-value set**, and `phantasy.set` uses nothing at all in
the 55-80 band where `PLN*` lives. It was written up as "whatever `PLN*`
encodes, it is not a `.set`-style map array" — and the item was closed on
that basis for a full session.

`PLN1`, `PLN2` and `PLN4` **are** `.set`-space map arrays. They are the
castle-interior (9×9) and Netherworld (31×16) maps — different maps in the
same game, in the same format, legitimately occupying different bands of a
partitioned space. The engine's own terrain classifier reads `61`-`67` as
"Dense Fog", `68`-`74` as "Bright mist" and `≥242` as "The River Styx";
those are precisely the bands `PLN*` uses and the overworld doesn't. The
disjointness wasn't an anomaly to explain — it was the format working as
designed.

## The discriminator that actually settles it

**Run the candidate bytes through the consuming engine's own classifier or
range table, if one is known.** That is a positive test with a real
denominator, and it is what the disjointness test can never produce.

For the PLN files: 100% of cells fell into named terrain classes with zero
leftovers, across all three files — including the border filler `0xF9`,
which lands in the "≥242 = The River Styx" impassable band, and exactly two
unclassified cells per file, which turned out to sit on the two hardcoded
map coordinates the location resolver tests for that map. A "not this
format" verdict cannot survive a 100%-coverage positive like that, and the
positive took about as long to run as the negative did.

If no classifier is known yet, prefer any other positive-evidence route
(a loader trace, a read-length match, a dimension that factors exactly)
over shipping the disjointness negative as a closure. Record disjointness
as "does not match the *known* instance's value range" — which is true —
rather than "not this format," which is not.

## Also still true

A cross-platform port or later revision can renumber a tileset wholesale,
so only compare against a confirmed table from the *same* build/platform.
And high overlap is corroboration, not proof — see
`cross-stat-correlation-refutes-index-hypothesis.md` for values that stay in
range while still being the wrong kind of field.

Sibling lesson: `struct-analogy-needs-pointer-target-census.md` — same
discipline applied to pointer targets in record structs rather than values
in a flat array.
