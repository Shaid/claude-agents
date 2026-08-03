# A record template reused across resource types leaks false positives into the first type's scanner

**When it bites:** a scanner for a confirmed record format finds a small
number of outliers with an unhandled field value (an "unknown format" or
similar), especially when those outliers are few, small, and otherwise
structurally perfect matches for the confirmed format's own discriminating
invariants.

Strike (Mega Drive): a 32-byte tilemap-header template's scanner used three
internally-redundant fields as its structural signature. Five records
across two ROMs passed every one of those checks but carried a payload
`format` value the confirmed decoder didn't handle. They turned out not to
be tilemaps at all — they were 5 of 271 records belonging to a completely
separate indexed resource (an "overlay-tile bank") that happens to reuse
the *exact same* 32-byte header layout, with three of its fields meaning
something different (one reserved-always-zero field became a live index;
one pointer field became dead/vestigial boilerplate). Every bank record
whose reinterpreted index field happened to equal zero passed the tilemap
scanner's structural test as a silent false positive — including a
`format` value the tilemap decoder *did* recognize, which meant it
rendered without erroring, just against the wrong tileset (plausible-looking
but wrong pixel content, not an out-of-range-cell crash).

The fix that worked: find the one field that reliably differs between the
two populations, not a positional/span heuristic and not a naive
duplicate-count threshold. Here, real records of the original type each had
a *per-record-unique* resource pointer (adjacent to their own record),
while every record of the *other* type in a given file shared one single
constant value for the same field (vestigial/dead for that type). Filtering
the original scanner on "this pointer value is the sibling type's known
shared constant" closed the false positives completely. A frequency-based
heuristic ("this pointer value repeats more than N times") was tried first
and rejected: legitimate records of the *original* type also shared
pointers up to 18 times in this corpus — more repetition than the leaking
type's own 3-4x — so repetition count alone did not separate the
populations; only "shared by literally every record of the other type,
file-wide" did. Derive the exclusion set programmatically from the sibling
type's own scanner (once it exists) rather than hardcoding the constant,
so the fix stays correct if the corpus grows.

General takeaway: when a confirmed record scanner turns up a handful of
almost-but-not-quite-conforming outliers, check whether they're actually a
*different* resource type before assuming they're a variant or a
compression-related exception of the type you already understand — engines
that reuse one struct-building code path across multiple loaders are common
enough that "same template, different consumer" should be a live hypothesis
from the start, not a last resort.
