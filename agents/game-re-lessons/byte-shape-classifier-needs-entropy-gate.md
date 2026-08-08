# A byte-shape/range classifier needs an entropy gate before it, or all-zero padding wins by default

**When it bites:** you build a soft structural heuristic that classifies a
byte block by checking whether small sub-fields fall inside a plausible
range (e.g. "is this ADPCM-shaped: does the shift nibble read `<=12`, the
predictor nibble `<=4`, the flag byte `<=7`?"), and you're about to trust
its positive hits without checking what the heuristic does on trivial
all-zero or single-byte-repeat data first.

Near-all-zero (or any near-single-value-repeat) data trivially satisfies
almost any "small field, small range" shape test, because zero (or any
low, repeated value) sits inside nearly every plausible numeric range by
construction. Confirmed on Chaos Legion (PS2): a PS-ADPCM byte-shape
classifier (`shift<=12 and predict<=4 and flag<=7` per 16-byte block)
flagged a **known-good plaintext record** (a `"Chaos Legion" 2003.05.08...`
build-stamp string sitting in mostly zero padding) as `adpcm-like` with a
99% match rate — because zero bytes trivially decode to shift=0,
predict=0, flag=0, all inside the accepted range. The false positive
wasn't a fluke of one record: **near-zero-entropy padding is the single
most common byte pattern in any real corpus** (sector-aligned records
routinely pad with zeros), so an ungated shape heuristic will misclassify
a meaningful fraction of *every* corpus's padding as "real" hits.

**Fix: compute entropy (or an equivalent "is this actually varied data"
check) first, and gate the shape heuristic behind it** — `entropy < ~1.0
bit/byte` should short-circuit straight to a `near-empty`/padding class
before the shape test ever runs. On the Chaos Legion corpus, adding this
gate moved 218 tiny near-zero-entropy entries out of the `adpcm-like`
bucket into their own `near-empty` class, with zero change to the
byte-total of genuinely-shaped hits — i.e. the gate cost nothing on real
positives and fixed every false positive.

This generalizes past ADPCM: any "does field X fall in plausible range
[0,N]" classifier (compression-tag bytes, opcode ranges, palette-index
bounds, struct-field sanity checks) is vulnerable the same way whenever
zero is a valid value inside the accepted range — which is nearly always.
Always check what your shape heuristic reports on a deliberately
constructed all-zero input before trusting its corpus-wide positive rate.
