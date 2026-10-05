# A "safe" priority-ordered resource-pairing heuristic's low-priority fallback rule can silently mispair a block of near-identical siblings — and the output looks like plausible content, not an error

**When it bites:** a container format documents a multi-rule priority chain
for associating one resource with its partner (a font with its text, a
palette with its image, an index with its payload) — an authoritative rule
(an explicit pointer/chain field, "0 deviation") plus one or more fallback
rules (a region-tag match, then "nearest same-container neighbour") for the
resources the authoritative rule can't resolve — and a batch run over a
large, structurally diverse population produces a MINORITY of outputs that
look suspiciously short, numeric, or otherwise uniform compared to the rest,
tempting the read "this instance just has no real content" rather than "this
instance's pairing fell through to the wrong rule."

Confirmed on Valkyrie Profile (PSX, `valkyrie`): `pairFontsWithText`'s own
doc comment names its `chainStride` rule "authoritative, 1,120/1,140 D1 and
1,015/1,035 D2, 0 deviation" with a same-slot-neighbour fallback for the
rest. Running the project's existing whole-disc extraction pipeline over
156 rooms sharing one player-character sprite bank produced 118 rooms of
completely normal, legible town dialogue and 38 rooms of plausible-looking
short garbage (`"8"`, `"-1"`, `"8O"`, `"0.-"`) — every one of the 38 was a
`Castle of Dipan(past)` room, part of a block of 35 near-byte-identical
dungeon-interior template rooms whose minimal scene scripts confused the
fallback rule into pairing each with the wrong neighbour's font. The output
wasn't a crash or a bounds error — it was low-entropy but individually
plausible byte-index-to-glyph output, exactly the shape "this specific
room just has no interesting dialogue" would also produce. A second,
independent decoder that resolved each room's OWN chained font directly
(bypassing the whole-corpus heuristic search entirely) decoded all 38
cleanly — real generic system-message text ("The item has broken."), not
dialogue at all, confirming the rooms genuinely have no speaker lines but
for a completely different, decode-bug-free reason.

The generalizable shape: a priority-ordered pairing heuristic's SAFETY comes
from the assumption that "nearest neighbour" (or any proximity/adjacency
rule) usually resolves to the right partner because neighbours are usually
distinguishable. That assumption breaks specifically when a *block* of
STRUCTURALLY similar (not just same-type) resources sits together in the
container — a run of template/placeholder/reused-layout entries, which is
common for filler dungeon rooms, padding records, or repeated boilerplate
sections — because the fallback rule can no longer tell which neighbour is
the real partner and picks a plausible-looking wrong one silently. The tell
is a batch of outputs that are uniformly shorter/blander/more uniform than
the surrounding population, not an outright failure.

**Fix:** when a format's own documentation names one pairing rule
"authoritative, 0 deviation" and others as fallbacks, and a population-wide
run shows a suspicious minority looking uniformly degenerate, don't trust
that the fallback kicked in correctly — re-derive that minority directly via
the authoritative rule (e.g. resolve each instance's own explicit
pointer/chain field one at a time) rather than debugging or accepting the
whole-corpus heuristic's output for those cases. This generalizes past text
resources to any format with a documented multi-rule "resolve the associated
resource" heuristic — font/text pairing, palette/image pairing, directory-
entry/payload pairing — wherever a large population can contain a block of
near-identical siblings.
