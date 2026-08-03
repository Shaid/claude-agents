# A preceding index/ramp table can make a fixed-position table's start look plausible one record too early

**When it bites:** a fixed-position table (palette, colour table, any
small-record array with no length prefix of its own) decodes to
structurally sane-looking values from a byte-pattern search hit, and the
only evidence for its start offset is "this position decodes to
reasonable-looking data" — not an independently-provable boundary on both
sides.

A byte-pattern search for a table shape (e.g. a run of small nibble/byte
values in a plausible range) can land one record early when the table is
immediately preceded by a sequential index/enumeration ramp (`00 01 02 …
0f`, the kind of table that names/orders another structure). The ramp's
own tail bytes can coincidentally satisfy the target table's per-field
range checks and produce a "valid-looking" leading entry that is actually
still ramp data, not the first real record — shifting every subsequent
field read by one record's width for the rest of the table, and silently
dropping the true final record off the end entirely.

**Confirmed** on Conan the Cimmerian (Amiga, `~/Development/middilgard`): a
32-entry, 4-byte-per-record nibble-colour palette table was read starting
at the first offset that "looked like" a palette (entry 0 decoded to
`0xdef`, a colour that read as a plausible, if odd, background/border
shade). It was actually one record early: the real table starts 4 bytes
later, immediately after a `00 01 02 … 0f` index ramp whose last three
bytes (`0d 0e 0f`) are exactly what decoded as the spurious `0xdef` entry.
Every real table entry was off by one index, and the true final entry was
lost past the table's real end. This survived an early check ("a second,
near-identical table 384 bytes later shares 29/32 entries") because that
check is invariant to a *constant* record-count shift applied to both
tables identically — it does not detect a shared off-by-one, only
disagreement between the two candidates.

**What actually catches it:** prove the block boundary on *both* sides,
independently of what the data inside looks like. On one side: what
immediately precedes the candidate start, and does it look like a
different, identifiable structure (a ramp, a different table, a distinct
byte pattern) rather than more of the same table? On the other side: does
`candidateStart + recordSize * recordCount` land exactly on some
independently-recognisable boundary (a filler run, a different table's
start, a directory entry) with zero slack — not just "run out of file
space eventually." A block that is bounded exactly on both ends this way,
and whose every record then satisfies a domain invariant (here: every
palette's entry 0 being black, `0x000`, only true at the corrected
offset) is far stronger evidence than "the values look plausible" or even
"the values look plausible and stay consistent across a duplicate table."

**A cross-platform or cross-format check strengthens but does not replace
this**, and can itself be shifted by the same bug if applied naively: the
Conan case was independently checked against a same-shaped table in a
different executable/port at a different byte width (4-byte vs 3-byte
records) — genuinely bounding the block on both sides in *that* file too,
rather than just re-finding "the same shift" a second time, is what made
the cross-check decisive rather than merely repeating the mistake twice.
