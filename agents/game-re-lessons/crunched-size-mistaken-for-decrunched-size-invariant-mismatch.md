# A byte-consumption invariant that "exceeds the file's size" may be checked against the wrong size

**When it bites:** a disassembled loop's total byte consumption (or any
other code-derived byte-count invariant) is compared against "the file's
size" and comes out larger, leading to a conclusion like "this routine
can't still be operating on the real buffer" or "must be a different,
larger scratch buffer this pass didn't locate" — on any format that is
stored compressed/crunched at rest.

A compressed-at-rest asset has (at least) two different, both-legitimate
"sizes": the on-disk crunched size, and the in-memory decrunched size the
game's own code actually operates on after decompression. If a prior
pass's documentation states a file's size without specifying which one,
or if a byte-count invariant is compared against a table that only lists
the crunched size (e.g. a per-file manifest built for tracking compression
ratios), the comparison silently uses the wrong number — and a real,
exact, zero-slack match against the correct number reads as "far
exceeding the file's size" against the wrong one, producing a false
negative that can stand unquestioned for an entire session or more.

Confirmed on Jungle Strike (Amiga AGA, `strike` project): a prior session
disassembled `LAB_0365`, a routine that consumes 9,100 bytes from a buffer
loaded from the file `weapons`, and wrote up "the byte math is
unresolved... far exceeding `weapons`' own confirmed 2,836-byte file
size... `108(A6)`/`112(A6)` are most likely NOT still pointing at the raw
`weapons` file by the time `LAB_0365` runs (a separate, larger
scratch/working buffer this pass didn't locate)." 2,836 was `weapons`'
**crunched** (LR88/PowerPacker) size; a one-line check (`decrunchLR88` and
compare) showed the file's **decrunched** size is exactly 9,100 bytes —
the routine's consumption matched with zero slack, and the "different
buffer" theory was needless. This one wrong comparison had blocked
progress on the file's entire pixel-content decode across multiple
sessions, even though every piece of evidence needed to refute it (a
one-line decompress-and-compare) was already sitting in the same
codebase.

**Fix:** whenever a byte-consumption/size invariant for a compressed-at-
rest resource "doesn't add up," explicitly re-derive and label both
candidate sizes (crunched and decrunched) before concluding a mismatch —
don't trust a size cited elsewhere in the docs without checking which one
it is. A byte-exact match against the *decrunched* size is exactly the
kind of zero-slack structural invariant this project's verification bar
calls for; failing to check it against the right number turns a positive
result into a false, standing negative.
