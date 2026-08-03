# A byte-by-byte terminator scan over variable-length records finds false positives inside well-formed data

**When it bites:** locating where a variable-stride record table ends by
scanning raw bytes for a sentinel/terminator value or pair (e.g. `0x0D 0x0D`,
`0xFF`, a repeated marker byte) — especially once the scan reports a
plausible-looking terminator position but the bytes just past it don't read
as the expected "leftover/unused" filler (they still look like structured
data, or the reported table size seems too small).

A blind linear scan (checking every byte offset, one at a time, for the
sentinel pattern) will happily match the sentinel bytes when they occur
*inside* a legitimate variable-length record's parameter bytes — a record's
own field values are not somehow protected from equaling the sentinel just
because a human wouldn't expect it. The real reader never looks at those
bytes as a candidate terminator at all, because it only checks for the
sentinel at *record-boundary-aligned* positions: it decodes one record,
advances the cursor by exactly that record's own size, and only then checks
the next aligned position for the terminator. A misaligned byte-scan can
therefore report a terminator many slots earlier (or later) than the real
one, either truncating real records or attributing terminator status to
what is actually the middle of live record data.

Confirmed on Phantasie I's dungeon-file action table (`~/Development/nicodemus`,
`docs/phantasie/dungeon-format.md` §3.1): a naive `for byte in file: if
byte==0x0D and next==0x0D: stop` scan starting from the action table's base
address found a `0x0D 0x0D` pair inside two of the ten sample files
(`dng2`, `dng4`) several bytes *before* the position the real
record-respecting walk reached — the bytes just past that false terminator
still decoded as plausible action-opcode records (readable structured
values, not filler), which was the tell that the scan was wrong. Re-running
the walk properly — at each record-aligned slot, decode one action record
(1 or 2 slots depending on its opcode), advance the index by exactly that
record's declared size, and only *then* check the new aligned position for
the terminator — found the true terminator a few slots later in both files,
consistent with all eight other sample files and with the fixed-capacity
formula derived from the table's declared base address and slot count.

The fix generalizes: before trusting *any* terminator/boundary position
found by scanning a variable-stride table's raw bytes, re-derive it by
simulating the reader's own record-walk (decode → read this record's own
size field → advance by exactly that many bytes/slots → check only the new
aligned position) rather than checking every byte offset. If the two scans
disagree, the aligned walk is authoritative — a byte-scan false positive
looks identical to a real terminator until you check whether the bytes
immediately after it are actually well-formed leftover/filler or still look
like live records.

This is a different failure mode from `fixed-stride-record-count-unverified.md`
(which is about a *uniform*-stride table's slot count being wrong because a
different structure starts partway through) and from
`byte-scan-tag-byte-vs-wrong-stride.md` (a recurring byte misread as a tag
because the assumed stride itself is wrong) — here the stride/record format
is already correctly known, and the trap is specifically in how the
*terminator search* is performed against a *variable*-stride table.
