# A fixed-stride byte-window scan for absolute-address literals produces false positives at instruction boundaries

**When it bites:** hunting for which code references a known address range
by sliding a 4-byte (or N-byte) window across a binary at every 2-byte (or
byte) offset and checking whether the resulting big-endian value falls in
the target range — especially right before treating a batch of "hits" as
evidence of a table's real consumers, or before that batch's *count* (e.g.
"205 hits") is quoted as a finding.

A raw byte-window scan has no concept of instruction boundaries. A 4-byte
window can span the tail of one real instruction and the head of the
unrelated next one, and the two halves can coincidentally concatenate into
a value that looks exactly like a valid absolute-long operand. On 68000
code this is common: a `move.w d0,0x6(a1)` immediately followed by a short
branch (`bra.b`) produces trailing bytes like `...0006 6064...`, which a
naive scan reads as the literal address `$00066064` — a value that never
appears as an operand anywhere in the actual instruction stream.

Confirmed on Deuteros (Amiga, `methanoid` project): a byte-window scan for
literal references to a suspected record-data range (`$66000`-`$6F392`)
found 205 "hits" in one file and 20 in another. Re-deriving the same census
from a real disassembly listing (r2 `pd`, filtering matches carrying the
`.l` absolute-long-addressing operand suffix) and independently
re-verifying with a second disassembler (Python capstone) found **exactly
one** genuine hit across the same files — every other "hit" was an artifact
of instruction-boundary misalignment, confirmed by checking that no
consistent single alignment (from either disassembler) decoded a valid
instruction containing the value at any of the coincidental offsets.

**r2's `aac` (auto-analyze-calls) recursive function-following is not
immune to the same class of error.** It can auto-detect bogus "functions"
starting *inside* a data region if the region's raw bytes happen to decode
as a plausible-looking call/branch chain — confirmed in the same session,
where several `aac`-found "functions" (e.g. `fcn.00068636`) landed squarely
inside the already-known record-data byte range and decoded literal ASCII
text bytes as nonsense opcodes. A function list produced by recursive
call-following still needs the same false-positive scrutiny as a plain
linear disassembly — it is a better starting point, not a guarantee.

**Fix:** never trust a raw byte-window address census on its own. Derive
candidate address references only from a real disassembly (linear `pd` or
function-based `pdf`/`aac`), filtering for the disassembler's own
absolute-addressing operand marker (r2's `.l` suffix; capstone's operand
string), and treat any resulting hit count in the single digits as
plausible, double-digit-or-higher counts as suspect until spot-checked. For
a definitive answer, re-verify every candidate hit with a second,
independent disassembler at the same address, requiring both to agree the
value is a genuine operand of a real instruction — not just present
somewhere in the byte stream.
