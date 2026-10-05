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

**When two cross-port files are the exact same size and record layout but
fail an md5/byte-identity check, try re-parsing the whole record at the
other platform's endianness before concluding a structural difference** —
the layout and every count can be identical, with per-field endianness the
only thing that changed. Confirmed on Eye of the Beholder II (Amiga,
`crawl` project): `ITEM.DAT`/`ITEMTYPE.DAT` are exactly the same size as
the DOS port's own files (10,385 / 1,026 bytes) but not md5-identical
(unlike this same corpus's `.DEC`/`.DCR`, which really are byte-identical
across platforms). Parsing DOS's already-confirmed 14-byte item record /
16-byte item-type record layout unchanged, but reading every multi-byte
subfield big-endian instead of little-endian, immediately reproduced DOS's
own exact `numItems`/`numNames`/`numTypes` counts (434/123/64) and landed
exactly on EOF with zero residue for both files — decisive confirmation
the whole record layout carried over unchanged and only the byte order
differs. A whole-file leading `u16` count field flipping from nonsense
(`45569`) to the sibling port's own exact value under the other endianness
is a strong, cheap first check before assuming any deeper structural
divergence.
