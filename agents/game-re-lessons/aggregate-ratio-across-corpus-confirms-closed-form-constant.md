# A weak per-instance tolerance fit can still be a strong aggregate confirmation of a closed-form constant

**When it bites:** a candidate formula for a fixed-point/integer table
(`table[i] = round(base · k^i)`, a geometric/exponential progression, a
trig-table lookup) checks out only loosely per individual entry — a tight
per-value tolerance (±1, ±2 units) passes on a minority of entries, tempting
"the formula is roughly right but something else is going on" or outright
rejection — while the *real* underlying constant `k` is a well-known
closed-form value (2^(1/12), π, a hardware clock ratio) that the noisy
per-instance data should reveal if averaged rather than spot-checked.

Confirmed on Final Fantasy VII (PSX field-BGM instrument bank,
`SOUND/INSTR.DAT`, `siren` project): a 12-entry `u32` table per instrument
record was hypothesized as a chromatic (semitone) SPU pitch-register lookup,
`table[i] = round(table[0] · 2^(i/12))`. Per-entry fit against this formula
at a tight tolerance was unconvincing — only ~52% of entries matched within
±1 unit, ~79% within ±2 — which would normally read as "close but probably
wrong, or a different formula entirely." But computing the **aggregate
geometric ratio** `(table[11] / table[0])^(1/11)` for every one of the 93
real records and averaging across the whole corpus gave **1.059458**,
against the mathematically exact 2^(1/12) = **1.059463** — a 5-part-per-
million match. The per-entry "misses" were small, roughly symmetric
rounding noise from the original 1996 authoring tool's own (coarser)
computation, not evidence of a wrong formula — per-entry fit converged to
99.9% once the tolerance was widened to ≤1% relative error (±16 units on
values in the thousands), which is the number that should have been checked
first.

**Why this happens:** a tight *absolute* per-entry tolerance is the wrong
statistic when the noise is small-and-roughly-i.i.d. per entry but the
formula spans many entries (each one compounds a `^i` exponent) — individual
rounding errors don't cancel across one instance's own 12-entry table, but
they DO cancel in expectation across many *independent* instances' analogous
ratios. A per-instance geometric-mean ratio is a much lower-variance
estimator of the true multiplicative constant than any single `table[i]`
value is.

**Fix:** when a candidate exponential/geometric-progression formula's
per-entry tolerance check is unconvincing but not obviously wrong (noise
looks roughly symmetric, not systematically biased), compute the implied
constant per instance (e.g. `(last/first)^(1/steps)` for a geometric
series, or an analogous per-instance regression for other closed forms) and
average it across the whole corpus before giving up on the formula. Compare
the result against the exact closed-form value to full float precision —
matching to several significant figures is decisive; matching "in the right
ballpark" is not. Corroborate independently where possible: a literal,
well-documented hardware/domain constant appearing verbatim as one
instance's own base value (here, the PSX SPU's literal `0x1000` "unity
pitch" register constant, found byte-identical across a smaller sibling
sub-bank) and an unrelated already-decoded field's value *range* exactly
matching the table's own length (here, a note-decode field's confirmed
`[0, 11]` range matching the 12-entry table with no rescaling) are two more
independent lines of evidence pointing the same way — three independently-
derived confirmations converging is a much stronger bar than any one alone.
