# An oracle-based "N/N exact match" verification can stay green for years while a decoder silently over-reads and generates extra garbage entries no comparison ever inspects

**When it bites:** a "confirmed, byte-exact" array/table-length field (a
record count, a table size in bytes) was verified by cross-checking
*specific, named/indexed* values against an independent oracle (a fan
decompiler's text dump, a community tool's printed field list) — before
trusting that the array's own declared LENGTH is also correct, especially
when the oracle's own comparison is driven by indices the oracle itself
enumerates.

## What went wrong

Frontier: Elite II's 3D model format has a per-model vertex table whose
length was computed from a header field documented (and shipped, in a
prior "confirmed, byte-exact" commit) as `verticesDataSize`, with
`numVertices = verticesDataSize / 4`. That commit's own verification
claimed "2,619/2,619 literal vertex positions match" against a real
community-decompiler oracle. The claim was true and remains true — and
was still hiding a real bug: the size field was actually wrong for every
model in the 230-model corpus (confirmed later via a direct, whole-corpus
recount: `(normalsOffset - vertexDataOffset) / 4` matches the oracle's own
declared count 229/229; the old field matched 0/229). The old, inflated
count made the decoder read `numVertices` records where the real count was
often an order of magnitude smaller — the extra "vertices" were garbage,
reading into the model's own normal table, its code stream, and beyond.

The bug was invisible to the "2,619/2,619 match" check because that check
was driven by the oracle's OWN printed comment-index labels — it looked up
"vertex at comment-index K" for every K the oracle printed, and the oracle
never prints indices beyond the real count. The decoder's extra,
too-many, out-of-bounds-of-the-real-data entries were never looked up by
anything, so they were never compared, so the mismatch was invisible to
every check run against that data — for as long as nothing else in the
pipeline ever indexed past the real count. (It surfaced only once a
downstream consumer — a submodel-assembly pass built on top of the same
decoder — printed `resolved_vertices[i]` for `i` just past the claimed
real count during ad hoc debugging, and found it was silently returning
literal normal-table bytes reinterpreted as a vertex.)

## The fix / general principle

An oracle-driven "N/N values match" check only validates the SUBSET of
positions the oracle itself iterates over — it says nothing about whether
your own array's LENGTH is correct beyond that subset. Independently
verify any decoded array's own declared/computed length against the
oracle's own declared count (not just spot-checking individual values at
oracle-chosen indices), especially when the length comes from a
still-unconfirmed or newly-introduced header field. A cheap, decisive test
once you suspect this: dump raw hex for the region just past where you
believe the real data ends, and check whether your decoder's own output at
those "extra" indices matches an ADJACENT, already-decoded structure
(here: vertex[N] == normal-table-entry[0]) — a smoking-gun sign the length
is wrong and the decoder has run off the end of the real data.
