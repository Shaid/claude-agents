# A "ruled out" domain conclusion can be wrong even when every traced byte fact is right

**When it bites:** disassembly has correctly traced an allocator, an
access-pattern (e.g. "select one record by index, copy it into a scratch
buffer"), and a few field offsets with genuine rigor, and the resulting
write-up "rules out" a candidate domain (e.g. "this is per-class UI data, not
the per-level data you were looking for") — especially when the eliminating
evidence is that an index variable's *range* (e.g. `0..13`) matches one
plausible domain, not that its *observed values* are inconsistent with the
domain you're trying to rule in.

A record-count or index-range match (`0..13` for "14 classes") is weak
evidence for *which* domain a section belongs to if a second, equally
plausible domain shares the same count (here: "14 maze levels"). An
access-pattern match ("select-one, copy-to-scratch, work-with-it") is
similarly weak on its own — both a character-selection screen and a
level-loader look identical at this shape, because both are "index picks one
of N cached records" mechanisms. Neither is a *value*-content oracle: they
never actually check what the selector variable's real observed values are
(does it ever get set to 14 or higher outside the loop bound? does it get
written from user-menu-selection code, or from level-transition/warp code?).

Confirmed on Wizardry 6 (Amiga): a session correctly traced a 14-iteration
allocator, a `CopyMem`-into-scratch-buffer selection pattern keyed by a
global `-0x47a4(a4)`, and two specific field offsets (a screen-position pair,
a bitmask), and concluded `scenario.dbs`'s section was "per-class UI data for
a character-creation screen" — explicitly ruling out it being the per-level
dungeon maze geometry a separate task was hunting for. Every one of those
byte-level facts was correct. The *domain* was wrong: `-0x47a4(a4)` is the
**current maze level index**, not a "selected class slot" — provable only by
finding where it's actually *written* (a `SetLevel` function, and two
scripted level-transition sites hard-setting literal level numbers, neither
of which a UI class-picker would ever do). The section really was the maze
geometry, discovered by a later `re-codebreaker` pass and independently
re-verified byte-exact (region-overlap invariant, cross-platform DOS-vs-Amiga
byte match, a second file's byte match, rendered maps).

**Fix:** before writing "domain X ruled out, this is domain Y" on the
strength of a count/range/access-pattern match, find at least one place the
disambiguating index variable is **written**, not just read/indexed with —
the write sites (what triggers a change, what values get stored, under what
UI/game-state context) are where two same-shaped domains actually diverge.
A "domain refuted" claim rests on the same load-bearing-negative standard as
`negative-from-addressing-root-not-shapes.md`: shape/pattern matches are weak,
enumerating every write site to the disambiguating variable is strong. Treat
a domain conclusion resting only on an ambiguous-range index as a hypothesis,
not a ruling-out, until you've checked its writers.
