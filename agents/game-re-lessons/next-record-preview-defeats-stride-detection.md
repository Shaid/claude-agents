# A sequential-id landmark scan can find the *next* record's preview, not its real start

**When it bites:** deriving a fixed-stride record array's size by walking a
sequential id/marker field (e.g. "find where `u16` value N+1 appears after
the position where N was found") and the resulting per-record gaps look
irregular (a handful of different, nearby-but-not-matching stride values)
even though the data otherwise looks like it should be one uniform table.

Confirmed on Warriors of Legend's `restart.dat` character/party table: a
scan for the first occurrence of each sequential character id (`0x07d0`,
`0x07d1`, `0x07d2`, ...) after the previous hit produced gaps of 206, 214,
198, 222, 190 bytes — plausible-looking evidence of variable-length
records. The real record size was a clean, uniform **210 bytes** throughout
all 10 records. The irregularity came from a genuine, confirmed artifact:
the *next* record's id — and for some records, the first 1-2 characters of
its name — is duplicated a few bytes *before* the true record boundary, at
the very tail of the *current* record (most likely a leftover of how this
canned save state was assembled in memory, not a real per-record field).
The naive scan's "first occurrence after the previous hit" landed on this
early preview instead of the record's real header, at an inconsistent
offset that varied with how much padding preceded it.

**The fix:** when a sequential-id/marker scan gives an irregular stride,
check whether the marker value occurs *twice* near each candidate boundary
(once as an early, inconsistently-positioned "preview" and once at a
position that is a clean, constant distance from the *previous* marker's
own second occurrence). Anchor on whichever occurrence produces a uniform
gap to the next record's corresponding occurrence, not on the first
occurrence encountered — a single, simple validation is to compute the
gap between corresponding N-th occurrences (not just any occurrence) across
several records and check it collapses to one constant value. This is a
distinct failure mode from `directory-entry-aliasing.md` (two *directory
entries* sharing one data offset) and from
`fixed-stride-record-count-unverified.md` (a *count* derived from total
size divided by stride, unverified past the first few slots) — here the
stride itself is being *derived* from a landmark scan, and the landmark is
ambiguous because the real marker value appears in two different places
per record boundary, one of them a red herring.
