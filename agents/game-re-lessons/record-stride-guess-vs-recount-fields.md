# When no candidate stride divides a table evenly, recount the reader's fields — don't guess more strides

**When it bites:** a format doc reports trying a list of candidate
record-stride sizes against a table whose element *count* is already
known unambiguously (a header field, or a cross-file structural
invariant), and says "none of them divide the remaining bytes evenly" —
especially when the candidates are all round/typical numbers (8, 10, 12,
15, 16, 20, 24, 25, 30...).

The instinct in this situation is to keep widening the search — try more
candidate sizes, look for a second embedded sub-table, suspect padding.
But when a reference reader function for the exact format is available
(disassembly, an emulator source port, or any reimplementation), the much
higher-probability cause is a **hand-counting error**: someone counted the
struct's fields by eye from a list of read calls and miscounted by exactly
one field-width somewhere — mistaking a struct with N single-byte fields
plus M two-byte fields for a slightly different N/M split. The fix is not
to try more candidate strides; it's to recount the reader's fields
literally, one `read*()` call at a time, and sum their exact byte widths.

Confirmed twice in one pass on EOB1/EOB2's `ITEM.DAT`/`ITEMTYPE.DAT`
(`crawl` project, Kyra engine, source: `engine/items_eob.cpp`). A prior
pass's doc recorded "attempted record strides 8, 10, 12, 15, 16, 20, 24,
25, 30 bytes — none divides the file size evenly" and left the format
open. `EoBItem`'s reader has 11 fields
(`nameUnid, nameId, flags, icon, type, pos` — six 1-byte fields — plus
`block, next, prev` — three 2-byte fields — plus `level, value` — two more
1-byte fields); a natural miscount lands on 15 bytes (rounding the mixed
field list up), but counting byte-by-byte from the actual read calls gives
**14** — a stride nobody in the "recognisable round number" candidate list
had tried. `EoBItemType`'s reader similarly recounts to **16** bytes, not
15. Both, once used, closed the file's declared byte count with the
header's own independently-read entry count to **zero residue** (`2 +
numItems*14 + 2 + numNames*35 == fileSize` exactly; `2 + numTypes*16 ==
fileSize` exactly) and every decoded record decoded into fully legible,
game-correct content (item/type names).

The general move: when a table's element count comes from its own
unambiguous header field (not a guess) and no candidate stride closes the
size equation, and a reference reader exists, stop widening the stride
search and instead sum the reader's field widths by hand, one declared
read call at a time — treat "the candidate list was wrong" as the default
explanation before "the format needs a second hidden region" or "the
count field is unreliable."
