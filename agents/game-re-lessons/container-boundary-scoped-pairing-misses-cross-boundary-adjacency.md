# Pair physically-adjacent build artifacts by raw byte adjacency, not by a higher-level container's boundaries

**When it bites:** two sub-resources are related because a game's own build
tool bundled them physically next to each other on disk/disc (a font +
its text, an index + its payload, a header + its data blob), and your
pairing/grouping logic scopes the search to some *other*, already-confirmed
container layer in the same format (a TOC slot's extent, a directory
entry's declared range, a chunk boundary) — especially when that container
layer was reverse-engineered independently and has no documented
relationship to the build tool's own bundling behavior.

Valkyrie Profile (PSX) ships each dialogue/script text resource with its own
subset font, and the two are always immediate byte-adjacent SLZ blocks on
disc (font right before or right after its text, in raw scan order). A first
implementation grouped candidate blocks by which already-confirmed TOC
"slot" extent contained them (a completely different, already-solved
addressing layer in this same container format) before pairing within each
group — and found **zero** real font+text pairs, not a degraded result, a
hard zero, even though every individual block was already decoding
correctly. Switching to pure whole-file byte-offset adjacency — sort every
decoded block by its raw file offset, then for each font block check only
its immediate previous/next neighbor in that flat list, ignoring which TOC
slot either one falls in — found 1,139/1,140 real pairs instantly. The two
boundaries (TOC slot extents vs. build-tool bundling adjacency) simply have
no necessary relationship: a real font+text pair can straddle a TOC slot
edge, and TOC slot membership tells you nothing about which block a build
tool placed next to which.

Before writing a "pair by proximity" algorithm, pair in the **flattest,
lowest-level addressing space you have** (raw file/disc byte offset) first,
and only add a higher-level container's boundary as a *filter* after
confirming it doesn't silently exclude real matches — a hard-zero result
from a plausible-looking pairing algorithm is a strong signal the grouping
boundary itself is wrong, not that the data doesn't pair at all.
