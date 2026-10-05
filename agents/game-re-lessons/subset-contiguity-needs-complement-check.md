# "Byte-contiguous when sorted" on a small subset is not evidence of a real region unless the complement is checked too

**When it bites:** a structural investigation isolates a subset of entries
(a directory's non-participating rows, an "unclassified" bucket, entries
sharing some flag value) — typically well under a few hundred out of a much
larger corpus — sorts them by offset, and finds most of them byte-contiguous
or near-contiguous with their neighbors in the subset. This is tempting to
read as "these form one hidden contiguous region/block," especially when it
would tidily explain an otherwise-unaddressed field.

Confirmed refuted on Valkyrie Profile 2 (PS2)'s TOC `unused` field
investigation. 165 TOC entries were classified "non-participating" (excluding
an already-solved 10-entry FMV block). Sorting the remaining 164 by offset
found 159/164 adjacent pairs byte-contiguous — strong-looking evidence of a
second hidden mega-block. The hypothesis was refuted by checking the
*complement*: 2,683 of the 2,685 already-known, unrelated *participating*
entries also fell inside that exact same byte-offset span. The disc is so
densely packed end-to-end with unrelated content that **any** sparse ~165-
entry subset scattered across it will look locally contiguous almost
everywhere by chance — the "contiguity" measured nothing about the subset
being special, only that the subset was small relative to a corpus with
almost no gaps at all.

**The general test:** a "sorted subset looks contiguous" result is only
evidence of a real boundary/region if entries **outside** the subset are
shown to *not* fall inside the same span (or fall inside it at a much lower
rate than their overall density would predict). Compute the same
contiguity/overlap statistic for a broader population (ideally the
complement, or a random sample of the same size drawn from the whole corpus)
before trusting the subset's contiguity as a discovery. A subset's sparsity
relative to a dense whole is, on its own, enough to manufacture a spuriously
clean-looking contiguous run — the smaller the subset relative to the corpus,
the more likely a spurious high contiguity rate becomes, which is exactly
backwards from how confident the raw statistic makes the finding look.

This is a distinct failure mode from `deepest-qualifying-gap-not-largest-
gap.md` (a human threshold turned into an unattended cutoff) and
`sparse-sample-flatness-heuristic-false-negative-on-real-content.md` (a
too-small pixel/byte sample missing real content) — here the sample size
itself is fine for what it measures directly, but the statistic computed
over it (contiguity/overlap) has no null-control baseline, so it can't
distinguish "these entries are structurally related" from "any small
scattered subset of a dense corpus looks like this."
