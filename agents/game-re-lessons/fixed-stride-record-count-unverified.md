# A record count from `(size - header) / stride` is not verified until you look past the last few slots

**When it bites:** you're sizing a uniform fixed-stride array (tiles, sprites,
table entries) by dividing remaining file bytes by a record size — especially
when the division isn't even clean cut, and you haven't individually looked
at content anywhere past the first row or two of results. Equally: you're
taking a record count from a *related* count somewhere else (a sibling
table's entry count, a resource type's population) rather than from the
table's own bookkeeping.

`(fileSize - headerOffset) / recordSize` (floored if it doesn't divide
evenly) tells you how many same-sized slots *could* fit in the remaining
bytes. It tells you nothing about whether the content in every one of those
slots is actually the same kind of record — a different, differently-shaped
data structure starting partway through the region will still "fit" some
whole number of slots at the wrong stride, and produce plausible-looking
output for a while if the different structure happens to start with
low-entropy or blocky data (a UI panel background, an icon border) before
degrading into visibly torn/banded garbage once the misalignment compounds.

Worked example (Black Crypt, Amiga, `crawl` project): `bcdfo` was documented
and extracted as "109 character portraits", 32x24 tiles at a fixed 576-byte
stride from a known base offset — purely `(63,010 - 0x60) / 576 = 109.2`,
floored. Only the first **36** tiles are real portraits; tile 36 begins at
*exactly* `0x60 + 36*576 = 0x5160`, which is this same file's own
already-documented, separately-sized UI descriptor table's first entry
(128x105, not 32x24). Reading it at the wrong fixed stride tore each real,
variously-sized UI element across several wrong-shaped "tile" boundaries —
visibly banded garbage that a full render (not just the first row) would
have shown immediately. This shipped as "109 portraits" across three docs
and a committed extractor for multiple sessions before someone actually
looked at tile 36 onward and asked whether it was still a face.

This is the same family of mistake as `rle-decode-succeeds-on-garbage.md`
(mechanical success ≠ correctness) and `unbounded-appended-data-boundary.md`
(a real content region ending mid-file, followed by something else, with no
length field announcing where) — but for a *fixed-stride tiling* read
specifically, where the trap is subtler because the arithmetic "just works"
with no decode step to fail at all. Before trusting a record count derived
this way: render every slot (not just enough to fill one screenful) and look
for a point where the content stops being the same kind of thing, and check
whether that point lines up with some other already-known offset in the
file (a different table's documented start) before shipping the count.

## The same trap with a borrowed count

A count inferred from a *related* structure fails the same way, and is harder
to spot because the number has an apparent justification. Spirit of Excalibur
CDTV's speech-cue table is **256** entries; the obvious count to reach for is
the 278 `CSTR` text resources it is keyed by, since the cue index *is* the CSTR
id. Reading 278 runs 22 records past the end into an adjacent pointer array —
whose values satisfy both structural constraints a real cue descriptor has
(bytes 0 and 4 zero) and fail only on value range.

The symptoms were quiet rather than obvious: a statistical check that should
have been decisive came out at +0.727 instead of +0.935, and nine cue intervals
overlapped each other when real ones never do. Both were initially read as
noise in the data rather than as the table being over-read.

**Fix for this variant:** range-check every field of every record, not just its
structural shape, and expose a `wellFormed` flag on the decode so a caller can
see where a table stops being a table. Where two candidate counts exist, prefer
the one the container's own bookkeeping supports over the one a related
structure suggests — and treat a degraded correlation or an impossible overlap
as an over-read hypothesis first, noise second.
