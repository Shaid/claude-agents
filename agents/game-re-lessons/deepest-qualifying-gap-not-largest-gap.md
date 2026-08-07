# Algorithmically generalizing a by-eye "clean natural gap" threshold: take the deepest qualifying gap, not the single largest one

**When it bites:** turning a human's one-off "eyeballed a ratio/score
distribution and picked a clean natural gap as the cutoff" judgment call
(bone-overlap ratio, similarity score, any 1-D ranking with a real
bimodal-ish split) into a reusable algorithm that has to run unattended
across many distributions, not just the one that was eyeballed.

The naive translation — "find the two adjacent sorted values with the
largest difference, cut there" — is wrong whenever the distribution has a
small, high-value cluster with one near-perfect outlier sitting a hair
below it. Confirmed on Drakengard 3 (`flower` project,
`docs/drakengard3/ps3/data-structure.md` §18, generalizing §17's
by-hand AnimSet-matching threshold): the real corpus had 65 candidates
tied at ratio 1.0, one lone candidate at 0.9938, then 90 candidates at
0.8634 (the single richest, most valuable band — a 521-sequence general
moveset), then a real character boundary at 0.7391. The single largest
gap in that list is between 0.9938 and 0.8634 (0.130), not between 0.8634
and 0.7391 (0.124) — naively cutting at the largest gap would have
excluded the entire 90-candidate valuable band over one meaningless
0.0062-wide anomaly at the very top.

**Fix**: scan the sorted distribution top-down, and keep the *deepest*
(lowest-value, most-inclusive) gap that still clears a minimum-size floor
— not simply the largest gap found anywhere. Overwrite a "best gap so far"
candidate every time a later, still-qualifying gap is found; the last
value written wins. Pick the minimum-size floor from the domain's own
granularity (e.g. scale it by `1/N` where `N` is the number of discrete
units the ratio is computed over, so a coarse low-N distribution needs a
proportionally bigger gap than a fine high-N one) rather than a single
fixed constant. Verify the algorithm against the exact real distribution
that was originally eyeballed by hand — reproducing that known-good cutoff
is the cheapest available oracle before trusting the algorithm on new,
unseen distributions.
