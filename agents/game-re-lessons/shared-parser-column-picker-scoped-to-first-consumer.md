# A factored-out "pick the informative field" heuristic is scoped to the question it was built for — a second consumer needs its own, re-derived pick

**When it bites:** refactoring a working row/field extractor (built to
answer one specific downstream question over a self-describing text/table
format) into a shared helper for a second consumer with a *different*
question, when the row carries more than one plausible-looking candidate
field (more than one backslash-containing path column, more than one
numeric id column) and the original heuristic was tuned to skip past one
of them in favor of another.

Confirmed on Metal Gear Rising: Revengeance (PC, `flower`): a Wwise
cue-sheet row carries both an "Audio source file" column (a literal
`D:\project\...\voices\english(us)\<code>\<file>.wem` build-machine path)
*and*, further right, a separate "Wwise Object Path" column
(`\Actor-Mixer Hierarchy\...`). The original music-only extractor
intentionally started its path search *after* the source-file column,
because music's own question ("what Interactive-Music-Hierarchy path is
this cue at") needed the Object Path, not the source file. Reusing that
exact "first path-shaped cell after the source-file column" rule verbatim
for a new consumer (recovering a voice line's character/actor code)
silently returned the *wrong* column — the Object Path, whose folder
convention doesn't have the `voices\english(us)\<code>\` shape the new
question needed at all. The regex match against it simply came back
`undefined`, with no error, and the new field ended up empty for every row
on the first attempt — even though the needed data was present, genuinely,
one column over, for essentially the whole corpus.

**Fix:** when reusing a shared parser's row shape for a new consumer,
re-derive which raw field the new question actually needs by reading a
handful of real rows *for that question specifically* — don't assume a
prior consumer's column-selection choice transfers just because the row
format itself is shared. A parser factored for reuse should expose the
individual raw cells (so each consumer can pick its own), not bake in one
consumer's "the informative path" choice as the shared behavior.
