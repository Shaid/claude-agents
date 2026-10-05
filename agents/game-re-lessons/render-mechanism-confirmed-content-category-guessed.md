# Confirming the render/lookup MECHANISM for a text/data table is not confirming what category its CONTENT belongs to

**When it bites:** a doc or claim asserts a semantic category for a table
entry or string ("this is the intro/ending narrative text," "this is a
level name," "this is dialogue for character X") based on the entry's
*position* or *how it's reached* (a confirmed table, a confirmed render
call site, consecutive/sequential indices, being adjacent to other known
content of that category) — while the entry's own decoded content was
never actually read/printed as part of establishing that claim.

Confirmed on Knights of the Round (CPS1, `kolbold`): a session found and
fully traced a real task (`$99fa`) that calls a confirmed scroll1-text-
render routine with two consecutive string-table indices, and — correctly
having confirmed the *mechanism* (real task, real call sites, real table,
matching format) — wrote it up as "the real narrative-text renderer...
real, consecutive story pages," reusing the "consecutive indices" pattern
that *had* held for a sibling, already-content-verified table (the
self-test menu text, which really was one long ordered sequence). A later
session actually decoded those two specific strings and found completely
different real content: a multiplayer character-select tie-break message
("Two/Three players have chosen the same character... The Lady of the
Lake will decide."), not narrative text at all. The render mechanism was
never wrong — the category label attached to it was inferred from context
(this task looked intro/ending-adjacent, other similar tables were
sequential prose) rather than from the text itself.

**The general check:** a confirmed table format + a confirmed real call
site proves the *mechanism* renders real, in-bounds content — it does not
by itself establish *what kind* of content a specific entry holds.
"Consecutive indices" and "reached from a plausibly-named task/state"
are contextual signals, not content verification, and they generalize
badly: a sibling table using the identical mechanism can hold a
completely different content category (UI dialogue vs. narrative
prose, a stat block vs. a name list, an item description vs. a monster
name) with no structural difference visible from the outside. Before
writing a categorical semantic claim about specific table entries,
actually decode and read those entries' content — the same discipline
`plausible-render-not-semantic-label.md` requires for *which pixel frame
plays under which named state*, applied here to *which textual/semantic
category a decoded string belongs to*. When the correction surfaces,
it's a pure labelling fix (the mechanism/format/offsets stay exactly as
confirmed) — write it as a `> **Correction:**` block in place, not a
silent edit.
