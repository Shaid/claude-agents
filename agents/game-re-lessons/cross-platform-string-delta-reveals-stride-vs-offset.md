# String-search delta against a known-good sibling offset separates "different start" from "different stride"

**When it bites:** the same game's data file exists on two platforms with
different binary layouts (e.g. 68k vs x86 native ports), one platform's
record offsets/strides are already confirmed, and you need to determine
whether the other platform's equivalent table starts at a different
absolute offset, uses a different per-record stride, or both — with no
symbol table or disassembly available for the second platform's executable.

Cross-platform ports frequently mix **two structurally distinct** kinds of
difference in the very same file, even between tables that are only a few
hundred bytes apart: one table can carry over with the *exact* offset and
stride, differing only in field endianness (native CPU byte order), while
the very next table in the same file is genuinely narrower per record
(dropped padding/reserved bytes) and starts at a different absolute offset
— and a third table can keep the first table's stride/endianness pattern
while still shifting its start offset, because the narrowing of an earlier
table compounds through the rest of the file. Assuming one uniform
transform (e.g. "everything shifts by a constant" or "everything is just
byte-swapped") across all tables in the file will get some of them wrong.

**The technique:** for each table under test, string-search a real,
already-known field value (an entity/location/item name — anything ASCII
and endian-invariant) in the second platform's file. Compute the byte delta
between where it's found and its known offset on the confirmed platform.
Then repeat for the *next* few consecutive real names in the same table and
check whether that delta is **constant**:

- **Constant delta across consecutive records** → same stride, different
  table start offset only (shift the base offset by the delta and stop).
- **Delta that itself changes by a fixed amount each record** → the stride
  itself differs by exactly that per-record change; the new stride is
  `old_stride - delta_increment` (or `+`, depending on sign).

This needs zero disassembly and zero symbol table — only a hex dump and a
handful of known string anchors, confirmed against **at least two**
independent files (e.g. two different episode/level files) to rule out a
per-file coincidence.

Confirmed on Vengeance of Excalibur's DOS VGA port (`episode1.dat`/
`episode2.dat`) against the already-solved Amiga `EPISODE1.DAT`/
`EPISODE2.DAT` offsets (middilgard project): the entity table carried over
byte-identical offset and stride (56 bytes, `0x34`) with only x/y position
fields little-endian (x86) instead of big-endian (68k) — zero mismatches
across all 93 records once read with the right endianness. The location and
item-type tables, only ~0x1000-0x1600 bytes further into the *same file*,
were each exactly 1 byte narrower per record (30→29, 28→27) with a
different absolute start offset, found by exactly the string-delta-vs-
consecutive-records method above: consecutive real location names
(`Alcantara`, `Alcazar`, `Algeciras`, ...) sat a constant 29 bytes apart on
DOS VGA vs. 30 on Amiga — an unchanging delta-of-one-per-record immediately
identifying "narrower stride," not "shifted start." A fourth table (item
placements) kept the exact same stride as the confirmed platform but shifted
its start offset only, and one of its numeric fields turned out **not** to
be endian-swapped at all — confirmed by comparing raw bytes directly
(byte-identical across 78 consecutive real+zero-padding records), not by
assuming the field-endianness pattern found in a sibling table extended to
every table in the file.

**Don't assume a discovered platform-difference pattern (endian flip,
narrower stride, shifted offset) applies uniformly to every table in the
file** — confirm each table independently with its own string-anchor
search, even when it's structurally adjacent to one you've already solved.
