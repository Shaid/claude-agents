# A "scan every entry for magic X" loop can OOM when the reader must decompress before it can even check the magic

**When it bites:** Writing a scan over a heterogeneous, compressed-at-rest
container archive (a DATA0/DATA1-style directory + blob pair, a KT_GZ/zlib
member archive, any format with no uncompressed type tag in its directory)
to find an entry with a specific magic/type — e.g. "find a `.bai` spawn
table among 1,000+ mixed model/texture/audio/data entries" — especially
when the loop only pre-filters by a cheap field like `decompressedSize`
before calling the actual (decompressing) reader.

## What went wrong

A test needed to find *any* real small data entry (a `.bai` file, ~13 KB
decompressed) inside a small-but-heterogeneous 1,060-entry DLC archive that
also holds large model/texture/audio entries. The first draft looped over
every entry in directory order, calling the project's `readDATAEntry`-style
reader (which fully decompresses an entry's payload before returning it)
on each one to check its magic bytes, with only a loose
`decompressedSize < some-bound` pre-filter. This crashed the whole worker
with a V8 "JavaScript heap out of memory" fatal error partway through the
scan — before it ever reached the entries the earlier, narrower
`decompressedSize` guard would have caught, because the pre-filter itself
was too loose (or, in a second variant, absent while iterating a range
that happened to contain a few genuinely huge entries).

The root cause: for a format with no separate lightweight "peek the type"
path, *any* magic/type check requires the full decompression cost of
whatever entry is being checked, however small the final answer turns out
to be. An "for each entry: decompress, check magic, continue" loop pays
the full decompression cost of every non-matching entry along the way —
including any multi-hundred-MB assets that happen to sit in the scanned
range — even though the loop only cares about tiny entries.

## Fix

1. **Set a hard `decompressedSize` ceiling** before calling the
   decompressing reader at all (e.g. skip anything over 1 MB when hunting
   for a table you know is a few KB) — cheap, since size is usually a
   directory-level field read without touching the compressed payload.
2. **Prefer a known or derivable index/offset range over a full linear
   scan** whenever one exists. If an earlier investigation (a scratch
   script, a prior session's notes, an already-documented binding formula)
   already narrowed down roughly where entries of the wanted kind live,
   scan that window specifically rather than the whole directory — this is
   usually both correct (matches already-established ground truth) and
   removes essentially all of the OOM/perf risk in one move, since the
   window excludes the large unrelated assets entirely.
3. Treat "decompress-before-inspect" as a first-class cost model for any
   corpus census over this kind of format — the same caution that applies
   to a slow-per-item batch operation (see
   `batched-resume-reprobe-cost-linear-in-corpus-size.md`) applies doubly
   here, since the cost isn't just wall-clock time but can be a hard
   memory ceiling with no partial-progress recovery.
