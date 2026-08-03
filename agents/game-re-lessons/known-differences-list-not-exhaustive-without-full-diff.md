# A documented cross-release "known differences" list built from targeted spot-checks is not proof no other differences exist

**When it bites:** about to treat a doc's already-enumerated list of
confirmed cross-build/cross-region/cross-port content differences as
complete — especially before writing a report, closing out a comparison
task, or concluding a censorship/localization-content investigation with
"these N are the only differences."

A "known differences" list is only as complete as the checks that produced
it. If those checks were targeted (verifying two or three specific,
already-suspected divergent records) rather than an exhaustive scan of the
whole comparable corpus, the list documents "differences found by the
checks we ran," not "the differences that exist." This matters most for
exactly the class of comparison where it's cheapest to get wrong:
localization/censorship-style edits, which are usually small in number,
scattered unpredictably across a large corpus, and easy to miss with
targeted checks but cheap to find with a full diff once you have a
same-shape filter to separate "real content edit" from "index/pointer-shift
artifact" (see `fixed-offset-diff-across-builds-hides-pointer-shift.md`).

**Confirmed on FFVI (SNES)** (`ceres` project): a prior session's doc
documented exactly 2 concrete monster/Esper battle-graphics differences
between the US and Japanese-original ROM releases, found via two targeted
stencil-bitmask checks. A later session diffed **all 176** unique
monster/Esper graphics pixel-for-pixel — each independently decoded from
each ROM through its own per-release pointer record, to avoid confusing a
real content edit with an already-documented pointer-shift artifact — and
found 4 more, previously-undocumented differences. All 4 had byte-identical
stencil bit-sets between releases (ruling out the tile-count-change
explanation the 2 known ones have) and were spatially localized to the
chest or groin region of a humanoid figure in every case — consistent with,
and in two cases (graphics independently named "Chadarnook" and "Goddess"
in a community disassembly project's own asset list) matching, well-known
real-world Nintendo-of-America-era SNES content-modesty edits. The 2-item
list wasn't wrong, just silently incomplete — nobody had run the full
176-graphic diff before.

**The fix:** when a task's "how much differs between these two
builds/releases/ports" question matters (and especially for anything
localization- or censorship-adjacent), run an exhaustive diff over the
*whole* comparable corpus rather than trusting an existing partial list, or
explicitly flag in the doc that the list reflects only the specific checks
performed so far, not a corpus-wide scan. A cheap, generalizable technique
for telling a real content edit apart from a shift/rearrangement artifact
mid-scan: for structures with an independent stencil/bitmask/index-set
field (which record layout doesn't change), require that field to be
byte-identical between releases before treating a pixel/byte difference as
"real content" rather than "the same content moved" — this is exactly what
separated the 4 new genuine edits from the 2 already-known
tile-count/rearrangement cases in the FFVI example above.
