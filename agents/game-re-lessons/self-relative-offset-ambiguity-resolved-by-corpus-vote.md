# A "self-relative offset" ambiguity with no reference source can be settled by a corpus-wide parse-success vote between the candidate bases

**When it bites:** a format doc (yours or a prior pass's) names a field
"self-relative" or otherwise leaves its exact base ambiguous between two
plausible readings (relative to the field's own address vs. relative to
its enclosing array/table's base — the *other* convention the same format
family uses one level up), and there is no disassembly, reference source,
or SDK available to settle it directly this pass.

Don't guess by analogy to a sibling field's convention (e.g. "the
enclosing table's own header offset is base-relative, so this nested
field probably is too") and move on — the two candidates can diverge
sharply in practice even though both are "a plausible reading of the
prose." Confirmed on Valkyrie Profile (PSX)'s room-compositor section-5
content-animation table (`valkyrie` project): a per-frame 12-byte record's
`dataOffset` field was documented as "self-relative" (from an earlier
pass that decoded the *entry*-level struct but never traced the
individual frame records or the routine that walks them) with no
disassembly access this pass to confirm which base it meant. Resolving it
as `frameRecordAddr + dataOffsetRaw` (literally self-relative, matching
the field's own name) gave a byte-exact-valid downstream parse on
1,850/1,850 (100%) real frame records across the whole corpus; the other
candidate, `enclosingArrayBase + dataOffsetRaw` (the sibling convention
the entry-level struct one level up genuinely does use), gave only
702/1,850 (38%) — not a close call, a decisive discriminator. A second,
independent field (`copyLength`, matching a derivable expected value on
94.3% of records) corroborated the same reading.

**Fix:** when a self-relative-offset ambiguity has no reference
implementation to settle it, compute BOTH candidate resolutions across
every real instance in the corpus and require each one's result to
satisfy an already-independently-confirmed downstream structural check
(a sibling record parses cleanly, a value falls in an already-known valid
range, a byte-exact length identity holds) — not just "doesn't crash."
The candidate with near-100% pass need not be probabilistically close to
the loser to be trustworthy; in practice a genuinely correct base tends to
resolve to *every* real instance, while a wrong one only accidentally
lands on a valid target some of the time. Treat anything short of a clean,
large-margin split as inconclusive and escalate or find a third oracle
rather than picking the higher number by a small margin.
