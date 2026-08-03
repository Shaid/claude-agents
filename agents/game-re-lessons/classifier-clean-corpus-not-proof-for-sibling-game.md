# A structural classifier with zero false positives on one game isn't proven for a same-format sibling game

**When it bites:** reusing a content-type classifier (a `looks_like_X`
structural/statistical heuristic used to sort a container's untyped
resources into categories) unmodified against a sibling game that shares
the exact same container format, especially before trusting its bucket
counts as a corpus-wide tally the way the original game's were.

A heuristic classifier can be legitimately, corpus-wide, zero-false-positive
"confirmed" on the game it was built against, and still misclassify real
content on a sibling game using the identical container format — because
the two games don't necessarily use every *sub-format* the container can
hold the same way. A heuristic tuned to reject everything the first game's
own other content classes could produce has no guarantee of rejecting a
sub-format the first game simply never puts in that container at all.

Confirmed on Dungeon Hack vs. EOB3 (`~/Development/crawl`, both AESOP/16,
sharing `scripts/eotb3lib/classify.py`'s container-content classifiers):
EOB3's `looks_like_pcm_sound` (an 8-bit-PCM byte-histogram bell-curve check)
was corpus-wide zero-false-positive against EOB3's entire `EYE.RES` —
verified this pass by explicitly checking EOB3's own `pcm_sound`/`unknown`
buckets for anything that also structurally decoded as the "old format"
row/span-RLE bitmap, and finding none. The reason is architectural, not
coincidental: EOB3 only ever uses that bitmap encoding *inside* a separate
GFF cutscene container, never as a bare resource in `EYE.RES` itself, so
the classifier was never exposed to it. Dungeon Hack embeds that same
bitmap encoding **directly** in its main container (`HACK.RES`/`OPEN.RES`)
for full-screen art and sprite/LOD tile sets — and several of those
resources ("Floor Deco 08", "Portrait 2", named graphics, not sounds)
happened to pass the byte-histogram check too, real false positives the
first game's own validation could never have caught.

The fix was a stricter, higher-priority structural check for the format
the first game's classifier had never had to reject (a full decode-and-
validate of every declared sub-record, not just a byte-value-distribution
heuristic), inserted *before* the looser heuristic in classification
priority order — and confirmed the fix changed nothing for the original
game (re-ran the stricter check against EOB3's own buckets: zero additional
matches, zero regressions).

The general move: before trusting a reused classifier's bucket counts on a
sibling-game corpus as if they were re-confirmed, check whether the sibling
game's own container inventory includes any sub-format the first game only
ever nested inside a *different* container (or otherwise never exposed
directly to that classifier) — a same-format container does not imply
same-usage-pattern container, and "zero false positives on game A" is a
claim about game A's actual content mix, not about the heuristic's
selectivity in the abstract.
