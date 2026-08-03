# Compressed streams may not start where the directory ends

**When it bites:** output looks "scrambled" right after what seemed like a clean directory/header parse — or, for prefix-free/variable-length bit codes (Huffman, LZ-style bit-tree walks) specifically, when a candidate start offset produces a mix of clearly-real legible fragments *and* garbage on the same record, rather than either clean output or total noise.

A 214-byte raw table sat between the directory and the RLE stream in one
format; decoding from the directory's end desynced everything and looked
exactly like a bitplane-alignment bug. If output is scrambled, suspect the
stream start offset before you suspect the pixel layout.

**Prefix-free bit codes specifically self-resynchronize, which can make a
wrong start offset look like it's "mostly working."** Decoding a Huffman
bitstream from a slightly-wrong bit or byte position doesn't reliably
produce pure noise — the tree walk can coincidentally land back on a real
code boundary a few symbols in and decode correctly from there until the
next desync, then resync again later. Confirmed in Wizardry 6 (Amiga)
`msg.dbs`: decoding straight from the wrong offset (`msg.hdr` field A,
which turned out to be an unrelated lookup key, not a stream position)
produced ~99% printable-ASCII output with genuinely correct 7+ character
English words (`CHEMIST`) embedded in otherwise garbled text — a
misleadingly strong signal that the *offset*, not just the tree/algorithm,
was still wrong. The tell that finally separated "right tree, wrong start"
from "actually correct": test several small offset perturbations (±1-2
bytes, ±1-7 bits) on the *same* record and watch whether legible content
before a fixed decoded-length cutoff stays fully clean edge-to-edge at
exactly one perturbation and stays garbled-at-the-edges at every other —
a truly correct offset has zero garbage anywhere in-bounds, not just "more
real words than the alternatives." Don't accept "mostly legible, some
garbage" as confirmation for this class of codec; treat any garbage at all
as evidence the start position (or a skipped header byte before the
bitstream — the actual bug here, a second undocumented length-adjacent
byte) is still wrong, and keep perturbing until it's edge-to-edge clean.
