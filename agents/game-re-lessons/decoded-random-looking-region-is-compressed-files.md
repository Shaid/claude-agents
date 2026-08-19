# A decoded data region that looks uniformly random is often compressed game files — validate via the file table, not the byte values

**When it bites:** a decoder (decompressor, deswizzler, container
unpacker) produces a large region of uniform high-entropy "garbage", and
the temptation is to conclude the decoder is broken and hunt for a bug —
especially when the *header/boot* part of the same output decoded
perfectly.

A game's bulk asset files (textures, models, audio, stage data) are
routinely stored compressed at rest, and compressed data is
indistinguishable from random by eye or entropy. The region is *supposed*
to look like garbage; the file *boundaries* are the thing to check. The
oracle is the container's own directory — the FST/TOC entries give
offsets and sizes; resolve a handful of file boundaries (e.g. `entry ×
unit` from a directory record) and check the bytes at those exact
positions for a real magic (FCMP/FTEX/etc.), rather than scanning for
plaintext or trusting the byte distribution.

Muramasa (Wii, RVZ): after decoding the decrypted 4.3 GB game-partition
stream, the entire data segment looked random; an `.SSB`/`.MBP` string
scan found only coincidences inside the noise, and ~2 hours were spent
chasing a suspected broken Lagged-Fibonacci junk generator (it was
correct). The real answer: the FST file offsets are in 4-byte units
relative to the partition stream; resolving `bg01b_01.esb`'s entry
(0x367674E5 × 4) landed exactly on a `FCMP` magic — everything was
right, the files are just compressed. The same trap applies whenever
"the file data is plaintext-findable" was true for a sibling title
(e.g. Odin/Grim CVM where AFS magics were visible raw): a different
container/generation can compress its files, making the magic scan fail
without the decoder being wrong.

Fix: before debugging the decoder, parse the directory (FST/TOC) and
resolve real file offsets against the decoded stream. A single correct
file magic at a directory-resolved offset confirms the decoder; a
plaintext/entropy scan cannot.
