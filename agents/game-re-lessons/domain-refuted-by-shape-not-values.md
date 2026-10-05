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

## A footer/header value equalling a plausible real-world constant is not proof of that field's role

The same weakness shows up in the opposite direction — building a domain **up**
instead of ruling one **out** — when the "evidence" is a numeric coincidence
rather than a range/count match. A trailing footer value decoding to `320`/
`240`/`224` inside a hypothesized image-format record looks like strong
confirmation of "this is a screen-dimension field," especially when a second,
derived value also matches a real algorithm's expected output (e.g. correct
4:2:0 chroma-subsampling rounding math on top of that dimension). It's still
only a coincidence-of-magnitude until the actual consumer code is traced —
plenty of unrelated fields (camera/projection constants, viewport half-extents,
tile-grid pitches) legitimately hold the same small set of "nice" round
numbers that also happen to be common screen resolutions.

Confirmed on Parasite Eve (PSX): a chunk3 sub-resource's footer decoded to
values matching `320x240`/`320x224` with textbook-correct chroma-subsampling
rounding, matching a community forum's claim that this slot held a background
image (see `romhacking-community-tools-first.md` for when forum/fan claims
*are* trustworthy — this one wasn't, for this specific field). A
`ghidra-disasm` trace of the real consumer showed the record is actually a
camera-position/trigger/tile-scatter 3D scene table; the "dimensions" were
projection/viewport constants that only coincidentally equalled real PS1
screen resolutions. No amount of additional numeric-plausibility checking
(more rounding-formula matches, more corpus-wide consistency) would have
caught this — only tracing what instruction actually reads the field settled
it. Treat a numeric match to a well-known domain constant (screen size, frame
rate, a hardware register width) as an interesting lead worth a code trace,
never as confirmation on its own — the same standard as this file's index/
range-match sections above, applied to values rather than shapes.
