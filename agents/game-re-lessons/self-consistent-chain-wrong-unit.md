# A running-sum offset/length chain with 0 internal deviations can still have the wrong unit

**When it bites:** a directory/record array's `offset`+`length`-shaped
field pair satisfies `v0[i] == v0[i-1] + v1[i-1]` exactly, across every
record, with zero deviations — before declaring these fields confirmed as
"byte offset into the data" and "byte length," check whether the chain's
*final* value lands where an independently-derived boundary says it should
(a parent record's own declared size, the container's directory offset,
the file size). Internal self-consistency of a running sum is a much
weaker test than it looks: *any* monotonically-summed sequence of numbers
passes it trivially, regardless of what unit those numbers are actually
in (bytes, timer ticks, pixel rows, an unrelated count).

Confirmed on Wings' (Cinemaware, Amiga) `.BOLT` container: the top-level
GROUP-entry chain's `[offset,length)` values are real file byte ranges —
confirmed because the running total lands *exactly* on the directory's own
offset (an independently-known boundary) with 0 deviations across 359
entries in 11 files. The *nested* FRAME-entry chain inside each group
looked identical in shape (same 0-deviation internal self-consistency) and
was initially assumed to be byte offsets within the group's own data too
— but cross-checking its final value against the group's own declared
byte length exposed the assumption as wrong: for groups with many frames
the frame chain's total overshoots the group's declared length by more
than 2x. The chain arithmetic is real (something does walk it that way);
the *unit* isn't bytes-within-this-group. Small groups with 0-2 frames
happened to stay under the group's length by coincidence, which is exactly
the kind of false-confirmation trap a single worked example creates — the
first-tried example (fewest frames) looked clean specifically because it
was too small to expose the mismatch.

**Rule:** every running-sum chain needs its own independent terminal
check, not just internal-deviation-count = 0. If nesting is involved (a
chain inside another chain's element), check *each level's* terminal value
against *that level's own* independently-known boundary — passing the
outer check doesn't imply the inner one is measuring the same thing.

**Sharper variant: a chain can be perfectly self-consistent while every
field in it is read from the wrong byte offset — a constant phase shift,
not just a unit mismatch.** Pool of Radiance's (Amiga, `crawl`) `.dax`
directory format has a leading 2-byte file-level `headerSize` field before
entry 0. An initial guess that skipped this leading field and instead
treated its bytes as part of entry 0's own layout (`[u16][u16 id][u32
offset][u16 compressedLength]`, no separate header) still chained
perfectly: `dataOffset[n+1] == dataOffset[n] + compressedLength[n]` held
with zero deviation across all 843 entries in the corpus, and the running
total even closed near the real file size (landing exactly `fileSize - 2`
short, every single file). That final-value near-miss looked like
corroborating evidence rather than the tell that it actually was. The
model was wrong — every field in every entry was being read 2 bytes off
from its true position — and was only caught by finding a real reference
implementation (`pooldata.py`) and hand-deriving the first two entries'
exact byte offsets against it. **The general trap: a phase-shifted
(constant-offset) misreading of a fixed-stride record array can still
telescope into a self-consistent running sum, because the chain arithmetic
only tests relationships *between* fields within a record, never each
field's absolute position.** A chain closing near — but not exactly at —
an independent boundary (off by a small constant like 2, not by a
percentage) is itself a specific signal worth chasing down as a probable
leading-field/phase-shift bug, not just "close enough, call it confirmed."
