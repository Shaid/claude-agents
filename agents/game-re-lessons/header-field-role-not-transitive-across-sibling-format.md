# A shared outer container doesn't guarantee a shared inner payload header — re-derive field roles per-format, don't inherit them

**When it bites:** two formats share an outer container confirmed byte-exact
(same directory shape, same codec), and you're about to read the *inner*
payload's header fields using the role assignments already confirmed for a
sibling format that uses the same container — especially when one of those
fields reads a suspicious, uninformative CONSTANT across the whole corpus.

Champions of Krynn's `8X8D0/1/2.DAA` tile-bank files share Death Knights of
Krynn's exact outer "Amiga DAA" container (the same big-endian 9-byte
directory-entry shape, byte-exact). It was natural to assume the *inner*
per-entry pixel-payload header also matched Death Knights' confirmed shape:
a 9-byte header with a `tileCount` u16 at offset 2, followed by a 64-byte
embedded palette, then plane data. Reading Champions' files this way gave
offset-2 a uniform, implausible `tileCount = 1` in every single entry — and
a "palette" region (bytes 9-73) that was always non-zero, which got flagged
as an unexplained structural puzzle rather than treated as the actual tell
that the field roles were wrong.

The fix was to stop trusting the sibling format's field positions and
re-derive them from this corpus's own bytes: sweep every plausible header
byte/field against a divisibility oracle (`(bodyLen - headerLen) %
(planeCount * 8) === 0`, i.e. "does this candidate tileCount evenly divide
the remaining plane data"). That found the real tileCount at offset 8 (a
single byte, not the offset-2 u16), with a fixed `planeCount = 4` and **no
embedded palette at all** — the "always non-zero palette region" was
actually just the first bytes of real plane data. This matched 24/25
entries exactly (the one exception being an off-by-one anomaly of the same
class Death Knights' own format has on its own "universal" entry).

**Fix, generalized:** a confirmed-shared *outer* container (directory
format, compression codec) says nothing about the *inner* payload layout —
two sibling formats can diverge there even when a naive read of field
positions looks plausible at first glance. Two tells that a field is
misidentified by analogy rather than confirmed on this corpus's own data:
(1) a field that should vary meaningfully instead reads a constant,
uninformative value across every instance; (2) a structurally "unexplained"
region flagged as a puzzle rather than resolved — both are signals to
re-derive the header from scratch (sweep candidate offsets against a
structural invariant/divisibility oracle) rather than inherit the sibling
format's role assignment.

**Second confirmed instance — a per-record field offset, not just a
header.** 13 Sentinels: Aegis Rim (Switch)'s `FMBS` sprite-model format
(`vanille` corpus) shares its 20-byte `part` record's overall shape and
semantic roles with the already-solved PS3/Wii `FMBS` siblings' 12-byte
`part` record, but the texture-page-index field moved from offset `+3`
(every sibling's position) to offset `+7`. Reading `+3` on Switch gave `0`
for every part on both a single-page test model *and* a 2-page test model —
a uniform, non-discriminating constant, exactly tell (1) above — because it
happened to be a genuinely-unused padding byte on this platform, not
because the model only used page 0. A byte-value histogram swept across the
whole record (not just the sibling-convention offset) found `+7` splits
cleanly into exactly N distinct values matching each multi-page model's
real page count, confirmed corpus-wide with 0 exceptions across 120,546
sampled parts. The same session also confirmed several *other* fields in
the same record (`uv`/`colour`/`xy`) kept their sibling positions
unchanged — the lesson isn't "assume everything moved," it's "verify each
field independently against this corpus's own bytes rather than inheriting
the whole record layout wholesale."
