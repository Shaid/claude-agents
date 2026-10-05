# A sequential block-chain walker silently truncates at the first block magic it doesn't know — check walked-vs-declared count per file, not just "did it parse"

**When it bites:** a container is walked by chaining `offset += blockSize`
from block to block, your walker accepts one magic, and most files parse
cleanly with no error. Especially when the corpus is large enough that you
sample a few files, see them come out perfect, and publish a whole-corpus
figure. Also bites when a per-file "declared count" field exists and you
have not compared it to what you actually walked.

## What went wrong

FE Warriors: Three Hopes' `KOD` object database (`_DOK0000`, 4,952
resources, `chimera`). A first walker accepted `IDOK0000` blocks and
advanced by `align4(blockSize)`. It looked healthy: **4,632 of 4,952 files
walked perfectly**, block-value sections tiled with zero slack, property
names resolved, real resource references came out type-homogeneous. Every
qualitative check passed.

The container also uses a second magic, `RDOK0000` — 75,158 of the 560,408
blocks, interleaved with the objects rather than grouped. A walker that
stops on an unrecognised magic therefore *terminated early* on the other
320 files, and terminating early is indistinguishable from finishing when
the loop's exit condition is "magic didn't match". One file walked 142 of
its 1,943 blocks and reported success.

Two things made this cheap to catch once looked for:

1. **The header's declared count covers every block kind.** Comparing
   `blocksWalked == header.blockCount` **and** `lastBlockEnd == payloadLength`
   per file immediately isolated the 320. Summing across the corpus,
   485,250 `IDOK` + 75,158 `RDOK` = 560,408 = the exact sum of every file's
   declared count — a zero-deviation invariant that the truncating walker
   could never satisfy.
2. **The sibling block was the same record shape.** `RDOK0000` carries
   `{size, instanceId, classKtid, <one extra u32>, propertyCount}` — one
   header word more than `IDOK0000`, then identical property headers and an
   identically-packed value section. Once accepted, it needed no second
   decoder, just a per-magic header width.

## The fix

- A chained walk's stop condition must distinguish **"reached the end"**
  from **"hit something I don't understand"**. Treat an unknown magic as an
  error to report, never as a loop exit.
- Validate every file against the container's own count/length fields:
  `blocksWalked == declaredCount` and `lastBlockEnd == payloadLength`.
  Publish the corpus-wide agreement (here 4,952/4,952) as the coverage
  claim, not "N files parsed without throwing".
- When a sibling magic turns up, diff its header against the known one
  before assuming a new format — a one-word difference in an otherwise
  identical record is the common case (compare
  `sibling-magic-may-be-same-struct-zeroed-field.md`).

Distinct from `first-subentry-only-check-misses-later-recurring-magic.md`
(that one is about ruling a format *out* after checking a single position)
and from `shallow-magic-scan-undercounts-sibling-magic-corpus.md` (raw
byte-scan population counting). This one is about a *structured walk* that
is doing everything right and still stops two-thirds of the way through a
file while reporting success.

## Variant: the walk can't even self-validate when one sibling block family carries no length field

Reunion (Amiga OCS/ECS floppy, `methanoid`)'s Disks 1-5 hold three sibling
block families (`2AM`/`1AM`, both length-prefixed, and `AMN`, which has no
on-disk length header at all). A sequential `offset += blockSize` chain
walk worked fine while it only met `2AM`/`1AM` blocks, but had no way to
skip past the first `AMN` block it met — nothing in the block itself says
how long it is — so it silently stalled there for the rest of that disk.
Unlike the KOD case above, there was no declared-count field to validate
against either, so the "walked vs declared" check this file recommends
wasn't available as a fix. The per-disk statistics derived from the
stalled walk were significantly wrong as a result (one disk's real
`2AM`/`1AM` split was more than double the walk's count on both families),
and the error was only caught by an unrelated agent doing a bounded,
read-only cross-check in passing.

The real fix was orthogonal to the walk itself: a separate, independently
discovered catalog (an installer's own asset table, giving each entry's
exact decompressed length and its block's disk+offset) gave ground truth
per block without needing to walk the chain at all. **When a
self-describing catalog/index with per-entry exact sizes exists elsewhere
in the corpus, prefer it over any sequential/chain-derived census** —
especially once you know one block family in the chain has no length field
of its own, which makes the chain walk structurally unable to
self-validate the way the count-check fix above requires.
