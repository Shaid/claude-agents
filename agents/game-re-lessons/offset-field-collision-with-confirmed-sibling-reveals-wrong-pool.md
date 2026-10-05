# A decode that "looks like" a different, already-confirmed sibling format may just be that sibling's real bytes, misaddressed

**When it bites:** several record types share one struct layout with an
`offset`/`size` pair addressing a common payload pool (a directory record, a
GPU-resource table entry), the convention is already confirmed for most of
those record types, and decoding one specific type's payload through that
same convention produces content that structurally *resembles* a different,
already-confirmed sibling format — not garbage, not noise, a coherent-
looking false positive. Also bites when a record type carries an already-
known-but-uncharacterized flag/discriminant bit correlated with whether it
has a real payload at all (logged as "role unconfirmed," never fully
resolved).

Confirmed on NieR (2010, PS3, `flower`): a `HEAP` GPU-resource directory's
`VXSH` (vertex-shader) records share the exact same 32-byte record shape as
`IXBF`/`VXBF`/`TX2D`/`PXSH` (offset+size into the paired `.MDP` payload
stream), and reading `VXSH.rawOffset` against `.MDP` produced small
ascending `u16` values with `0xFFFF` restart tokens — structurally
*identical* to the already-solved `IXBF` (index-buffer) format. A prior pass
took this at face value and documented it as "index-buffer-shaped, unusual."
It wasn't a coincidence of format similarity: `VXSH`'s declared byte range
collided **byte-for-byte** with the model's own real `IXBF`/`VXBF` ranges in
1,332/1,334 (99.9%) records corpus-wide — the "index buffer" content was
literally misaddressed `IXBF` bytes read through the wrong base.

**The two-part test that cracked it, generalizable to any offset-field
format:**

1. **Collision-with-confirmed-content check.** Does the record's declared
   `[offset, offset+size)` range, read against the pool the shared
   convention assumes, overlap an *already-confirmed* sibling record's own
   declared range? If yes for (nearly) every instance corpus-wide, the
   shared convention doesn't apply to this record type — it's not that the
   format is unusual, it's addressing the wrong pool entirely.
2. **Self-consistency-among-itself check.** Do the suspect record type's own
   offsets, taken alone and sorted, still tile with zero gaps and zero
   overlaps from a fresh base of 0 (after deduplicating any records that
   legitimately share one payload)? If yes, the offsets are real and
   self-consistent — proof they address *some* real pool, just not the
   assumed one. This is what tells you to go looking for a second pool
   rather than writing the field off as garbage/unused.

Once both checks flagged the mismatch, the real base was found in the
obvious adjacent place: immediately after the directory's own already-
confirmed descriptor-pool region ends, inside the *same* file the directory
lives in (not the paired payload file the shared convention assumed).
Confirmed whole-corpus, exact: 304/304 files, 1,334/1,334 `VXSH` records
tiled with 0 gaps/0 overlaps from that new base, and 0 files where the tiled
pool exceeded the directory's own declared chunk size. This also resolved
the previously-uncharacterized flag bit's real meaning: it wasn't a vague
"main-memory vs. video-memory" guess left untested — it was literally "which
of the two pools does `rawOffset` address," confirmed both directions
(0 exceptions either way).

**How to apply it:** before trusting a decode that "looks like" a known
sibling format under a directory's default addressing convention, check for
byte-range collision against already-confirmed sibling content first — a
structurally plausible decode is not evidence of a correct base. And before
writing off an outlier record type's offset field as garbage or an unused
convention, check whether it tiles losslessly among its own kind from a
fresh base — that's the signal a second, adjacent pool exists, worth
searching for at the boundary of an already-confirmed region (the directory
descriptor pool's own end, a header's declared size field, etc.) rather than
guessing at fixed constants.
