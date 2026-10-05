# A container's role read off its first tagged sub-block's magic can name a slot that holds none of the real content

**When it bites:** a multi-slot/multi-chunk container has been given a
semantic role in the docs on the strength of the magic found at its
`firstBlockStart` (or chunk 0) — `"INFO"`, `"HEAD"`, `"DESC"`, anything
that reads like a label for the whole file — and that role is about to be
carried into another pass, an escalation brief, or a TODO row. Ask first:
does the named block actually *vary* across the corpus, and does it account
for any meaningful fraction of the file's bytes?

Confirmed on Fire Emblem Warriors (Switch, `chimera`):
`nx/stage/info/S###-Info.bin.gz` (~676 KB each) carries the magic `"OFNI"`
— `"INFO"` under the project's reversed-magic convention — at
`firstBlockStart`, and a whole prior pass recorded the file as "likely
stage metadata/bounding-box data (unconfirmed)" on that basis alone. That
magic labels **pack slot 0 only**: a 128-byte descriptor (0.02% of the
file) that is byte-identical across 18 of the 19 stages, with a single
varying u32. It contains no stage-specific data of any kind. The file's
actual content is in slots 1-4 — a 256x256 1-bit navigation bitmap, a
128x128 coarse grid carrying a rectangular sector partition, an
axis-aligned quad list, and a float parameter block — none of which the
word "INFO" describes or hints at. The fix was a two-minute slot walk plus
a cross-stage byte diff of each slot, which immediately showed slot 0
constant and slots 2/3 fixed-size-but-varying.

The trap is structural, not a lapse of care: the first tagged block is the
one a triage pass hexdumps, so its magic is the first human-readable string
anyone sees, and a container whose *own* filename agrees with it
(`S###-Info.bin.gz` / `"INFO"`) reads as corroboration when it is really
just the same naming convention twice.

**Cheap diagnostic, before trusting any inferred container role:** diff the
named block across the corpus. A block that is byte-identical (or nearly
so) across every instance cannot be what makes those instances different
from each other, so whatever the container is *for*, that block is not it.
Then rank the slots by (a) bytes and (b) cross-corpus variance and hexdump
the top of each — the role lives in the slots that are both large and
varying. A sibling trap one level down is
`main-chunk-role-masks-own-unopened-payload.md`: there the first chunk was
large and *did* hold the missing data, but an assigned wrapper role kept
anyone from opening it. Same root cause — a name standing in for a content
classification — opposite symptom.
