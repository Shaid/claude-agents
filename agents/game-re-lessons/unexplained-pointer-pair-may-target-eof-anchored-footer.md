# An unexplained header field pair that "looks like a pointer, 20 bytes apart from a second one" may target a trailing footer at EOF, not anything near the header itself

**When it bites:** a leading header has two `u32` fields whose values
differ per file but are always a small constant offset apart from each
other (e.g. always exactly 20 apart), previously logged as "consistent
with a pointer/size pair, though which wasn't determined" or similarly
shelved as low-priority/unexplained — especially inside a container whose
main payload is a self-describing chain (each block's own `size` field
points at the next block, so nothing in the format *needs* an external
directory to be walked).

Two candidate offset-shaped fields with no obvious target near the start
of the file are easy to file away as "some kind of pointer, not worth
chasing" — there's nothing at their literal byte values that looks like
useful data when you jump there naively if you're checking against the
wrong base, and a self-describing chain payload doesn't obviously need any
directory at all, so the assumption becomes "leftover/unused metadata."
Before shelving it: test whether the field(s) resolve against **the end of
the file**, not the start. Compute `decompressedSize - field` (or
`decompressedSize - field - knownConstant`) for every sample in the corpus
and check whether it lands on a suspiciously round or exactly-repeating
value (zero deviation, not "close"). A trailing footer/directory anchored
to EOF — appended *after* a self-describing chain that doesn't itself need
one — is a real, recurring container shape: it lets an offline tool that
already streamed through the whole chain once (to compute its total
length) append per-object metadata (counts, placement tables, LOD/
parameter blocks) without needing to know that metadata's size *before*
laying out the chain.

Confirmed on Fire Emblem: Three Houses' `.kldm` map-prop model containers
(`chimera` project, `fe3h-kldm-header`). An earlier pass found the leading
header's bytes 8-12/12-16 were "always exactly 20 apart" but couldn't
place what they pointed at, and separately found bytes 16-20 as "a small
round-ish `u32`... could plausibly be a per-object byte-length" without
connecting the two. Testing `decompressedSize - field(@8) == field(@16) +
20` across the full 29-entry corpus closed **exactly, 0 deviation, in
every sample** — the two fields are a `{offset, offset+20}` pair pointing
to a trailing footer whose length is the third field, sitting at the very
end of the file, well past the entire `_M1G` model chain. The first 20
bytes at that footer offset turned out to be a **literal second copy of
the file's own leading tag** (`"PADD" "MDLK0001" \0\0\0\0 "PADD"`,
byte-identical to the file's own opening bytes), immediately followed by a
nested nested `{count, (ptr,size)[count]}` sub-container — the same
section-pointer-table convention already confirmed elsewhere in this
project's PACK/gamedata formats, just appearing again in a completely
different, previously-unexamined corner of the format. Recognizing the
EOF-relative arithmetic is what turned two shelved "unexplained pointer"
fields into a fully-resolved footer discovery in one pass, where five
files' worth of eyeballing raw hex bytes at the header's own start had
gone nowhere.
