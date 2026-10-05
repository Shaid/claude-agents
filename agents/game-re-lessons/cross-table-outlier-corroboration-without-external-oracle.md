# When no external name/ID oracle exists, two independently-derived structural outliers in different tables can corroborate each other

**When it bites:** trying to attach a specific known game entity (a
character, item, or other identified thing) to one record ID in an
ID-registry-shaped table, and every external oracle route has come up
empty — no community 010-template, no save-editor/cheat-table ID list, no
WebSearch hit naming this exact game's internal numbering.

> **First, do not use this technique yet.** "No oracle exists" almost always
> means "no *external* oracle exists", and the strongest oracle for an
> asset-ID space is usually inside the game's own executable, not outside
> it. Read `executable-resource-path-registry-names-asset-ids.md` and
> extract the code partition before falling back to what follows. On the
> very game this lesson was written from, doing that later replaced the
> circumstantial single-record result below with a byte-exact name for all
> 350 records. What follows is the technique for when that has been checked
> and genuinely comes up empty (an archive-indexed title whose executable
> holds only `"%s.bin"`-style templates).

The usual ground-truth ladder (Method §4) assumes *some* external oracle is
reachable — a walkthrough, a fan datamine, a sibling port. Some games (a
first-of-its-kind title with no active RE community around its exact
internal formats) have none. In that situation, a same-corpus, cross-table
check can still produce real (if only circumstantial) confirmation: look
for a **second table with its own, unrelated ID namespace** covering
overlapping subject matter, found by an unrelated method, and check whether
an outlier record in each one independently points at the same real
entity.

Confirmed on Fire Emblem Warriors (2017, `chimera` project) — and the
technique's conclusion was later shown correct by a real oracle, which is
the best evidence it works. At the time, no *external* ID oracle was known
for `ModelChrParam.bin`'s 350-record, ID-100-470 per-model registry (WebSearch for 010-templates, cheat tables, and save-editor
character lists all came back empty for this exact game). Two independent
lines of evidence still converged on the same conclusion for one record:
(1) a column-level statistical census of `ModelChrParam.bin` itself found
exactly one record (`id=132`) that simultaneously carries the table's own
maximum values on two physical-size columns *and* a category-enum value
seen nowhere else in 350 records — a classic single-outlier signature for a
unique giant/boss entity; (2) a completely separate table in the same
corpus (`ModelWpnParam.bin`, its own leading-ID space 500-799, found via an
unrelated `strings` scan rather than a column census) turned out to embed a
literal on-disk model filename fragment (`"C_Evildragon"`) inside an effect
asset path belonging to one specific record — and that filename is
independently known (from the corpus's own model directory listing) to be
the game's unique final-boss dragon, with no alternate-costume sibling file
the way every normal roster character has. Neither table names its
"boss-ness" directly; the corroboration came from the *coincidence of two
independently-derived anomalies pointing at the same real thing*.

**Fix, generalized**: when an ID-registry table has a plausible outlier
record but no name for it, check whether a sibling table covering related
subject matter (weapons/effects/audio/etc., found via any method — strings
scan, magic-byte scan, format family reuse) has its *own* independent
outlier or literal-string hit, and whether the two are consistent with the
same real entity. Report the result as **hypothesis, strongly
corroborated** — not confirmed. (On FE Warriors that exact call was
vindicated: a later pass found the executable's resource-path registry and
`id=132` really is `C_Evildragon`. Holding it at "corroborated" rather than
promoting it to confirmed was the right discipline, and holding it there is
also what kept the question open long enough to get solved properly.) The
caution is real: the two ID namespaces still have no established mapping
between them, so this is meaningfully weaker than a
byte-exact cross-reference against a real external name table (contrast
`published-walkthrough-numeric-oracle.md`, `domain-archetype-plausibility-
oracle.md`), but it is a real, reusable step up from "unconfirmed
hypothesis" when literally nothing else is available.
