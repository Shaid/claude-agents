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

**The same trap defeats a from-scratch structural search, not just a
scanner refinement pass, when the search has no address/provenance
anchor to fall back on.** Valkyrie Profile (PSX, `valkyrie`): searching an
entire corpus for an unlocated 33-entry/12-byte-stride table (known only
by its record shape — a flags-byte value range plus a function-pointer
field passing a validity check) using structural constraints alone did
turn up a genuine, fully-conforming match: 33 consecutive records,
correct stride, every flags byte and pointer field passing every
constraint. It was the wrong table — a completely unrelated dispatch
table belonging to a different, unidentified subsystem (a different TOC
slot, pointers clustering in an address range outside every already-
mapped overlay), which happened to reuse the identical 12-byte record
convention (id + flags + pointer) as an engine-wide idiom. Because the
target table's *address* was unknown (that was the entire point of the
search), there was no way to disambiguate the false hit from structure
alone — only opening the block, resolving which TOC slot/file contained
it, and checking whether that provenance was even plausible for the
target subsystem exposed the mismatch. General takeaway, extended: when a
structural-only search (no address anchor, no directory/manifest cross-
check) turns up a hit that satisfies every constraint, that is necessary
but not sufficient evidence of identity whenever the record shape itself
could plausibly be an engine-wide convention rather than something unique
to the one table being hunted — confirm provenance (which container, which
subsystem, which already-known consumer's own reachable address range)
before promoting a structural match to a solved location.
