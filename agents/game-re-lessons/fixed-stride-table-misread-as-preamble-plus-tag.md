# A fixed-stride record table's own marker bytes can look like an unstructured "ascending sequence + padding" preamble on a first read

**When it bites:** a quick byte-level read of an unfamiliar region describes
it as "a short ascending count/index sequence, then a run of padding bytes,
then a tag/magic" (or any similar "preamble, then real content" narrative)
— especially right before or after a magic string that looks like the
region's real start.

A coarse read of raw hex naturally samples bytes in one continuous scan and
groups whatever regularities it notices into an ad-hoc narrative. If the
region is actually a **fixed-stride record array** whose records mostly
contain filler (e.g. `0xFF`) around one or two small live fields — a leading
`u8` index that increments by 1 per record, plus a couple of real values —
that scan can misread the recurring index bytes (which are really spaced one
full record apart) as a short, unrelated "ascending sequence" sitting in
front of the real content, with the intervening filler bytes explained away
as generic padding. The table itself never gets recognized as a table.

Confirmed on Fire Emblem Warriors (2017, `chimera` project): an earlier
pass's byte read of `common/battle/stage/area###.gz`'s `"FTHD"`-tagged
slot-4 payload described it as starting with "a short ascending byte-count
sequence (`01 02 03 ... 09 0a`), then `0x80`-byte padding, then the `FTHD`
tag" — actually backwards and mis-scoped: `FTHD` is the very first four
bytes of the payload, and what looked like an unrelated ascending sequence
was really the `index` field of a 64-byte-stride, 64-record table's first
several records, sampled through a window too narrow to see the stride. The
fix that broke it open was the project's own standard technique (Method
§4's "monotonically-incrementing-by-1 ID" signal): treat any recurring
small-integer byte as a candidate record-boundary marker, search for the
byte *offset* at which consecutive occurrences increment by exactly 1, and
use that gap as the candidate stride — not eyeball the hex dump's first
screen and describe what's visually obvious.

**Fix**: before writing up an unfamiliar region as "preamble + tag" or
"ascending sequence + padding," run the sequential-marker-byte search
(Method §4) over the *whole* region, not just its first 100-200 bytes — a
real fixed-stride table's marker gap is often 40-70+ bytes, well past what
a manual hex-dump skim naturally samples before concluding "no repeating
structure here."
