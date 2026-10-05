# A well-above-chance-but-not-clean single-offset fit against a direct target oracle means try an indirection step, not "field is noise"

**When it bites:** a small numeric id field (character/model/asset id, item
id, etc.) is hypothesized to index directly into a target archive/table
whose real membership you can check (a confirmed file/entry-index set,
a name table, ...), a brute-force single-constant-offset sweep against that
target finds a clear best fit, and that fit lands in the **80-95% range** —
convincingly above chance, but not clean/total, and no amount of widening
the offset search improves it.

This is a different diagnosis from `partial-resolution-rate-is-noise.md`
(that file covers a **40-70%** match rate, which usually means the field is
*wholly* wrong — a missing byte-order fix or in-place loader transform on
the *same* field). An 80-95%+ single-offset fit is too clean to be pure
chance and too dirty to be the direct answer. The likely cause is that the
id is a **row index into a separate, already-parseable-but-unopened table**
(a sibling section of the same container, or a companion table elsewhere)
whose fields are the *real* per-kind small ids that then need the additive
constant — not the original id itself.

Confirmed on Fire Emblem: Three Houses (`chimera`, Switch): a `PersonData`/
`ClassData` character/class `assetId` field (0-451) was known to select a
3D body/head model, and a brute-force offset sweep of `assetId + k` against
the real (structurally re-derived, not manifest-cached) set of non-empty
DATA0 mesh-pack indices best-fit at `k=+3639`, hitting 176/202 (87%) of
distinct ids — well above the ~61% base rate from pack-file density alone,
but stuck there regardless of search range. The real mechanism: `assetId`
is a row index into `PersonData`'s own **section 1** (a sibling section of
the same already-parsed container, previously left undecoded past section
0), whose `part1Body`/`part2Body` int16 fields are themselves small
per-kind ids that (fed through their *own* offset, `+3120`) resolve
352/355 (99.2%, with all 3 "misses" independently confirmed as genuinely-
empty archive slots — i.e. effectively 100%). The original 87% fit was real
signal, not chance, precisely *because* `assetId` and the true body-model id
are correlated (allocated in similar order) without being the same number.

**The move:** before accepting an 80-95% single-offset fit as "the mapping,
just imperfect," check whether the id's own container has an already-
structurally-confirmed but never-content-decoded sibling section/table — a
20-90% overlap between two id spaces is exactly the signature of "these
correlate because of shared allocation order, not because one directly
equals the other plus a constant."

**Caution on the other tail:** a fit that comes back **100%** from the same
sweep machinery is not automatically stronger — if the per-hit acceptance
test was just "target slot non-empty" in a dense range, a perfect score is
achievable by many wrong offsets (this same FE3H table's `sothisFusedID`
field "confirmed" 31/31 at `+3049` and was later refuted outright). See
`dense-range-offset-fit-needs-identity-oracle.md`.
