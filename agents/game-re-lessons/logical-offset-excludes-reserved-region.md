# A directory table's offsets can be logical, excluding a reserved host-filesystem region

**When it bites:** most entries in a directory/chunk table decode
byte-exact by walking it naively, but a systematic-looking minority don't —
and the failures cluster at or after a known reserved structure's file
location (a boot sector, a root/bitmap block, a partition table).

A custom trackloaded container layered under a cosmetic-but-real AmigaDOS
root+bitmap block (placed mid-disk purely so the volume shows a name, and
so the all-zero bitmap block stops the OS ever allocating over the game
data) computed its directory offsets as if that 1024-byte reserved region
didn't exist. Naive table-walking decoded 35 of 49 chunks byte-exact; the
other 14 — every one at or past the reserved region's file position —
showed an unexplained ~1024-byte high-entropy "prefix" before a second,
genuine compressor-magic header whose own declared length field exactly
matched the outer table's declared value for that same entry (too precise
to be coincidence, but the prefix bytes themselves were pure noise, not a
parseable sub-structure). Two hand-driven hypotheses — a nested
sub-directory table, and a second headerless compressed stream sharing
state with the first — were tried and failed before the real mechanism
(logical vs. physical offset) was found.

The fix, once found: excise the reserved bytes from the raw file once, up
front (a `repairDisk()`-style transform), after which every directory
offset becomes a correct 1:1 physical offset with no further
special-casing. This took the corpus from 35/49 to 49/49 chunks decoding
byte-exact, zero deviation (Desert Strike Amiga, `~/Development/strike`).

Generalizes beyond Amiga/AmigaDOS: any custom container riding on top of a
real-but-decorative host filesystem structure (a boot sector, an ISO
volume descriptor, a partition table, a save-slot header) is a candidate
whenever most chunks decode, a systematic minority don't, and the failures
correlate with file position rather than any per-entry property. Check
whether the reserved structure's file offset and length line up with where
the naive-vs-real decode divergence starts before chasing a per-chunk
theory.
