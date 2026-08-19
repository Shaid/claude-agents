# A cleanly-decomposable data byte may index no table at all — and a sibling game's role for the same-shaped byte doesn't transfer

**When it bites:** a map/tile/entity byte decomposes suspiciously cleanly
(tens digit looks like a type, ones digit like a variant; or a constant
offset splits the value space in two), and you're about to (a) hunt for the
terrain/property/graphics table it must index, or (b) import the role that
same-shaped byte was already confirmed to have in a sibling game.

Both moves are reasonable hypotheses and both can be flatly wrong.

**(a) The table may not exist.** A retro engine can consume a decomposed
byte entirely through branch chains, with no array anywhere. Confirmed on
Phantasie I (Amiga, `nicodemus` project): the overworld tile byte splits via
a literal `divs.w #10` into two globals, and *every* consumer is a compare
chain — movement cost is `(class + 1) * 75` for classes 0-3 and `60`
otherwise; the random-encounter group is `variant * 12 + r`; passability,
town prompt and event dispatch are individual `cmpi` tests on specific
values. An exhaustive search of the two hunks owning the subsystem found **no
lookup keyed on the raw byte or on either half**. Time spent looking for the
"terrain properties table" would have been spent looking for something that
was never written. Check for the *consumer* (find where the split halves are
stored, then who reads those globals) before assuming the table exists.

**(b) Same series, same byte shape, different role.** Phantasie III's `.set`
world map, already confirmed in the same project, encodes its map byte as **a
rendering index** — an X pixel-column into a bundled terrain-band picture, so
terrain art falls out of the byte directly. Phantasie I's byte, same series,
same conceptual asset, similar-looking `class*10 + variant` shape, is **pure
simulation state**: it is never drawn at all. The visible map comes from a
completely separate per-section display list plotting icons from a bitmap
bank in the executable. A cross-game analogy on byte shape alone would have
sent the whole render pipeline down the wrong path. (Compare
`sibling-format-encoding-paradigm-not-transitive.md`, which is the same
caution one level down: between two formats inside a single engine.)

**(c) A perfect statistical correlation can coexist with a completely
different causal mechanism — the byte may be the *marker art*, not the
lookup key.** Phantasie III's overworld map array contains 30 cells whose
values (`25`-`52`, `54`) are distinctive against the bulk terrain, and there
are exactly 30 named towns/dungeons/inns. The bijection is real and
verifies perfectly: each value's occurrence count in the 3,750-cell array
equals its number of named locations, including one value that legitimately
occurs *twice* because two inns share a graphic. It is very hard to look at
that and not conclude the engine reads the cell value to know what's there.
It doesn't. `LocateSpecial()` identifies every named place by a chain of ~34
hardcoded `(x, y)` comparisons compiled inline, and **never touches the map
array at all** — a byte search for the active-map pointer across the whole
routine returns zero hits. The distinctive values are just the tile artwork
the level designer placed at those coordinates, so of course they correlate
one-for-one. The check that separates the two readings is cheap and should
be run before writing the mechanism down: **find where the fetched byte
goes.** Here it goes exactly two places — verbatim into the tile blitter,
and into a terrain-class range chain whose bands (`2`-`25`, `61`-`67`,
`68`-`74`, `≥242`, …) contain exactly one immediate anywhere near the
"marker" range, and that one is a band *boundary*, not a marker test. A
correlation this clean means the values are *diagnostic*, which is genuinely
useful for extraction — you can place location pins from them — but
diagnostic is not causal, and the docs must say which one you proved.

**A per-file all-or-nothing constant offset is game state, not a graphics
bank.** The same investigation found tile codes splitting at exactly 120:
two of eighteen section files used codes 0-119 for **520/520** of their
cells, the other sixteen used 120-239 for **520/520** of theirs, never
mixed — and at every seam where the two populations met, the neighbouring
cell's code was *exactly* `+120`. That was written up as an unexplained
per-section "code bank," reaching for a rendering explanation. It is a
**fog-of-war flag**: the reveal routine does `cmpi.l #120` / `subi.l #120` /
write the byte back, and the engine saves the data file on every section
exit, so the flag is live save state stored in the shipped asset. The
structural signature to recognise — a perfectly clean, never-mixed,
all-or-nothing split at a round constant, correlated with *which file* rather
than with position inside a file — points at persisted state (explored,
visited, unlocked, defeated) far more often than at a graphics variant,
because a graphics bank would have no reason to respect file boundaries that
exactly.
