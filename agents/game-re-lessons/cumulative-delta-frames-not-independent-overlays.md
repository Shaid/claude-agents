# A multi-frame sparse delta/patch stream may apply cumulatively, not as independent overlays on one pristine base

**When it bites:** a resource clearly isn't a raw bitmap (its size doesn't
fit any consistent width/stride at any bit depth) but its bytes resolve
cleanly into a stream of small records — a destination offset, a count, and
a payload — that patch sparse spans of a same-sized buffer belonging to an
already-decoded base image. Once the record grammar is confirmed (zero
parse errors, consumes the whole file with zero slack), the natural next
step is applying each frame's records fresh onto a copy of the pristine
base and rendering — and early frames look perfect while later ones show
visible corruption (border/edge artifacts, garbled regions) that grows
frame over frame.

Confirmed on Powermonger (Amiga)'s `END.PAK`: a 7-frame "crown descends
onto the emperor's head" ending animation, each frame a stream of
`{dest: u16 (4-byte aligned, 0xFFFF = terminator), count-1: u16, count
longwords of payload}` records patching a copy of `END_PIC1`'s screen
buffer. Decoding each frame as an independent overlay on the untouched base
image visibly corrupted the crown and border in frames 4–6. The real
in-game player loop, once traced, does something the data alone doesn't
reveal: it copies the *previously displayed* (already-patched) buffer
forward into the new working buffer **before** applying the next frame's
records, and never reloads/rewinds anything back to the pristine base. The
frames are therefore cumulative deltas on top of each other, not
independent diffs against one shared original — later frames only specify
what changes *since the last frame*, not the union of every accumulated
change from frame 0.

**The fix:** for any sparse delta/patch-record animation format, don't
assume independent-overlay semantics just because each frame's records
parse cleanly against a byte-exact structural invariant (zero slack, zero
alignment violations) — that invariant only proves the record *grammar* is
right, it says nothing about *composition* order across frames. Render
frame N by patching a copy of frame N−1's own rendered result (starting
from the base for frame 0), and compare against an independent-overlay
render of the same data: if cumulative renders clean while independent
shows growing corruption in later frames, that's strong confirmation for
cumulative semantics. Where available, the authoritative source is the
player/consumer code itself — specifically, whether it reloads/resets the
working buffer to the pristine base before each frame, or copies the
previous frame's buffer forward and never rewinds. This generalizes beyond
animation: any format describable as "a stream of small structurally-valid
records, applied to a shared mutable buffer across multiple passes" has the
same open question (composition order) that a clean per-record parse alone
cannot answer.
