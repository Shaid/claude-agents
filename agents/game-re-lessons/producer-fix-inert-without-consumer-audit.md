# Fixing a decoded field's producer is silently inert if a downstream consumer never got wired to it

**When it bites:** a data-file-first pipeline has more than one place that
consumes the same decoded/composed field (an offline export step, an
in-browser viewer tool, and the game engine's own runtime all reading
"the same" table) and you've just fixed that field's producer — before
declaring the fix complete, check every consumer, not just the one you were
staring at when you found the bug.

The seer architecture (and similar data-file-first pipelines) routinely grows
two or three independent code paths that each compute or consume "the
composited scene/table/asset" for a different purpose: a tile-preview viewer,
an arbitrary-position generator, and a precomputed-per-named-entity cache.
These paths are easy to write once, each correctly reading the same
now-fixed producer field — and easy to leave silently un-migrated when a
sibling path was written earlier against a stale or wrong field, because
nothing errors: the stale path just keeps rendering the old (wrong or
incomplete) data, with no exception, no lint failure, no visibly broken
build.

Confirmed in `middilgard` (WIME, Amiga): after reimplementing
`SynthSceneObjects` and fixing `generateSceneObjects()` to call it correctly,
the fully-accurate merged object list (`sceneObjects`) was already being
computed and exposed on every named location's exported data — but the
in-game engine's own tile-click preview panel (`Game.ts`) had **never been
wired to read it**, instead still building its compositor input from an
older, separate `layerBlocks`/`synthObjects` pair that predated the accurate
field's existence. The producer-side bug was completely fixed; one of three
consumers kept rendering as if it wasn't, because nobody had audited whether
every consumer of "the scene composition data" actually pointed at the
now-correct field versus an adjacent, older one with a similar name.

**Fix:** after confirming a producer-side decode/table fix, grep the whole
project (not just `src/`, also `tools/`) for every reader of that data
structure's *type* (not just its name — related fields commonly share a
type shape, e.g. `SceneObject[]` reused across three different named fields)
and check each one is pointed at the corrected field, not a sibling that
predates the fix. A compositor or renderer that already prefers the accurate
field "when present" (a common defensive pattern) is not evidence every
caller actually populates that field — check the call site, not just the
consumer's fallback logic.
