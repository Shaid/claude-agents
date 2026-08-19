# A raw magic-byte scan can fully substitute for reverse-engineering an unknown container, if you only need one known content format out of it

**When it bites:** you've confirmed (or inherited an already-working decoder
for) a *content* format's magic bytes (G1T, a texture header, a compressed-
stream tag, ...), but the *container* wrapping it is unfamiliar, undocumented,
or only partially reverse-engineered — and the instinct is to fully solve
the container's directory/header structure before extraction can start.

Often you don't need to. If the goal is "get every instance of format X out
of this corpus" rather than "understand everything this container holds,"
scanning the raw (or, for a compressed container, decompressed) bytes of
every candidate file for X's magic and validating each hit against X's own
parser (bounds checks, sane field ranges, entry-count sanity) is frequently
enough on its own — and is far cheaper than a full container reverse-
engineering pass, especially when the container turns out to be inconsistent
across sub-types (a fixed-slot directory whose slot-count semantics differ
between a model pack and a stage/scenario pack, say) in ways that would
otherwise block a clean unified parser.

Confirmed twice in one Chimera session, against two structurally unrelated
containers: (1) Fire Emblem Warriors (2017)'s per-asset "pack" files (an
undocumented, only-partially-solved `{length, cumulativeEnd}`-table format)
— scanning every file's raw bytes for G1T's `GT1G` magic and validating
each hit with the existing `parseG1T` found 829 valid G1T blocks / 8,216
textures corpus-wide, with a single false positive out of 830 raw magic
hits (rejected by the bounds check), all without ever needing the pack
header's real structure. (2) Three Hopes' `.fdata` asset blobs (a `PDRK0000`/
`IDRK0000`-tagged wrapper never reverse-engineered at all) — the identical
technique found textures there too. Both extractors shipped as the working,
"confirmed" texture pipeline for their respective games while the actual
container headers remain partially or fully unsolved — recorded as *known
open items*, not blockers, because the extraction goal didn't need them.
`fe-threehouses`' existing stage in the same project independently arrived
at the same technique against DATA0/DATA1 entries, which is a second signal
this generalizes rather than being a one-off trick for these two containers.

**The trade-off to be explicit about:** a magic scan only gets you the one
content format you're scanning for. It won't reveal a sibling content type
inside the same container that doesn't announce itself with a recognizable
magic (a model/mesh format with no distinct tag, say) — if the task needs
*everything* the container holds, not just one known format, the container
still has to be solved properly eventually. Treat the scan as the fast path
to a specific, already-identified deliverable, and record the container's
real structure as open/future work rather than silently deciding it doesn't
matter.
