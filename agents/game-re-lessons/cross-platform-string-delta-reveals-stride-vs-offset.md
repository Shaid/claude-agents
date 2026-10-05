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

**Second confirmed instance — same technique, but across two REVISIONS of
the same platform's file, where the whole growth had been modelled as one
inserted block.** Fire Emblem: Three Houses (Switch, `chimera`): save-slot
files grew from 152,588 to 154,412 bytes (+1,824) between the header
`version`-13 and `version`-23 formats. A prior pass modelled the delta as a
single inserted block (`Items[] + 456 records x 4 bytes = 1,824`, an exact
but meaningless factorization) and tested the known 60-slot `Character[]`
roster array at `base + 1824 + i*oldStride` — garbage — then fell back to a
whole-file brute-force signature scan (thousands of zero-dominated false
positives) and a "location not found" write-up. The truth: **1,680 of the
1,824 bytes were inside the array** — every one of the 60 records gained 28
bytes because two per-class arrays widened 90 -> 100 entries, tracking the
update's `ClassData` table growing 90 -> 100 rows — plus 144 elsewhere. The
array base and the id field's in-record offset were unchanged, so
`base + i*newStride + 0x24` decodes cleanly on 12/12 real saves. A
whole-array shift can never coincide with a stride change for any `i > 0`,
so the negative was guaranteed regardless of where the array actually was.

Four cheap tests that find this in minutes, in the order to run them:
1. **Factor the delta against every known array count first**: for each
   array of `N` records, check whether `(Δ - r) / N` is a small integer for
   a small remainder `r` (`1824 = 60 x 28 + 144`) — a per-record growth
   hypothesis with a clean remainder beats any single-block factorization
   with none.
2. **Anchor landmarks OUTSIDE the suspect array** to bound where the growth
   lives before touching the array: a player-name string, a self-describing
   block-size field (whose value being *unchanged* proves that block didn't
   grow), an array of sentinel-filled records — each gives a "+1,680 here,
   +1,824 there" reading that localizes the growth for free.
3. **Window-match delta map** (32-byte exact windows, old file -> new file):
   record `i`'s fields shift by `i x 28` (+56, +84, ...) and the identical
   empty-record templates recur at the *new* stride — the string-delta
   trick above, with any repeated byte window standing in for a name.
4. **Align the old vs new EMPTY-record template** (`difflib` on the two
   sentinel-filled templates, noise-free since every empty slot is
   byte-identical) to see exactly where inside the record the bytes were
   inserted (here: 20 zero bytes before the old exp-array end, 8 appended).

See `docs/fe-threehouses.md` § "Roster/recruitment membership — SOLVED for
the current format" (2026-09-02) for the worked numbers.
