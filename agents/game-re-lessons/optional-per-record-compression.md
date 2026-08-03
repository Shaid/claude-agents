# A minority of "corrupt" records in a healthy container is usually optional compression, not data rot

**When it bites:** most entries in an archive/resource container decode cleanly,
a minority come out as garbage, and the docs describe those as corrupt, garbled,
or damaged.

Containers frequently compress records **per-record and optionally** — the
container itself says nothing, and each record either is or isn't compressed,
usually decided at build time by whether compression actually saved space. A
reader that assumes uniformity decodes the compressed minority as raw bytes and
gets plausible-looking garbage, often with recognisable fragments mixed in
(which reinforces the "corrupt" reading rather than dispelling it).

The tell: the failures are a *minority*, they are *consistent* in character
rather than randomly varied, and the container's structural invariants (offsets,
lengths, counts) all still hold. Genuine data rot rarely respects a container's
own bookkeeping.

Worked example (Spirit of Excalibur CDTV, `middilgard` project): `hint.res`
carries 278 `CSTR` text resources. 226 read as clean text; 52 were documented as
"decoding with embedded garbled bytes, cause unresolved" and left as an open
item. They are **LZSS-compressed**, using the same `u32 decompressed-length +
stream` wrapper the same game family already used for its `IMAG` graphics. Run
through the project's existing, unmodified `lzssDecompress()`, all 52
decompressed to exactly their declared length, yielding clean English prose.
Nothing was corrupt.

The generalisable fact was bigger than the fix: `CSTR` is *optionally* compressed
in exactly the way `IMAG` is. That is a property of the container family, not a
quirk of one file — and it had been sitting unexamined because "garbled" reads as
a data problem rather than a format one.

**Fix:** before writing any record off as corrupt, try every codec the container
family is already known to use, with the family's own wrapper convention. The
decompressor you need is usually already in the project, written for a different
resource type. Confirm by the strongest available check — decompressed length
matching a declared length exactly, across every affected record, is close to
conclusive.

**The same "uniform assumption breaks a minority" shape shows up one layer
earlier, in a preprocessing/fixup step rather than the decompressor
itself.** A byte-swap or endianness fixup applied uniformly to every
resource of a given type — on the assumption every instance carries the
same size-prefix header a *majority* of them do — can silently corrupt a
minority that has no such prefix at all, rather than merely failing to
decompress. Confirmed on Warriors of Legend's `GAMI`/`LMRF` resources: most
are PackBits/LZSS-compressed behind a u32 size-prefix header that needs an
LE→BE byte-swap for downstream BE-default readers, but 12 real `GAMI`
resources are stored **uncompressed** with a completely different 6-byte
header (marker/height/width/depth) sitting at byte 0 — the uniform swap
fixup scrambled that header's fields before the decoder ever saw them,
producing "Invalid IMAG depth: 0" rather than garbled-but-plausible pixels.
The fix mirrors the decompressor case: check the uncompressed variant's own
exact-length invariant (`length == headerSize + bytesPerRow*height*depth`)
*before* applying the fixup, and skip it when that invariant holds on the
pre-fixup bytes — the same "does this minority's own structural bookkeeping
already check out without the uniform operation" test, just applied one
step earlier in the pipeline.

Related: `renamed-magic-container.md` (unfamiliar magic, familiar payload) and
`rle-decode-succeeds-on-garbage.md` (the opposite error — a decode that runs to
completion on data that isn't in that format at all).
