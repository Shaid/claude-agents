# When two candidates tie at the identical score under your primary matching signal, look for an orthogonal signal instead of accepting ambiguity or lowering the threshold

**When it bites:** a match-scoring mechanism (bone-name overlap, structural
signature, any similarity metric) declines a real match because the top
candidates are genuinely, provably tied — not "close," but computing the
*exact same* score against every reference, because they share the
underlying data the metric measures. Lowering the confidence threshold or
widening the tier doesn't fix a true tie; it just admits more noise.

Confirmed on Drakengard 3 (`flower` project, `docs/drakengard3/ps3/
data-structure.md` §19): a moveset-merge pass matched creature meshes to
animation sets by bone-name overlap. 18 real character clusters were stuck
because their top two candidates — the *player character's own* general
moveset and an unrelated boss's moveset — scored *identically* for every
one of the 18, because both were built on the same shared 172-bone base
rig. No amount of bone-overlap threshold tuning could break this tie; the
metric was structurally blind to the actual distinguishing information.

**Fix**: find a signal from a *different* dimension of the data —
something the primary metric doesn't measure at all. Here: the game's own
production/package naming convention (`AS_<scene>_<character-id>`,
`ANIM_<id>_SF/<id>`) already encoded which specific character an AnimSet
belonged to, entirely independent of bone names. Checked against all 18
tied clusters, every one had its own dedicated, name-correlated candidate
elsewhere in the corpus — not hardcoded per-character, computed generically
by string-matching each mesh's own object-name token against every
candidate's object name. Use a **longest-common-substring** match on
normalized (lowercased, punctuation-stripped) tokens rather than a plain
`includes()` check when the shared "core id" is likely flanked by
*different* noise on each side (the target's own name may carry a
costume/variant suffix; the candidate's name may carry a scene/package
prefix) — neither full string is a substring of the other, but their
shared core is a contiguous common substring of both.

**A second-order trap once the secondary signal works**: sort its results
by the secondary signal's own precision (e.g. match ratio), not by a
convention borrowed from the primary signal (e.g. "richest candidate
first," sorted by content volume). Confirmed on the same corpus: a
same-family-but-wrong-member candidate had *more* content (34 sequences)
than the mesh's own exact dedicated match (14 sequences, but a higher,
more specific ratio) — sorting by volume let a caller's fixed injection
budget fill up on the less-precise match before ever trying the better
one, silently defeating the whole point of adding a precision-seeking
secondary signal in the first place.
