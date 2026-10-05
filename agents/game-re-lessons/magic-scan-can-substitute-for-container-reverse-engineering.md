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

## The trade-off, and the hard limit that is easy to get wrong

**The limit that actually bites: a magic scan silently misses instances of
the very format you ARE scanning for, whenever the container compresses
members.** A compressed member carries no magic anywhere in its bytes, so
the scan doesn't fail or warn — it returns a plausible, self-consistent,
*fractional* corpus. See
`compressed-container-members-invisible-to-magic-scan.md`.

**Correction to example (2) above.** Three Hopes' `.fdata` corpus was cited
here as a clean second confirmation. It is not. **54.5% of that game's
166,571 resources are zlib-compressed inside those same `.fdata` files.**
The technique did ship a working *texture* pipeline, but on the same corpus
it saw 198 files' worth of models where the container's own directory lists
**6,923**, and 1,675 animation clips where the directory lists **5,152** —
and a later pass then built a thorough, well-evidenced "this asset does not
exist anywhere in the extraction" negative entirely inside that blind spot.
The container (`_DRK0000`/`IDRK0000`, a Koei Tecmo RDB) also turned out to
be a straightforward directory, decoded and confirmed byte-exact against
161,563 records in one session — so "solve it properly" was never the
expensive option this lesson assumed. Example (1) still stands as written.

The milder trade-off also still holds: a magic scan only gets you the one
content format you're scanning for, and won't reveal a sibling content type
inside the same container that doesn't announce itself with a recognizable
magic.

**Corrected rule.** A magic scan is a legitimate fast path **when you only
need working output of format X, and nothing downstream will claim coverage,
completeness, or absence from it.** The moment a number ("N instances", "X%
decoded") or a negative ("format Y isn't here", "no larger rig exists")
rests on it, solve the container's directory first — it is often much
cheaper than assumed. And when recording the container as open work, say
that the corpus may be fractional until it is solved, rather than that the
container "doesn't matter" — that phrasing is what let the blind spot
survive several passes.
