# An exact formula OR a "0 exceptions" invariant claim can pass 100% on a small sample while a conditional/edge-case term hides in the majority

**When it bites:** a doc claims an arithmetic relationship between two
already-decoded fields (`fieldB == f(fieldA)`, e.g. "the next chained
block's offset equals this payload's end") — or, more broadly, ANY
"N/N, 0 exceptions" structural/coverage claim (a boolean invariant like
"always unscaled", "never has flag X set") — backed by a small sample
(single digits to ~10, or a handful of hand-picked files/slots) that all
passed, and you're either about to trust that claim at full-corpus scale,
or you're re-auditing it and the naive claim is failing on some fraction
of real records in a way that looks like noise rather than a bug. A
systematic way to *find* candidates for this audit, rather than stumbling
on one: grep the whole doc tree for phrasings like "checked on N", "N
samples", "verified (on|against) N", "across N slots/bundles/rooms" — any
small, single-digit-to-low-hundreds N attached to a confirmed/checked/
verified claim is a candidate, whether or not the doc explicitly flags it
as a sample.

## What happened

Confirmed on Valkyrie Profile (PSX, `valkyrie`)'s "SLZ" compression
container. The format doc claimed `chainStride == 16 + compressedSize`
"whenever nonzero... checked directly against the next real SLZ hit's
offset for 10 samples — exact in every case." A full-corpus rigor audit
(round 209) re-ran the production magic scanner and checked the formula
against **every** real chained block on both discs (2,649 total, not 10):
it held for only **24%** of them. For the other 76%, `chainStride` was 1,
2, or 3 bytes *larger* than the naive formula predicted.

The real rule, holding with zero exceptions across all 2,649 chained
blocks (and, more broadly, all 26,911 SLZ headers on either disc): every
header's absolute file offset is a multiple of 4, and `chainStride` rounds
`16 + compressedSize` **up** to the next 4-byte boundary (`align4(n) = (n+3)
& ~3`) — 0-3 pad bytes are appended after each compressed payload before
the next chained header. The original 10-sample check passed 10/10 purely
because none of those 10 samples happened to land on a `compressedSize`
that needed padding — a coin that landed heads 10 times running out of
sheer bad luck, not because the coin is fair.

## Why this is a distinct trap from a plain small-sample undercount

`small-sample-probe-undercounts-dominant-subformat.md` is about a
*presence/prevalence* claim ("does feature X exist, how common is it")
missing the dominant case. This is about an *exact arithmetic formula*
between two fields that already decode correctly individually — the
formula genuinely holds on every sampled record, so there's no obvious
"this looks wrong" tell in the sample itself. The failure mode is
specifically a **conditional correction term** (rounding, alignment
padding, a rare extra field) that only manifests for *some* records and
is invisible unless the sample happens to include one that needs it. A
small sample of a binary (needs-padding / doesn't-need-padding) condition
can easily draw all-same-outcome runs by chance — 10 independent 50/50-ish
draws landing all one way isn't even that improbable (here the real split
was closer to 24/76, making an all-pass run of 10 roughly 1-in-1,400, rare
but far from impossible, and nobody had run the numbers before trusting it).

## The fix

- Don't accept "confirmed exact, N/N samples" for an inter-field formula
  as settled once N is single digits to low tens — re-run it against the
  **whole population** the fields' own container/scanner can enumerate
  (here, every block the magic scanner finds, not a hand-picked run).
- When the full-population check fails for a nonzero-but-not-all fraction,
  don't file it as noise or a decode bug — **compute and histogram the
  per-record delta** between the naive formula's prediction and the real
  value. A tight, small-integer-only histogram (here: exactly `{0, 1, 2,
  3}`, no other values) is the signature of a rounding/alignment term, not
  random corruption. Then test the obvious alignment hypothesis directly
  (`realValue % N == 0` for the smallest plausible `N`) before doing
  anything more elaborate — it settled this case in one follow-up probe.
- Once the corrected formula is found, keep the *original* formula's
  citation in the doc as a `> Correction` block rather than silently
  editing the number away — a formula that "was confirmed 10/10" and later
  turns out to only be right 24% of the time is itself a fact worth a
  future reader knowing, especially since it's evidence that this
  project's earlier verification passes sometimes treated "checked a
  handful of samples by hand" as equivalent to "checked structurally,"
  which is exactly the class of gap a periodic rigor-audit series exists
  to catch (see `game-re.md`'s Method § 7 "Re-audit, periodically").

## A second instance: a "0 in the wild" coverage claim, not an arithmetic formula

Confirmed on the same project, one round later (VP1 PSX round 210, applying
the search technique above systematically for the first time rather than
auditing one claim at a time). `data-structure.md`'s field-sprite part
renderer table claimed, across 4 hand-picked dungeon slots (3,136 parts):
`w2 == w && h2 == h` ("unscaled") 3136/3136, and "parts with the free-quad
flag set: 0". The renderer's own disassembled dispatch shows this table's
population takes the *fast* path specifically — a slower "general path"
exists in the real code for wrong-layer, scaled, and free-quad parts, none
of which happened to occur in these 4 slots. A full-corpus re-walk (both
discs, every real record block, 113,908 parts) found the free-quad
prevalence was already known corpus-wide from a *different* doc section
(12,125/113,908, 10.6%) — so that "0" was already understood as
sample-scoped, not a live misconception — but the "unscaled" claim had
never been re-checked past the same 4-slot sample anywhere in the repo,
and turned out to have **3,224 real exceptions** (2.8% of all parts, a
genuine authored stretch, not decode noise — deltas cluster at ±1-2px).
This is the same trap as the `chainStride` case above but with no
arithmetic formula at all — it's a plain boolean invariant over a small,
non-random sample (four dungeon slots, not a random draw), and the fix is
identical: re-walk the real population with the production parser before
trusting a "0/N" or "N/N" table row, especially one whose own surrounding
prose (here, the renderer disassembly two paragraphs above the table)
already names the specific alternate code path the sample happened not to
exercise.
