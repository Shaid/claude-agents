# A variable-length composite record's alignment padding can sit at the very end, not between its own sub-fields

**When it bites:** decoding a `[count][sparse index/offset array][value
array]`-shaped variable-length record (or any composite record with two or
more variable-length sub-arrays back to back) against a known corpus-
confirmed total size, and a computed end offset is consistently off by a
small constant (commonly 2 or 4 bytes) that correlates with the record's
own count field's *parity* (even vs. odd) rather than being a fixed bug.

The natural first guess is that a variable-length sub-array needs 4-byte
alignment padding **immediately after itself**, before the next sub-field
starts (e.g. pad the sparse index array up to a 4-byte boundary, then the
value array starts at that aligned offset). This is often right, but not
always: confirmed wrong on Drakengard/Drakengard 2's `CMFf` animation-clip
format (PS2, Cavia Inc.) — a per-joint keyframe block shaped
`[u32 count][((count-1) u16 sparse frame indices)][value array, 8 or 6
bytes/sample]` consistently computed an end offset 2 bytes short of the
real (corpus-confirmed, via the next record's own start offset) block
boundary, but *only* when the sparse index array's byte length wasn't
already a multiple of 4 — i.e. the discrepancy tracked the index array's
own element-count parity, not a fixed off-by-constant bug.

The real rule: **the padding belongs at the very end of the whole
composite record**, after the value array too — i.e. `alignUp4(indexArray
+ valueArray)`, not `alignUp4(indexArray) + valueArray`. Both formulas
agree when the index array already lands on a 4-byte boundary on its own
(masking the bug on roughly half of real records by luck), which is what
let a first pass's implementation look correct against several samples
before a full corpus-wide structural-closure check (every record's
computed end must equal the next record's real start, whole-corpus, zero
tolerance) surfaced the residual failures precisely on the odd-parity
cases.

**Fix:** when a per-record byte-alignment formula shows a small, constant-
magnitude residual correlated with a count/length field's parity rather
than being wrong outright, don't just add a fixed fudge constant — test
moving the alignment operation to wrap the *entire* record (every
sub-field it's known to contain) rather than sitting between two
particular sub-fields. This is cheap to test (one-line change) and, when
right, fixes every failing record in the corpus at once rather than
needing a per-case exception. Corpus-wide before/after here: a structural
validator checking every block's declared end against its real neighbor's
start went from 467/1,133 (41%) to 1,133/1,133 (100%) passing with this
one change.

Distinct from `planar-plane-padding-vs-tight-stride.md` (that lesson is
about *fixed-size* bitmap planes padded to a round buffer size instead of
packed tight — a different record shape and a different symptom, silent
progressive image degradation rather than a hard structural-closure
failure).
