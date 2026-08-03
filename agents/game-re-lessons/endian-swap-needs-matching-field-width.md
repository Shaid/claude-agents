# Cross-platform endian conversion needs per-field width, not a blind byte-pair swap

**When it bites:** a sibling platform port ships a same-sized file as an
already-solved platform, and you're about to byte-compare the two under a
single global hypothesis (raw identity, or a blind adjacent-byte-pair swap)
to decide whether the format carried over unchanged.

A pairwise 16-bit byte swap (`b0,b1,b2,b3 -> b1,b0,b3,b2`) correctly
converts a run of `u16` fields between big- and little-endian, but is
**silently wrong for `u32` fields** — a real `u32` needs a full 4-byte
reversal (`b0,b1,b2,b3 -> b3,b2,b1,b0`), which a pairwise swap does not
produce (it yields a value that is neither the original BE nor the correct
LE reading). Test each field at its own declared width and the *other*
platform's endianness, not one blind transform applied uniformly to the
whole file.

**A whole-file raw (unswapped) match percentage is also misleading in the
other direction**, because ASCII text fields are endian-invariant — a file
that's mostly names/strings with a few numeric fields scores deceptively
high under plain raw comparison even when every numeric field in it is
still wrong, and scores deceptively *low* under a blind swap (which breaks
adjacent text bytes that didn't need touching). Isolate all-numeric
subregions first — a small header of pure counts/offsets/sizes, no text at
all — and check *that* region alone at correct field width/endianness
before drawing conclusions from a whole-file percentage. Confirmed on
Wizardry 6's DOS/Amiga ports: `master.hdr` (20 `u16` values, no text) and
`disk.hdr`'s 44-byte leading header (9 `u32` offsets, no text) both hit
**100% exact-value match** once read at their real field width in the
other platform's endianness — proof the two ports share byte-identical
underlying tables, not just "a similar format" — while the same files'
whole-file raw/swap percentages (looking at the mixed regions too) were
far less conclusive on their own.
