# Cross-platform ports are decode oracles — for code too, not just data

**When it bites:** you're stuck decoding a format or tracing a symbol-less caller, and another platform's port, a sibling game, or a sibling RE repo already has that piece solved. Also: a known-content byte search against a port finds only noise-level 4–6 byte matches. Also: a same-platform census came back negative and you need an independent second opinion.

Another build of the same design is ground truth you didn't have to derive. It works for data bytes, table order, code location, and even code absence. Two things defeat it silently: a transform you forgot to undo (a packed executable, endianness), and assuming that sameness at one layer implies sameness at another.

**Check / fix (pick what fits):**
- **Byte search finds nothing?** Check the target for a packer first (LZEXE `LZ91` at file+0x1c; `ancient`, `unlzexe`, `tools/shared/lzexe.ts`) and search the decompressed bytes. This only rescues flat data. VM bytecode that embeds platform addresses won't byte-match (`vm-bytecode-embeds-platform-addresses.md`).
- **Decode the easy platform first, then map back.** DOS/Windows twins are often the same structure with a different endianness or no compression (Black Crypt `bcdfs`↔`maindung.gam`, WIME `IMAG`↔`GAMI`).
- **Locate code** by searching the target for a reference routine's near-unique immediates (`MOVE.L #imm,Dn`). This cracked FE2's save cipher after caller-tracing failed. **At subsystem scale:** index ~8-byte sliding windows of the confirmed binary (drop windows with <4 distinct byte values), scan the other binary for exact hits, and cluster `(target−source)` deltas per region. Each dominant delta marks a routine family. Platform I/O (loaders, sound) won't match.
- **Table role and order:** run the same strided scan on a port built by a different compiler. One matching table on each side, same values in the same order, confirms the role (`resource-id-in-strided-record-field-carried-by-callback-object.md`).
- **Code absence:** repeat a clean negative consumer census (`dataflow-census-root-must-cover-publish-sites-and-full-function-body.md`) on a different-compiler port. A source-level test would survive both compilers' idioms. Pair it with a positive explanation of the value if you have one.
- **Pixels:** if a sibling encoding of the same art is already clean, decode it to an index grid. Brute-force the best offset *per structural unit* (plane, field, record), not per buffer. Per-unit offsets in arithmetic progression mean a stride bug (`planar-plane-padding-vs-tight-stride.md`).
- **Remap worry:** before tracing a remap table, `find()` the source asset's raw bytes in the target and check that a second item sits at the same relative offset. A verbatim copy needs no remap.
- **Identity:** compare byte-value histogram *percentages* against the sibling's solved resource before guessing dimensions (`tile-grid-dimension-needs-render-not-just-bytecount.md`).
- **Catalog identity:** when a port regroups N files into M, diff the resource-ID sets instead of filenames.
- **Sibling game / sibling repo:** run a same-studio decoder unchanged on any tag with overlapping magic naming. Verify each tag family separately, since a shared prefix doesn't guarantee a shared codec. Clone the sibling's RE repo and run its tooling on your bytes. Coverage may be partial, and the sibling's own caveat ("docs can be wrong — the ASM is the source of truth") applies to whatever you take from it.
- **Different container ≠ different internal layout.** Codec and post-decompression layout are separate questions. Try transferring the layout anyway and test it with byte-count and ID-arithmetic predictions.
- **Offset directory + string pool:** check that the directory values land exactly on regex-found string starts. Then diff the pool *content* across platforms at the same offsets. A mismatch in the directory region alone is expected.

**Canonical example:** Hunter (Amiga vs Atari ST, both based at `$800`). A sliding-window anchor index built from the confirmed Amiga binary mapped 8+ routines of the 3D renderer (scan, transform, bbox, edge-build, poly-fill, line-draw, matrix, per-object dispatcher) onto the ST binary in one pass. Different subsystems clustered at different deltas, several with 16-byte exact runs. It also surfaced a header-field consumer that a same-binary search had missed (`negative-from-addressing-root-not-shapes.md`).

**Variants:**
- Vengeance of Excalibur (DOS `vex.exe`, LZEXE 0.91): the search found nothing until decompression, then all 3 Amiga tables matched byte-identically.
- Valkyrie Profile VP1→VP2 (`valkyrie`): VP1's unmodified `SLZ` decoder worked byte-exactly on 4/4 VP2 `SL Z` samples, while an earlier VP2 session had burned ~480 parametric LZSS attempts (plus zlib/LZMA/`ancient`) on an `SL E` sample — which turned out to be a different codec.
- Valkyrie Profile PSX vs PSP `Field_master.prx`: a flags-bit-2 census gave the same "5 masks, nothing else" result under both compilers (PSP uses `beql`/`bnel`), and the bit was 100% determined by record position.
- WIME (`PAMM` IIGS): 40.3% `0x21`/22.0% `0x00` matched Amiga's `MMAP`, predicting the same terrain grid, later confirmed at 99.7%. EGA (3 files) vs VGA (7 files): 110/110 `GAMI` and 19/19 `LMRF` IDs matched.
- Pool of Radiance (Amiga, `crawl`): Gold Box Explorer's DOS wall-view geometry and `baseBlockId = 10*blockId` transferred exactly despite unrelated containers. Dune (`wyrm`) `command1.hsq`: the directory hit the string starts (638, 647, 655…) and the pool matched DOS from byte 638 on.

**History:** ~14 recorded techniques/instances (VoE, FE2, Black Crypt, WIME, Hunter, Wizardry 6, Valkyrie Profile, Might & Magic I, Pool of Radiance, Dune). Full log in `_archive/cross-platform-decode-oracles.md`.
