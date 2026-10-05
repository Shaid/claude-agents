# A disk/binary region no traced code path reads is not evidence it's filler — run a plain strings scan before more structural work

**When it bites:** a static loader-chain trace has enumerated every disk
read a game's boot/mini-loader/dispatch code issues, and a sizeable region
(tens to hundreds of KB) falls outside all of them — the instinct is to
label it padding, protection-tool template residue, or "not yet reached by
this session's tracing" and move on to structural/statistical techniques
(entropy maps, bitplane-shape censuses, audio oracles) applied elsewhere.

"No traced reader reaches it yet" is a fact about how much of the loader
chain has been traced, not a fact about the region's content. A region can
be entirely real, human-authored content reached by a *dynamic* reader
(one whose target address is data-driven, not a literal operand a
whole-binary census can find) that just hasn't been traced to this region
specifically. The cheapest test for "is this actually inert" is a plain
ASCII strings scan (`[\x20-\x7e]{5,}` or equivalent) — near-zero cost,
and decisive when it hits: real menu labels, dialogue, or (as below)
multiple parallel language blocks are direct proof of human-authored
content, settling the question without any further structural work.

Confirmed on Deuteros (Amiga, `methanoid`): the ~372 KB gap between the
title picture (Disk.1+0x13400) and the giant track-80 payload
(Disk.1+0x6E000) had no traced loader read reaching it after several
sessions of boot-chain tracing, and an earlier pass's structural read of a
*different*, smaller repeating-record region nearby had already floated
"protection-tool template padding" as a working hypothesis for
superficially similar unexplained space. A plain strings scan of the gap
in a later session found 2,794 printable-ASCII runs forming a genuine,
extensive multi-language (French + German, each preceded by its own
`@1991 i.r.bird v1 (<language>)` version tag) UI/menu string table — real
game content, not filler, hiding in exactly the kind of region a
"no reader found it yet" framing would otherwise write off. The scan cost
one line of Python against an already-in-hand file; the entropy map and
audio-oracle sweep that also touched this region (a separate, valid line
of investigation) would not have found the text on their own since the
region's bulk byte content is genuinely non-text (interleaved audio-shaped
data, ~5-25% of each sub-region by byte count is the text itself).
