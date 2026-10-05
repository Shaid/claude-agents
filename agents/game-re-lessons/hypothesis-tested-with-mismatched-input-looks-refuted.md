# A structural hypothesis tested with a mismatched input looks refuted — retest with an input derived from the target's own logic

**When it bites:** a runtime selector/discriminator hypothesis (a
layer/mode/bank index, a palette page, a script-side "which sub-array"
flag) was tested by borrowing a concrete test input (a position, cell,
sample id) from a DIFFERENT already-solved sibling script/consumer, got a
blank or degenerate result, and was filed as INCONCLUSIVE or "probably
wrong" — before trusting that verdict, check whether the input itself, not
the hypothesis, was the mismatch.

A test position/sample/index that is real for one consumer of a shared
mechanism is not automatically valid for a sibling consumer of the *same*
mechanism if the two consumers select different sub-partitions of the
underlying data. Borrowing sibling A's known-good input to test sibling B's
hypothesis conflates two independent variables (the hypothesis, and the
input's validity for B specifically) into one pass/fail result — a blank
render refutes nothing on its own.

Confirmed on Crystals of Arborea (Amiga, `crawl` project): `CAVINT.bin`
("cave interior") reads the same `omaintc(0x7c)` local-scene array as the
outdoor script `ARBRE.bin` ("tree"), indexed by an additive `direct` term
(`omainb(0x2b3c)`) with no writer found in either script's own reached CFG
— structurally, this looked like a shared "layer selector" defaulting to 0
(the outdoor/terrain sub-array). A prior session hypothesized `CAVINT`
might need `direct=1` (a separate, denser "room outline" sub-array found
earlier by a whole-array visual scan) but tested it at `ARBRE`'s own
terrain-cluster test position — the frame came back blank, and the layer-1
guess was marked INCONCLUSIVE, not confirmed or refuted.

A follow-up session disassembled `CAVINT.bin`'s own `cswitch1` cell-value
dispatch directly (rather than reusing FORET/ARBRE's dispatch or a borrowed
position) and got its REAL accepted value set (`{-94..-90, -79..-70,
80..85}`, 21 distinct values). Scanning the layer-0 sub-array for these
values found **zero matches** anywhere in the whole grid; scanning layer 1
found **1,947 matches**, forming real, coherent, closed room/wall outlines.
The layer-1 guess had been right all along — the earlier "inconclusive"
result was caused entirely by testing at a position real only for the
OTHER script's OTHER layer, not by a wrong hypothesis.

**The fix**: when a structural hypothesis about a shared selector produces
a blank/negative result, don't treat that as evidence against the
hypothesis until you've re-derived a test input from the TARGET's own
logic (its own dispatch table, its own accepted value range, its own
consumer code) rather than reusing a sibling's. If the target's own value
alphabet doesn't exist anywhere in the sub-partition the hypothesis
predicts, that IS a real refutation; if it doesn't exist in the
sub-partition the *previous test* used but does exist in the one the
hypothesis actually predicts, the hypothesis was right and the test was
wrong. This is a distinct failure mode from
`individually-failed-fixes-may-combine-cleanly.md` (which is about
confounded fix-axes across separate attempts) — here there was only ever
one axis (the layer), and the "second variable" that needed varying was
the test input's provenance, not another decode parameter.
