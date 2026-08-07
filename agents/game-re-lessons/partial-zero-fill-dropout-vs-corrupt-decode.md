# A large, sector-aligned zero-fill *inside* an otherwise-healthy file is a disc-read/rip artifact, not corrupt game data — cross-reference an independent second copy to prove it

**When it bites:** a decoder fails on one specific file out of a large,
otherwise-clean corpus (a zlib/compression error, a bad magic, a header
field that doesn't parse) and the file is *not* fully all-zero (ruling out
the far more common "shipped-as-cut-content stub" explanation — see
`all-zero-stub-file-inflates-failure-count.md`), but a byte scan shows a
large contiguous run of zero bytes *somewhere inside it*, especially with
suspiciously round start/end offsets (page/sector-aligned: `0x1000`,
`0x30000`, exactly 4096 bytes, etc.).

Confirmed twice in the same session on Drakengard 3 (PS3, `flower`
project, `docs/drakengard3/ps3/data-structure.md` §8/§14): a UE3 package
(`BG41_SND_20_SOUND.XXX`) failing umodel's zlib decompress with a specific
compressed-block-size mismatch, and two `COOKEDSOUND` SCD audio files
missing their `SEDBSSCF` magic entirely. In both cases the file's disc-dump
copy had a large contiguous zero-fill run at a round offset (192,512 bytes
from `0x1000` to `0x30000` in the first case; exactly one 4096-byte page in
the second), bookended by real, varied, non-zero data on both sides — the
classic shape a drive/rip tool produces when it can't read a run of
physical sectors and substitutes zero-fill rather than failing the whole
read.

**The decisive test, not a guess from the byte pattern alone**: this
project already had a second, independently-sourced copy of the same
logical file — a PSN digital-pkg build of the base game, decrypted via
the project's own PKG tooling, packaged completely separately from the
physical disc dump. Diffing the two copies byte-for-byte showed the
zero-fill region was **the only difference** — every byte outside it
matched exactly, and the PSN pkg's copy decoded perfectly (confirmed both
structurally, by re-running this project's own parser, and independently,
by running the target game's own decoder — umodel — against a directory
containing only the alternate copy). This is what actually proves "disc
read defect in this one distribution" rather than "genuinely bad/degraded
source data common to both" or "my decoder's byte-offset math is wrong" —
a byte-pattern match to "looks sector-aligned" is suggestive but not
proof on its own.

**Where to find a second copy when one exists**: any project with more
than one *independently packaged* source for the same content — a PSN/
digital release alongside a physical disc dump, two different regional
releases, a patch/update pkg that re-ships an unchanged file, a sibling
platform port — is a candidate oracle for this specific failure class,
even if that second source isn't the project's primary/preferred data
path for anything else. Don't dismiss a secondary data source as "already
solved, not on the critical path" without checking whether it can serve
as ground truth for isolated single-file weirdness in the primary source.

**Don't force a pipeline fix for a single-file disc defect** unless the
recovered content is actually needed — recovering the file (re-extract
from the second source, feed to the existing decoder) is usually cheap to
*prove*, but wiring a permanent cross-container fallback into the
pipeline for one file out of thousands is a real complexity cost for a
0.1%-scale gain; document the root cause and the proven recovery path,
and leave the wiring for whenever (if ever) that specific content is
actually wanted.
