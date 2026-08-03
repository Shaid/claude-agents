# A distinctive fixed table's byte pattern can anchor a whole chain of undocumented addresses

**When it bites:** you need the real address of one or more static data
tables in a binary and don't want to (or can't fully) trust a reference
project's declared address for them — its rip-list/JSON might be stale,
might describe a different build, or you simply want an address derived
from *this* binary's own bytes rather than copied from someone else's
claim — and a disassembly's debug/local labels for the tables in question
look like plausible offsets but haven't been independently checked.

Confirmed on FFVI (SNES, `ceres`): needed the real HiROM address of five
sequential tables (`TopSpriteHFlip`, `BtmSpriteHFlip`,
`MapSpriteTileOffsets`, and two object-pointer arrays) that a community
disassembly declared only as small local labels (`@cd3a:`, `@cdba:`, ...)
with no stated absolute address. Rather than trust the label text as an
address (a documented trap elsewhere — see
`file-offsets-vs-segment-relative.md`), one of the tables
(`TopSpriteHFlip`) has an extremely bit-sparse, distinctive fixed
byte pattern: 64 zero bytes followed by 64 bytes all equal to `0x40`. A
raw byte-string search for that exact 128-byte pattern across the entire
3 MB ROM produced **exactly one match**. That match's file offset,
converted to a HiROM CPU address, was then cross-checked two ways: it
matched the disassembly's own debug label for the same table numerically
(`0xCD3A`), and it landed exactly one byte past the community's
independently-documented end of the preceding code region (a bank
boundary claimed in unrelated prose, `C00000-C0CD39`) — two agreements
from two unrelated sources, neither of which was the address search
itself. Every subsequent table's address then fell out by simple
arithmetic (`anchor + confirmed_size_of_each_intervening_table`), each
step re-checked against that table's own debug label. The final address
chain was validated end-to-end by reading the *last* table in the chain
(an object-pointer array) and diffing 19 of its resolved pointers
byte-exact against the reference project's own independently-published
values — a confirmation that didn't depend on trusting either the
anchor-search or the reference project alone, since it required both to
agree.

**The general technique:** when you need an anchor address for a family of
sequentially-laid-out static tables and don't want to lean on a single
unverified source, look for the *most bit-sparse or structurally
distinctive* fixed-content table in the same source file/region (long runs
of a repeated byte, a sharply bimodal pattern, anything far from generic
code/text entropy) and byte-search the target binary for its exact
content. A single, unique whole-binary match is strong evidence you've
found the real address, especially when it can be cross-checked against
*two* independent pieces of context (a disassembly's own debug label, a
separately-documented bank/region boundary, a reference project's declared
size). From that one anchor, every other same-file table's address is
pure arithmetic — size of table N gives the start of table N+1 — with each
arithmetic step itself checkable against a debug label if one exists. This
is strictly more self-contained than trusting a reference project's own
rip-list/JSON coordinates outright, and considerably cheaper than tracing
every intervening instruction by hand.