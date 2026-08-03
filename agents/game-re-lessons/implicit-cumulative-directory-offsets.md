# A directory record's offset field can be absent entirely — recomputed cumulatively instead of stored

**When it bites:** a directory/record-array format is confirmed on one
platform (or by other means) to include a per-record file-offset field,
but on a new file/port no byte position for that field parses as a sane
offset (constant, monotonic, in-bounds) under any width/endianness/position
you try — while the record's *other* fields (dimensions, flags, names)
verify cleanly against a known-good oracle.

Test the hypothesis that the offset isn't stored on disk at all: the
reader may reconstruct it at load time by summing each prior record's own
byte length (`offset[i] = headerSize + sum(recordByteLength(j) for j <
i)`), which needs no stored field once the per-record length formula is
known. This is cheap to verify — no brute force required once the length
formula is known from an oracle: check `headerSize + sum(all record
lengths) == real file size` exactly. Confirmed on Wizardry 6's DOS
`mazedata.ega`: the directory record shrank from 6 bytes (Amiga: `u32`
offset + width + height) to 5 bytes (DOS: width + height only, offset
field dropped), verified because `width`/`height` for all 153 records were
byte-identical to the already-solved Amiga file, and the cumulative-sum
formula landed on the real file size with zero deviation on the first try.

**A fast triage step for deciding whether a smaller sibling file is a
narrowed field or real compression:** a same-content file that's smaller
by a **constant byte count equal to (or a clean multiple of) the record
count** — not a percentage — points at one field shrinking or being
dropped per record, not compression (Wizardry 6's `mazedata.ega`: exactly
153 bytes smaller, 153 = the record count, i.e. exactly 1 byte/record
saved). A size reduction that's a **non-constant percentage** across
several sibling files of varying size (Wizardry 6's `.pic` sprites: 51%
to 86% of the original size, no fixed byte or percentage) is the signature
of genuine content-dependent compression instead — decide which triage
branch to pursue (brute-force a narrower record layout vs. hunt for a
compressor) from this shape before investing time in either.
