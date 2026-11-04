# A table column whose values land in a known index space is probably not an index — run the residue/range/sortedness null battery first

**When it bites:** a large fixed-stride table (thousands of rows) has a
column of small-ish integers, some fraction of them are valid indices into
a table you have already solved (a TOC, a resource catalogue, a string
pool), and the column gets written up as "the index list into T". The
write-up survives because nothing ever tried to make it fail: the only
test applied was "is this value a valid index", whose base rate in a
densely-populated target is high by construction. The claim then becomes
load-bearing for everything built on top of it.

**Small integers fit small-integer index spaces by coincidence.** Before
citing any column as an index, run four cheap structural checks — each of
which a *genuine* index set passes and an address, offset, size or packed
field usually fails:

1. **Residue distribution** against the target's stride/alignment. A real
   index into an N-entry table populates **all** residues mod any
   stride; a byte offset or address populates only the aligned ones.
   This is the single sharpest test and it needs no ground truth.
2. **Range violations**, counted — not "values look in range" on a
   sample. Any row whose value exceeds the target's entry count refutes
   the reading outright; a handful can't be waved off as padding without
   a mechanism.
3. **Sortedness / monotonicity.** An index column in an unsorted record
   table has no reason to be ordered. A column that is sorted, and whose
   first and last values bracket a known module/segment extent exactly,
   is an **address range**, not an index.
4. **Neighbour-column context.** Columns in the same row are usually one
   structure. Try each neighbour against quantities you can already
   derive independently (a function's stack frame size, a span length, a
   row count) under plain shifts and masks — a 98%-level hit names the
   record's real purpose and retires the index hypothesis with it.

Compare the observed rate against what pure chance gives for *that* value
window (`partial-resolution-rate-is-noise.md`), and treat "always in range"
as the weak positive it is (`cross-stat-correlation-refutes-index-
hypothesis.md` — correlation against confirmed same-record fields is the
equivalent battery for gameplay stat records, where residues mean nothing).
A ~100% fit from an offset sweep is the third regime and has its own file
(`dense-range-offset-fit-needs-identity-oracle.md`).

**Canonical example:** Valkyrie Profile (`valkyrie`). A 4,089-row table's
middle column was documented for **months** as a list of TOC indices on
the strength of 153 of its values being valid TOC indices — 14% of the
target population, i.e. squarely in chance territory. The battery refuted
it in minutes: residues mod 4 populated **only 0 and 1** (an index set
would hit all four), 118 rows held values beyond the target's range at
all, the adjacent column was **sorted** and spanned the code module's
extent exactly, and a third column's value `>> 9` equalled the stack frame
size of the function named by column 0 for **98%** of rows. The table was
never an index list; it was per-function code metadata.

**The general rule:** a column is an index only once something has tried
and failed to show it is something else. Run the null battery before the
claim is written, not after it has been cited for months.

**History:** 1 recorded instance (`valkyrie`).
