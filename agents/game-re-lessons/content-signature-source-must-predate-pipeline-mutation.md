# A content-identity/dedup signature must be hashed from a file the pipeline never mutates again — not the promoted/final output

**When it bites:** computing a byte-identity signature (a dedup hash, a
"is this the same asset" fingerprint) from an asset pipeline's *promoted*
output file, when some other stage of that same pipeline (in this session
or an earlier one) writes additional data into that file in place after
promotion — most commonly an animation/metadata-injection pass appending
to an already-exported mesh/model file.

Confirmed on Drakengard 3 (PS3, `flower` project,
`docs/drakengard3/ps3/data-structure.md` §18): a full-corpus character-
identity dedup pass hashed each `SkeletalMesh3`'s promoted `.bin` (glTF
binary buffer) to detect byte-identical scene-local duplicates. One
specific mesh had already been animation-baked by an *earlier session's*
proof-of-concept pass (25 clips appended, growing its promoted `.bin` from
1,512,592 to 9,798,776 bytes) before the dedup pass ever ran — so it
hashed as "different" from its 58 true, never-touched duplicates, even
though its real geometry was byte-for-byte identical. The bug wasn't
theoretical: it silently mis-clustered exactly the one asset a prior
session's own manual verification had used as its reference example.

**The general trap**: any identity/dedup signature computed mid-pipeline
is only trustworthy if the source bytes are guaranteed stable for the rest
of that pipeline's life — which usually means computing it from data
*before* any enrichment/annotation stage, not from the promoted "final"
artifact a consumer-facing viewer serves. Two independent identity checks
(two files that "should" be the same) drifting apart is real, silent
evidence of this — investigate before concluding the underlying assets
differ. If the pipeline still has the pre-enrichment staging copy on disk
(common: an offline pipeline stages raw exporter output, then
promotes/patches a copy into the public asset tree), source the signature
from that staging copy instead, with a documented fallback (and ideally a
regression test reproducing the exact drift) for corpora where the
staging copy no longer exists.
