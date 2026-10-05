# A synthetic test input can trip the disassembled function's OWN legitimate guard branch, silently zeroing a subset of outputs and mimicking a decode bug

**When it bites:** feeding fixed/arbitrary synthetic position, origin, or
coordinate values into a real disassembled (or interpreter-executed)
renderer/geometry function as part of a verification script, when that
function has its own real off-screen-clip, bounds-check, or early-return
branch — some test inputs land outside the function's accepted range,
and the function does exactly what it's supposed to: skip writing some of
its output fields while still writing others (e.g. already-computed
position fields survive, colour/UV/opcode fields downstream of the clip
test don't). The partial, structured-but-wrong output looks exactly like a
formula/decode bug rather than what it is — you asked the real function to
render something off-screen, and it correctly declined part of the job.

Confirmed on Valkyrie Profile (PSX): a round-211 verification script for the
field-sprite "general path" `POLY_FT4` submission ran the real overlay code
under a scoped MIPS interpreter with a fixed test origin (`-40, 300`) for
every part. All UV/rgbc/opcode-word outputs read back as 0 while the XY
fields were already correctly written — a pattern that superficially reads
as "the function writes position before it computes colour/texture, and
something's broken in the second half." Tracing the disassembly instead
found a genuine, already-partially-known off-screen clip-reject branch:
once XY is computed, the function tests it against the real 320x224 screen
bounds and returns early, skipping the rgbc/uv/code writes, if the sprite
would be fully off-screen. `(-40, 300)` is off-screen on both axes for a
320x224 framebuffer — the test input, not the function, was wrong.

**The fix:** don't hand-pick one fixed origin for a whole corpus of
differently-sized/positioned records. Compute a per-record on-screen origin
from the record's own known dx/dy (or width/height) so every test input is
guaranteed to land inside the function's accepted range, e.g.
`originXY = [160 - part.dx, 120 - part.dy]` (centre of a 320x224 screen,
adjusted for the part's own offset) — and add a second, deliberately
different origin per record as a cheap positive control that the check
still passes independent of exact placement. More generally: before
concluding a disassembled function's *output* is wrong from a partial-field
mismatch, check whether the function has any conditional branch between
the fields that came out right and the fields that didn't — a legitimate
early return/guard is a far more common explanation than a formula bug
once you've already gotten some real output. See also
`hypothesis-tested-with-mismatched-input-looks-refuted.md` for the sibling
case where a borrowed-from-elsewhere test input (not just an arbitrary
constant) produces the same class of false negative.
