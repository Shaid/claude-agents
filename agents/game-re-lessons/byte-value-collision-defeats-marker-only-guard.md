# A single marker/tag byte can coincidentally collide with a real data value — gate transforms on the full structural invariant, not the byte alone

**When it bites:** a decoder or container parser branches on a single lead
byte to decide whether to apply a transform (byte-swap, decompress, skip a
header) versus treat the data as already in its "special-case" form — and
a resource that should have taken the transform branch instead silently
falls into the special-case branch (or vice versa), producing an
implausible downstream value (e.g. a decompressed-size field that reads as
an enormous number) rather than a thrown error.

A one-byte marker check (`data[0] === MARKER`) cannot distinguish "this
really is the special/uncompressed case" from "this is the general/
compressed case, and its first real data byte just happens to equal the
marker value by coincidence." If the special case has its own multi-field
structural invariant available (an exact expected byte length given a
width/height/depth read elsewhere in the same header, a valid-range check
on another field), that invariant is cheap to also check and is what
actually disambiguates the two cases — the marker byte alone is necessary
but not sufficient.

**Confirmed** on two different games sharing one IMAG/GAMI-style bitmap
container (Conan the Cimmerian and Warriors of Legend,
`~/Development/middilgard`): a resource-fork loader used `data[0] === 0x02`
alone to mean "this is an uncompressed bitmap header, don't byte-swap its
leading bytes as if they were a compressed-size prefix." Two independent
resources (one per game) were genuinely **compressed**, with a real
little-endian size-prefix value whose low byte coincidentally equalled
`0x02` (e.g. size `0x00000402` = 1026, stored as `02 04 00 00`). The guard
mis-fired, left the bytes unswapped, and the downstream decoder read the
un-swapped bytes as a big-endian size (`0x02040000` ≈ 33.8 million),
producing a nonsensical decompression-underflow rather than a caught error.
Fixed by requiring the marker-plus-exact-length check the project's own
decoder already implemented for validating a genuine uncompressed payload
(byte 0 is the marker AND total length matches `header + bytesPerRow(width)
* height * depth` exactly for some real width/height at the header's
declared field offsets) — the real compressed resource's actual on-disk
length never satisfies that exact-length invariant for any plausible
width/height, so the fuller check correctly routes it to the transform
branch instead.

**General shape to watch for:** any parser-level `if (data[0] === X) skip
transform` gate, where the transform being skipped is a byte-swap,
decompression, or header-reinterpretation, and a stronger structural
check for the "skip" case already exists somewhere else in the codebase
(often written for a *decoder*, not the *loader* that needs the same
check to decide whether to hand the decoder pre- or post-transform bytes).
Reuse that stronger check in the loader rather than duplicating the weak
one-byte version — the two guards drifting apart is exactly how this bug
survives even after the "real" decoder already handles both cases
correctly.
