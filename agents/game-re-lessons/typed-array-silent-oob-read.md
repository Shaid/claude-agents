# JS/TS typed arrays don't bounds-check — a Python/C prototype's implicit rejection becomes silent success

**When it bites:** porting a validated Python (`bytearray`) or C prototype
decompressor/decoder to TypeScript for the production pipeline, especially
one where an out-of-bounds index is relied on (even implicitly) to reject
garbage/false-positive input during exploratory scanning.

`Uint8Array` (and other JS typed arrays) do **not** throw on an
out-of-bounds read: `arr[i]` for `i >= arr.length` silently returns
`undefined`, which then coerces to `0`/`NaN` on the next arithmetic op or
assignment, instead of raising like Python's `bytearray[i]` (`IndexError`)
or even signalling like a C array under a sanitizer. A prototype that
happens to work correctly *because* invalid input triggers a bounds error
will port silently wrong: it keeps "successfully" decoding data it should
have rejected.

Jungle Strike (Genesis) Strike-LZSS port: the reference decompressor reads
`window[offset]` from a fixed 2048-byte ring buffer, where `offset` is
computed from 2 raw bitstream bytes and can nominally be up to 4095 (12
bits) even though only values below 2048 are ever produced by real
compressed data. The Python prototype (`bytearray` window) correctly raised
`IndexError` on garbage input with an out-of-range offset, which a
`try/except` used as the rejection signal for a full-ROM plausibility scan.
The first TypeScript port used a `Uint8Array` window and silently returned
`0` for the same out-of-range read instead of failing — decoding continued
instead of being rejected. This wasn't a cosmetic difference: an early
false-positive match (at file offset 4, inside the 68k exception vector
table) "succeeded" with a bogus huge declared size, and in a sequential
non-overlap scan its accepted byte range swallowed every real block that
followed it — cutting a 459-block scan down to 251 and losing **all 34** of
a 34-item ground-truth set.

Fix: when porting any bounds-dependent algorithm from a language with
native bounds-checking (Python, C-under-sanitizer, Rust) to JS/TS, add an
**explicit** range check (`if (index >= validRange) throw ...`) at every
point where the original language's implicit bounds failure was doing real
work — ring-buffer/window indices, table lookups by a decoded offset,
anything where "index went out of range" is supposed to mean "this isn't
real data." Don't assume behavioral parity across language ports for
anything that relies on an out-of-bounds access as a control-flow signal;
verify the port against the *same* known-good/known-bad ground truth used
to validate the original, not just the known-good cases.
