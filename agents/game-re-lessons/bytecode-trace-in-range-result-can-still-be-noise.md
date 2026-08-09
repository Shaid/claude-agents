# A bytecode trace that terminates cleanly with in-range values isn't proof it read real content

**When it bites:** you've written a bounded linear/step-limited trace over a
small per-record bytecode VM (walk bytes from a known entry point, collect
opcode operands, stop at a terminator instruction or a step cap), it reached
a real terminator (not the step cap) with every collected value passing a
type/range check, and you're about to trust the result as decoded — especially
across a *corpus* of sibling records where most, but not all, are expected to
carry real content at that entry point.

Confirmed on War in Middle Earth (Amiga, `middilgard` project)'s per-race
252-byte animation bytecode table. A linear tracer collecting `FRAME` opcode
values from a "death" entry point, stopping at the VM's own `RET`
instruction, passed every structural check available at the single-record
level: it terminated via a real `RET` (not a step-count cap), and every
collected frame index was in-range for that resource's real frame count.
For one race (orcs) this produced `death: [0..13]` — a huge, non-specific
range spanning almost the entire frame count — sourced from wandering
through ~30 bytes of unrelated, mostly-zero-filled table space (a region
with no real per-race script at all for this race) that happened to decode
as valid-looking opcodes before incidentally reaching a `RET` deep in the
row. Nothing about that single trace looked wrong: real terminator, in-range
values, plausible opcode shapes throughout.

**The fix:** the bug was caught only by cross-checking against a *different*
record in the same corpus whose expected output was already pinned by an
independent method — here, a sibling race (troll) whose real visual collapse
frame this same project's pre-existing geometry-based classifier had already
confirmed by rendering (the widest, shortest frame in the resource). Running
the same ungated trace on troll produced `death: [5,6,7]` — ordinary-height,
low-index frames nowhere near the geometry-confirmed real collapse frame — a
direct, checkable contradiction the single-record checks never surfaced.
Once caught, the real fix was cheap and corpus-derived rather than a single
magic threshold: require the trace to show a genuine "this is deliberate,
authored content" signal specific to the opcode family in question (here: a
substantial `DELAY`/hold operand, reached within a short step count) — every
real per-race death script in the corpus shared one exact value for that
signal (`DELAY:30`), while every spurious trace only reached a visibly lower,
incidental value (`22`) via the unrelated bytes it wandered through. **A
per-item validity check (in-range, well-typed, reaches a real terminator) is
necessary but not sufficient** — when a corpus has more than one record and
even one of them already has an independently-confirmed expected value (from
rendering, a different decode path, or any other oracle), cross-check the
new trace against it *before* trusting the rest of the corpus's otherwise-
unverifiable results. See `rle-decode-succeeds-on-garbage.md` for the
sibling lesson about run-length decodes specifically, and
`traced-calling-convention-unverified-against-corpus.md` for the same
"structurally clean but never cross-checked against real values" trap from
the calling-convention-trace side.
