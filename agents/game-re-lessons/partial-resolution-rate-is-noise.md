# A partial resolution rate against a reference corpus is noise, not partial success

**When it bites:** a decoded id/index field resolves to a real entry in a
reference corpus (resource ids, string table, tile bank, sprite catalogue) for
only *some* fraction of records — roughly 40-70% — and you're about to explain
the residue as a second id space, another resource class, or a dispatch path
you haven't mapped per-entry yet.

A partial match rate is not a partially-solved field. It is usually the
signature of a **whole-field transform you haven't applied** — the field is
100% wrong and merely lands on valid ids by chance.

**Compute what chance would give you before calling a partial rate progress.**
Vengeance of Excalibur's `SCEN` object entries carry a 10-bit `refId` biased to
the range 800-1823 (1024 reachable values). 354 of those 1024 values are real
`IMAG` resource ids — so **34.6% of the reachable id space is valid by
construction**, and real data clusters into the populated banks, which pushes a
purely-wrong reading well past that. The observed 51.7% (2538/4911) was the
same order of magnitude as chance, and was read for a long time as "about half
the entries are IMAGs, the rest are something else." With the missing transform
applied it went to **4911/4911 = 100%**.

## The trap is having a real mechanism to hang the residue on

`_DrawScenePiece` genuinely contained a code-traced three-way dispatch
(`_OpenFrml` / `_OpenImag` / a door-rectangle table). That made "the other 48%
resolve through the FRML path" feel like a complete story, and it survived in
the docs as a confirmed mechanism with an unmapped consequence.

**The test is to score the mechanism corpus-wide, not to note that it exists.**
When finally scored, classifying by the (untransformed) dispatch key sent 3075
entries down the FRML path of which exactly **4** named a real FRML resource.
A mechanism that makes the numbers *worse* is not an explanation. If you cannot
state your candidate rule's corpus-wide resolution rate as a number, you have a
story, not a finding.

## The tell: a constant table whose tail is repeated filler

`_aCharFlags`, the 16-entry byte table the dispatch key indexes, was
`[0x00, 0x02, 0x10, 0x12, 0x04, 0x08, 0x20, 0x42, 0x62]` followed by **seven
identical `0x36` bytes** — obvious filler padding a 9-value table out to a
power-of-two index. Under the wrong reading, 2772 of 4911 entries indexed into
that filler region.

**A constant table with a repeated-filler tail is a free validity oracle for
whatever indexes it.** Real data should never routinely land in the filler; if
it does, the field extraction is wrong. Costs nothing, needs no external ground
truth, and here it was what pointed back at the loader. Look for this shape
(a lookup table sized to a power of two but meaningfully populated only up to
some smaller N) in any table your decode indexes.

## A higher match rate from a wider search is the same trap, just quantified

Re-running the baseline-percentage check after a *systematic* brute-force
search (many bit-widths × many bias constants) doesn't buy immunity —
Conan the Cimmerian's own `SCEN.refId` field (a different game in this same
project) was re-searched this way and found a "better" 9-bit/`bias=1044`
fit at 91.7%, tempting to log as progress over an earlier 73-78%. Computing
the *specific* chance baseline for the id window that bias selects (not a
generic corpus-wide percentage) put it at 43.2% — the search had simply
found the densest sub-range of a non-uniformly-distributed id corpus, not a
better field decode. **A second, cheap, independent check catches this even
when the baseline math is subtle: look at how matches are distributed
across the resolved ids, not just the aggregate rate.** In this case a
single id absorbed 12.9% of *all* 6,541 entries in the corpus — wildly
implausible for a real per-object reference field, where usage should
spread across many distinct ids. A wide brute-force search over many free
parameters (bit-width, bias, byte order) is *more*, not less, susceptible
to this trap than a single hand-derived hypothesis, because it actively
hunts for whichever parameter combination lands in the densest region of
the id space.

## The usual cause: an in-place fixup inside the loader

Before trusting stored bytes, check the loader for a transform applied to the
buffer *after* the read and *before* the consumer sees it. Byte-order fixups,
endian swaps, relocation, in-place decompression and index rebasing all live in
that gap.

These are easy to skim past because they are typically **gated on a "was this
freshly read from disk, or a cache hit?" flag** — which makes a universal,
once-per-load fixup look like a rare conditional. Vengeance's `_LoadScene`
reverses all four bytes of every one of the `(count + 1)` entry longwords in
place (`ExcalII.asm:42224-42262`), gated on a flag the resource loader sets
only when it actually hit the disk. Read as a conditional it looks skippable;
in practice it always runs exactly once.

On 68k, the canonical longword byte-reverse idiom to grep a loader for is
`AND.L #$00ff0000` / `AND.L #$0000ff00` combined with `LSR.L`/`ASL.L` of 8 and
24 and `OR.L`. The same engine family (Melbourne House Excalibur games) carries
it in both Vengeance's and Spirit's `_LoadScene` — applying it took Spirit's
own id resolution from 24.2% to 99.9%.

## Check every field, not just the suspicious one

A wrong whole-field transform corrupts *all* the fields in the record, and the
other ones are usually cheaper to falsify. Under the wrong byte order, the same
Vengeance record's `paletteSelector` took values 22-59 and indexed a palette
table to PALT ids 57/75/84 — **none of which exist** in the game's own
`PALETTE.RES`; with the fixup it takes values 0-12 and every one maps to a real
PALT. A third check (object bounding boxes against the 320x200 screen) went
from 460 of 914 entries entirely off-screen to **1 of 4431**.

One wrong-looking field is easy to rationalise as an unmapped special case.
Three independent fields each failing their own oracle is a decode that is
wrong. When a record has several fields, score them all before writing up any
of them as confirmed.
