# Two independent strict structural matches can both verify against ground truth from overlapping byte ranges

**When it bites:** a structural scan (or any offset-hunting technique) finds two candidate record placements whose declared byte extents overlap, and decoding *either* one independently reproduces recognisable, externally-confirmed content.

Normally a strict, low-false-positive structural test (an exact padding-index
bit pattern held constant across every row of every plane, not a fuzzy
"looks constant" test) plus an external ground-truth match (silhouette
agreement against a third-party port) is enough to call a record confirmed.
It is not automatically enough to also confirm its *framing* is unique: in
Black Crypt/crawl's `bcdfa` UI panel bank, two different offsets 280 bytes
apart both passed a strict test pinned to their own distinct exact padding
pattern (one to backdrop index 33, the other to index 2), and both
independently reconstructed the *same* DOS port master image at ~99.36%
silhouette agreement — yet their declared 1,680-byte extents overlap, which
is mathematically impossible for two independent full-size records at those
exact offsets.

Do not resolve this by picking whichever one "looks more confirmed" or by
silently dropping one — record both candidates and the overlap explicitly as
an open sub-question (a second real colour/state variant stored nearby vs. a
scan artifact from re-reading the same bytes one bitplane later, which can
still decode to a recognisable if mis-recoloured image — see
`round-looking-longwords-are-centred-bitmap-rows.md`'s family of "a
misaligned read can still look clean" traps). The fix is to find a code
reference (e.g. a per-slot "which template" selector) before trusting either
offset as the true framing, not to pick one from the pixel evidence alone.
