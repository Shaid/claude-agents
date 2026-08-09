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
