# A "self-relative offset" field's exact additive constant lives in the reference's arithmetic, not its prose/struct notes

**When it bites:** a format uses a "self-relative offset" convention (a
`rel_offset_X` field's target address is computed relative to the byte
position of the `rel_offset_X` field itself, not the struct/buffer start),
you have a real reference implementation (community tool source, a leaked
SDK, a fan disassembly writeup) documenting the struct layout in a header
file or plain-text research notes, and a first attempt at applying it to
real data produces plausible-but-wrong output — most diagnostically,
strings that are **truncated from the front** (missing their first few
characters) rather than garbage or a crash.

Plain-text/struct-only documentation of this convention ("rel_offset is
from the start of that field") states the *rule* but not the *per-field
additive constant* needed to apply it — that constant depends on exactly
where the offset field sits within its containing record (e.g. "the 2nd
u32 field, so +4" vs. "the 4th u32 field, so +0xC"), and differs per field
even within one format family. It's easy to derive that constant by
inference from the struct layout alone and get it subtly wrong — in
particular, double-counting the "skip past earlier fields to reach this
one" step that the reference's own compiled arithmetic already folds into
its named constant, producing a name/data offset that's a few bytes too
far into the buffer.

Confirmed on NieR Replicant ver.1.22474487139 (PC, `flower` project): a
community reference tool's `PACK`/`tpArchiveFileParam` struct layout and
`research/*.txt` prose notes ("rel_offset is from the start of that
field") were applied by hand, producing archive names like `"1.arc"` and
`"on.arc"` instead of `"lang1.arc"` and `"common.arc"` — silently
plausible-looking (still valid-looking short ASCII strings, still
null-terminated) rather than obviously broken. The bug was adding a
`FILE_NAME_OFFSET`/`ARC_PARAM_OFFSET`-style constant *and* a separately
hand-derived "skip the id/count field" `+4`, double-counting the same
correction the reference's own constant already encoded. Fixed by reading
the reference's actual `.cpp` pointer arithmetic
(`offset + sizeof(Record)*i + param.rel_offset_name + FIELD_OFFSET`) line
by line rather than re-deriving it from the `.hpp` struct declaration or
the plain-text research notes, which state the convention but not this
exact formula.

**Fix:** when a reference implementation ships both a struct-only header
(or prose notes) *and* real source implementing the parse, always read the
`.cpp`/parsing function's literal offset arithmetic before hand-applying
the convention — don't stop at the struct layout. If the output looks
plausible but subtly wrong (truncated strings, off-by-a-few-bytes data),
suspect a double-counted or missing per-field additive constant before
suspecting the wrong offset field or a wrong base entirely.
