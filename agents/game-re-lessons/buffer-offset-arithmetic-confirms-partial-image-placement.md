# A blit-target buffer-offset computation before a raw image load is a free, code-derived dimension oracle

**When it bites:** a raw/uncompressed picture's byte count is ambiguous
between several `(width, height, bitplanes)` factorizations (common for
any picture that isn't a full standard screen — a partial-height overlay,
a popup, a credits panel) and no header field states the dimensions
directly.

Byte-count factorization alone can't disambiguate — several candidate
triples reproduce the same total. Before falling back to render-every-
candidate-and-eyeball-it, check whether the loader code computes an
**offset into the destination buffer** before the file's `Read`/`Fread`
call (`add.l #$28a0,d4` or equivalent, added to a screen-base pointer
already in a register). That offset is itself strong, independent
evidence: divide it by the row stride implied by each candidate width
(`width/8 * bitplaneCount` bytes/row for a packed-planar/interleaved
format) — the candidate whose row count evenly divides the offset, and
whose own declared height plus that starting row exactly completes the
full screen height, is confirmed without rendering anything.

Confirmed on Phantasie II (Atari ST) `COVER2.PIC` (21,600 bytes,
ambiguous between multiple `width×height×bitplane` factorizations at the
byte-count level): `START.PRG`'s loader does `d4 += 0x28A0` (10,400
bytes) before reading `cover2.pic` into the screen buffer.
`0x28A0 / 160 bytes-per-row (320px × 4bpp) = 65`, and `65 + 135 = 200`
exactly completes a 320×200 low-res screen — independently confirming
`320×135×4bpp` is correct (matching the file's own byte count) and
additionally revealing that the picture is a bottom-of-screen overlay,
not a full frame, explaining why the earlier picture's top rows remain
visible above it once both are on screen.

This is a stronger, code-level version of the byte-count invariant check
— it comes from a completely different part of the trace (buffer/blitter
arithmetic, not palette-set tracing or string xrefs) and, when available,
settles the dimension question outright rather than narrowing the
candidate list. It doesn't replace rendering — a render is still the
final confirmation — but it can pick the right candidate to render first,
or confirm a render's result independently. See
`tile-grid-dimension-needs-render-not-just-bytecount.md` for the general
"byte count alone can't disambiguate" problem and the render-based
fallback when no such arithmetic oracle exists.
