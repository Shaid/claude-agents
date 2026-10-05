# A 1,024-byte RGBA8888 CLUT and a 256-pixel RGBA8888 image are the same bytes — an alpha-position statistical test can't tell them apart

**When it bites:** an alpha-channel/4th-byte statistical test confirms
"RGBA8888 at a 4-byte stride" for a small region (~1,024 bytes, or 512, or
64 — i.e. 256/128/16 entries) sitting at offset 0 of a larger entry with
more data following it, and a width sweep across that region can't find a
discriminating best width (every candidate width scores about equally on
an adjacent-pixel-delta or similar smoothness metric).

**Why it happens:** a 256-entry RGBA8888 colour lookup table and 256
RGBA8888 pixels are structurally identical — both are 1,024 bytes of
4-byte `(R,G,B,A)` groups, and in either role the alpha byte is
overwhelmingly `0xff` (a real CLUT's entries are almost all opaque; a real
opaque image's pixels are too). A statistical test built to confirm "this
region is RGBA8888" (checking that byte 3 of every 4-byte group equals
`0xff` far above chance) is by design blind to *which* of the two roles
the bytes are playing — it only proves the pixel format, not whether
what's being decoded is a lookup table or a picture. When the region is
actually a palette, there is no image there to have a width, which is why
a width sweep finds every candidate equally (un)convincing: it's testing
2D smoothness on data that was never laid out as a 2D raster with a real
width at all. What renders is what a **sorted or near-sorted palette**
looks like laid out as pixels — often a smooth-looking gradient with a
repeating dither-like texture, easy to mistake for a real (if odd) small
image rather than recognize as "not an image."

Confirmed on Valkyrie Profile: Lenneth (PSP remaster, `valkyrie` project):
25 "sparse tail" `PSPVAL1.PFS` entries each had their first 1,024 bytes
statistically confirmed as RGBA8888 (99%+ alpha match vs. ~0.4% chance)
and rendered at 4 candidate small widths (32×8, 16×16, 8×32, 64×4) as a
plausible-looking vertical gradient with checker-dither artifacts — no
width scored better than any other. A `re-codebreaker` escalation on the
*separate*, still-unidentified 53,760-byte remainder found the real
answer covered both pieces at once: the 1,024 bytes were a 256-entry
CLUT, and the "unidentified tail" was simply the entry's `256×256` 8bpp
palette-indexed pixel plane, decoded *through* that same CLUT.

**Corollary, same root cause, worth checking together:** a container's own
already-documented padding/filler byte turning up as the single most
frequent non-zero byte inside a supposedly-unidentified/sparse region is
evidence the region's declared **start offset** is wrong (an earlier
structure was under-counted, so the padding-fill run for the *following*
sector got folded into "the unidentified region"), not that the region
holds a genuine unknown tag/opcode/field. In the VP1:Lenneth case, the
53,760-byte "tail" region's single most common non-zero byte was `0x98` —
already documented in the same project's own container-header section as
the archive format's own MakePfs sector-fill byte. That byte run wasn't a
mystery field; it was 1,024 bytes of ordinary trailer padding that the
prior pass's under-counted region boundary (treating the CLUT as an image
inflated the "already accounted for" byte count by nothing, but treating
the palette+pixels as two separate unknowns split one real structure into
a spurious "confirmed + unidentified" pair) had folded into the wrong
bucket.

**The fix:** when an alpha-position (or any single-channel-position)
statistical test fires on an exact, suspiciously round byte count (256,
512, 1024, 2048 entries × a small fixed stride) sitting at offset 0 of a
larger entry, try **palette** as the first hypothesis and **image** only
second. The immediate next move is not a width sweep of that region — it's
trying the *entry's remainder* as N-bpp (8bpp first, then 4bpp) palette
indices through the candidate CLUT, checking whether `paletteBytes +
width*height*bpp/8 + smallPadding == entryLength` for a plausible
`width×height`. A width sweep that can't discriminate is itself a symptom
worth treating as a stop sign for the "it's a standalone image" hypothesis,
not a reason to try more widths.
