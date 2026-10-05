# A narrow-width sibling can make an old and a corrected planar layout byte-identical

**When it bites:** one member of a same-blit-code sprite/tile-bank family
(e.g. a 32px-wide bank) gets its bitplane layout corrected (row-interleaved
→ word-interleaved, or a mask-plane split replacing a flat N-bitplane
index), and you're deciding whether every other same-family member needs
independent re-verification before shipping the fix — or whether "no
visible difference" for a narrower sibling means the correction doesn't
apply there.

Two things compound to make this easy to get wrong in either direction:

1. **Byte/frame accounting is layout-independent.** A generic planar decoder
   (e.g. `planarByteLength`) computes total bytes from `width * height *
   planes` alone — row-interleaved, plane-major, and word-interleaved all
   consume the identical number of bytes per frame. So when you correct a
   family's layout (or bit semantics), every previously-confirmed frame
   count and total-byte accounting **carries over unchanged, automatically**
   — there is nothing to re-derive there, and a byte-count-only check will
   never catch or refute the correction either way.
2. **Narrow widths make row-interleaved and word/byte-interleaved formulas
   collapse to the same address arithmetic.** Word-interleaved's offset
   formula reduces to `floor(byteX / interleave) * planes * interleave +
   plane * interleave + byteX % interleave`; when a row is only 1
   interleave-unit wide (e.g. `width == 16` with a 2-byte/word interleave,
   or `width == 8` with 1-byte granularity), `floor(byteX/interleave)` is
   always 0 and the formula degenerates to exactly the row-interleaved
   byte order. For these siblings, the "layout" part of an old model was
   never actually wrong — only a co-occurring *semantic* error (e.g.
   treating a transparency-mask bitplane as a flat colour bit) would be.
   A wider sibling in the same family (e.g. `width == 32`, two
   interleave-units per row) does NOT degenerate this way — there the
   layout correction is a real, different byte order and must be
   independently re-verified (by content/render, not just arithmetic).

Confirmed on PowerMonger (Amiga): SPRITE24 (32px wide) was cracked first as
masked 4bpp/word-interleaved via disassembly. Generalizing the fix to
SPRITE32 (also 32px — genuinely needed the new word-interleaved byte order,
confirmed by a frame-for-frame content match against SPRITE24 at two LOD
sizes) versus SPRITE16 (16px) and SPRITE8. (8px, single mask+colour byte per
row) — the latter two's *byte layout* was already accidentally correct
under the old row-interleaved model (their rowBytes doesn't exceed one
interleave unit), so only their *bit-splitting* (mask bit vs. colour bit 4)
needed correcting, not their byte order. All four banks' frame counts and
total byte accounting matched the pre-correction numbers exactly with zero
re-derivation, confirming point 1.

**Fix:** when propagating a bitplane-layout/semantics correction across a
sprite-bank family that shares one blit routine, (a) trust that
frame/byte-count arithmetic needs no re-verification — it's invariant to
the fix by construction — and (b) compute `rowBytes = width / 8` for each
sibling and compare against the interleave unit: if `rowBytes <=
interleave`, the byte layout was already equivalent to row-interleaved and
"no visible change" there is not evidence the fix doesn't apply; if
`rowBytes > interleave`, render and content-compare that sibling
independently (e.g. against another already-confirmed same-blit-code
sibling) rather than assuming the correction transfers for free.
