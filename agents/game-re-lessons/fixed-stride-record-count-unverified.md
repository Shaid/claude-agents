# A record count from `(size - header) / stride` is not verified until you look past the last few slots

**When it bites:** you're sizing a uniform fixed-stride array (tiles, sprites, table entries) by dividing remaining bytes by a record size — especially when the division isn't clean and you've only looked at the first few results. Equally: you're borrowing the count from a *related* structure, taking the table size from a "data start" header field, or confirming a stride on a file with only one record.

`(fileSize − headerOffset) / recordSize` says how many slots *could* fit, not that every slot holds the same kind of record. A differently-shaped structure starting partway through still "fits" a whole number of slots and renders plausibly for a while if it begins with low-entropy data, then degrades into torn, banded garbage.

**Check / fix:** render every slot, not one screenful; find where content stops being the same kind of thing and check whether that point lands on another already-known offset in the file. Range-check every field of every record (not just its structural shape) and expose a `wellFormed` flag so callers see where a table stops. Prefer the count the container's own bookkeeping supports.

**Canonical example:** Black Crypt (Amiga, `crawl`) `bcdfo` shipped as "109 character portraits", 32×24 at 576 B from a base: `(63,010 − 0x60) / 576 = 109.2`, floored. Only 36 are portraits; tile 36 begins at exactly `0x60 + 36×576 = 0x5160`, the first entry of the same file's separately-sized UI descriptor table. The wrong stride tore each UI element across several "tiles"; it shipped across three docs and an extractor for several sessions.

## Borrowed count

Spirit of Excalibur CDTV's speech-cue table has **256** entries; the obvious count is the 278 `CSTR` resources it is keyed by. Reading 278 runs 22 records into an adjacent pointer array whose values pass the structural checks (bytes 0 and 4 zero) and fail only on range. Symptoms were quiet: a correlation of +0.727 instead of +0.935, and nine overlapping cue intervals. Treat a degraded correlation or an impossible overlap as an over-read first, noise second.

## "Data start" field read as table size

A header field that equals header + table size is easy to read as the table size; `n = field / stride` then yields one extra slot that decodes the first payload's opening bytes as an entry. Tells: a declared "populated" count that is "off by one, unexplained"; the extra entry's name/hash field holds a recognisable payload start (`"cavia stream format v1.01"`, `fpk\0`, an MPEG pack header); a walker that swallows decode errors may emit a whole archive as one leaf. Compute `n = (field − headerSize) / stride` and require `populated` to equal the non-empty slot count on every container. Cavia `dpk` (Drakengard 1/2, PS2, `flower`): slots = `([0x0c] − 0x20)/32`; the old formula added 904 garbage leaves to one archive and a 544 MB bogus leaf to another; fixed, `populated` matches on 907/907 headers.

## Stride confirmed on a single-record file

With one record, any stride ≥ the true one still reads inside that record's real bytes and looks plausible — there is no second boundary to walk into. MGR:R (PC, `flower`) `WMB4` `meshes[]` was pinned at 56 B from `ba0012.wmb` (`numMeshes=1`); the corpus run then failed on 752 of 1,453 files, every one multi-mesh and always from the *second* record, with "offsets" that were float bit patterns (`1029824172` ≈ 0.055). A stride sweep on a multi-record file found 68 B in seconds. Say "confirmed only against a single-record file" in the doc until an n>1 sample exists. Failures clustered after the first record, and garbage that reads as floats, point at a phase/stride error, not corrupt data.

Related: `rle-decode-succeeds-on-garbage.md`, `unbounded-appended-data-boundary.md`, `declared-range-field-loose-for-bulk-records.md`.

**History:** 4 instances (crawl Black Crypt, middilgard Spirit, flower MGR:R + dpk). Verbatim pre-condensation text and the dpk instance in `_archive/fixed-stride-record-count-unverified.md`.
