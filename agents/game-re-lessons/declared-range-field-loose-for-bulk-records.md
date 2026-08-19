# A record's own declared count/range field can be a loose bound for large/bulk records, not a tight one — derive the real range from downstream index references instead

**When it bites:** a per-record struct field looks like (and validates as,
against a small/medium dev sample) a tight sub-range into a larger shared
array — e.g. `start`+`count` into a vertex/element buffer — and you're about
to slice/copy that declared range directly to build a self-contained output
per record, especially for the largest/bulkiest records in a corpus
(world/terrain meshes, catch-all containers, anything that could plausibly
be "the whole buffer" for one record).

## What went wrong

Decoding PlatinumGames' `WMB3` mesh format (NieR:Automata PC,
`~/Development/flower`): each `mesh` record declares `vertexStart`/
`vertexCount` into its owning vertex group's flat vertex array. On small/
medium meshes this is a real, tight per-mesh sub-range — a genuine, useful
declared bound, confirmed 100% consistent (face indices always fell inside
it) across a 27-file dev sample. But on large **world/terrain** mesh files,
the same field is routinely a degenerate, maximally-loose bound: one real
mesh in a 52MB file declared `vertexStart=0, vertexCount=1,028,651` — 99.9%
of its whole 1,029,913-vertex group — while its own 8,424 face-index
entries only ever referenced a **7,142-wide window** near the end of that
range. 598 of 735 meshes in that one file showed the same shape
(`vertexCount > 100,000`, actual usage a small fraction of that).

This produced two real problems, not just an aesthetic one: (1) a
correctness risk — code that trusted the declared range as "this mesh's
real vertices" would have processed/exported up to a million vertices that
don't belong to that mesh at all, and (2) a severe **performance cliff**:
naively slicing/copying the full declared range per mesh made this one file
take **80+ seconds** to export (out of a corpus where files an order of
magnitude smaller export in under a second).

The struct field itself isn't corrupt or mis-parsed — it's genuinely the
value on disk, correctly read at the correct width and offset. The problem
is purely semantic: "declared count field" quietly stopped meaning "this
record's real element count" for a subset of records, and nothing about the
field's type or position hints at that — it looks identical to the tight-
bound case everywhere except in its *value*.

## The fix

Don't trust a declared count/range field as authoritative for a record's
real element set, especially once corpus scale reveals outliers — derive
the real *used* set from downstream index references instead (here: collect
every vertex index the mesh's own face-index entries actually reference,
dedupe, and remap to compact local indices). This is strictly safer (a
record's face indices are always a subset of its declared range — confirmed
zero violations) and, for the degenerate cases, dramatically faster (the
above 52MB file dropped from 80+ seconds to 1.1 seconds after the fix).

**A real prior-art detail worth noting**: two independent community
Python decoders for this exact format had *already* solved this — both
carry a `clear_unused_vertex()` helper that computes
`sorted(set(faceIndices))` + a remap dict, rather than trusting the
declared range, specifically to handle this case. A naive/literal port of
the format's own struct *fields* (which is all a byte-level spec conveys)
would have missed this entirely; the fix lived in the reference tools'
downstream *consumer* logic, not their struct definitions. When porting a
community decoder, read past the struct-parsing code into whatever
processing/export logic the reference tool itself does with the parsed
fields — it may already encode a correction the struct layout alone
doesn't reveal.

This is a sibling problem to `fixed-stride-record-count-unverified.md` (a
count formula untested past the first row) and
`shared-resource-caller-declared-dimension-under-reports.md` (a *caller's*
declared dimension for a *shared* resource under-reports vs. the resource's
real content) — different concrete shape: here it's a record's *own*
self-declared range being loose for a subset of records (not a caller/
resource mismatch), and the field is *correct on disk*, just not uniformly
tight in what it means.
