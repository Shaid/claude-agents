# Summing a repeating structure's own per-record counts under 1-based numbering always lands one short of the total

**When it bites:** writing a regression test or verification probe for a
directory/bone/segment table whose records carry a **1-based** "first
index" field (`firstVertex`, `firstEntry`, `startId`...) plus a per-record
count, and the check is phrased as "does the sum of every record's count
equal the declared total" — this is a different (and subtly wrong)
statement from the format's own real internal invariant, and confusing the
two produces a test that fails on genuinely correct, already-verified
decoder output.

The real invariant a 1-based chain actually satisfies is: record `0`
starts at `1`; record `i+1`'s start equals record `i`'s
`start + count`; and the *last* record's `start + count` equals the
total. Because the chain is anchored at `1` rather than `0`, summing
**only** the `count` fields across every record (a 0-based accumulation)
is mathematically guaranteed to come out to `total - 1`, never `total` —
regardless of how many records there are or how the counts are
distributed. This isn't a decoder bug; it's an arithmetic identity of
1-based numbering that's easy to gloss over when translating a "the chain
should sum to the total" intuition into code.

Confirmed on Parasite Eve (PSX)'s actor-model bone table: a real,
already-pixel-verified-correct model (345 vertices, 22 bones) produced a
plain sum of `bone.vertexCount` equal to `344`, one short of `345` —
tripping a test assertion that had been "fixed" once already by naively
re-deriving the same wrong sum-based formula a second time, before working
out from first principles that the format's own parser checks
`lastBone.firstVertex + lastBone.vertexCount === total`, not
`sum(vertexCount) === total`.

**The fix generalizes:** when writing a verification loop for any
1-based-start repeating structure, track a running `cum` variable seeded
at `1` (not `0`) that gets reassigned to `record.start + record.count`
after each record (mirroring the decoder's own internal acceptance check,
if one exists — read it rather than re-deriving the formula from
intuition), and check that the *final* `cum` equals the total. Never
substitute a plain sum of the count field for this chain check on a
1-based format.
