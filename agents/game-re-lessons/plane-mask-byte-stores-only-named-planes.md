# A plane-mask byte stores only the planes it names — stored plane k goes to the k-th set bit

**When it bites:** a planar sprite/cel record carries a small byte documented as "flags (uninterpreted)", frames have varying data spans at the same w×h, or a minority of frames render with plausible but wrong colours. Amiga engines often store and draw only the planes a frame uses (the OS's own `VSprite.PlanePick` works the same way): a frame with mask `0x1B` stores 4 planes, not 5, and they belong to hardware planes 0, 1, 3 and 4.

Decoding the stored planes as contiguous planes 0..n−1 is right for every frame whose mask is a low contiguous run (`0x0F`, `0x1F`) and gives wrong colour indices for the rest. Palette-level checks don't catch it: the union of indices a sprite family uses barely changes, so a "used indices" tripwire keeps passing.

**Check / fix:**
- Invariant: `dataSpan == popcount(mask) × rowBytes × h` on every frame. Run it against a null (`mask >> 1`, or a fixed depth).
- Decode by scattering: stored plane k → hardware plane at the position of the k-th set bit. Confirm in the blitter loop: it shifts the mask (`lsr #1 / bcc skip`) and advances the source only on set bits, while the destination advances every plane.
- Re-render every frame whose mask isn't a low contiguous run, and redo any palette work that used the old indices.

**Canonical example:** Moonstone (Amiga, `moonstone`). CEL record `{u32 offset, u16 w, u16 h, u8 hi, u8 mask}`; the `mog` blitter does `lsr.w #1,D6 / bcc` and advances the source only on set bits. `span = popcount(mask) × rowBytes × h` holds on 2,329/2,329 frames in 50/50 banks, against 76/2,329 for the `mask>>1` null. 319 frames in 36 banks have non-contiguous masks (`0x1B`, `0x17`, `0x0B`, `0x05`); 51,834 of their 87,533 opaque pixels changed index after the fix, while family index unions changed for only two families.

Related: `bitplane-layout-variants.md` (plane order/interleave), `one-bitplane-or-equal-stride-reading-renders-plausible-art.md`, `unexamined-bits-of-parsed-field-hide-a-discriminator.md`.

**History:** 1 instance (moonstone, 2026-11-18 audit).
