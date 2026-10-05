# A boundary/terminator scan must step at the real element's own granularity, not one byte at a time

**When it bites:** locating where a variable-stride record table ends by
scanning raw bytes for a sentinel/terminator value or pair (e.g. `0x0D 0x0D`,
`0xFF`, a repeated marker byte) — especially once the scan reports a
plausible-looking terminator position but the bytes just past it don't read
as the expected "leftover/unused" filler (they still look like structured
data, or the reported table size seems too small). Also bites the sibling
case: auto-detecting a *fixed-stride* directory/table's own length by
scanning forward for the first recognized tag/magic pattern one byte at a
time, when the table's real element width is 2 or 4 bytes — the scan can
match a multi-byte tag pattern that straddles two adjacent aligned slots,
finding a "hit" that isn't a real element at all.

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

**Second confirmed instance (fixed-stride table, not variable-stride
records):** Parasite Eve II's (PSX, `parasite`) `hONE` SndScript program
format has a leading directory whose own length isn't given by any header
field — it has to be auto-detected by scanning forward from a fixed base
for the first offset that looks like a recognized 4-byte ASCII tag
(`'oneV'`, `'Wait'`, `'Loop'`, …). The directory's own entries are 2 bytes
wide, so the real element granularity is word-aligned. A first version of
this scan advanced the candidate offset by 1 byte per step instead of 2;
on one real file (`stage1/folder501/file(id0)@0x945800/chunk0`) this let a
4-byte tag pattern straddle two adjacent word-slots and match at a
byte-misaligned position, producing a directory-length value wildly out of
bounds for the actual 740-byte program (harmlessly caught by a downstream
bounds check in this case, but a real, silent generalizable bug — a luckier
byte pattern would have produced an in-bounds-but-wrong length with no
crash at all). Fix: step the scan by the table's own real element width (2
bytes here), matching the variable-stride case's underlying principle —
*scan granularity must equal real element granularity, or a boundary
pattern can be found straddling two legitimate elements instead of at a
real element start.*

This is a different failure mode from `fixed-stride-record-count-unverified.md`
(which is about a *uniform*-stride table's slot count being wrong because a
different structure starts partway through) and from
`byte-scan-tag-byte-vs-wrong-stride.md` (a recurring byte misread as a tag
because the assumed stride itself is wrong) — here the stride/record format
is already correctly known, and the trap is specifically in how the
*terminator search* is performed against a *variable*-stride table.
