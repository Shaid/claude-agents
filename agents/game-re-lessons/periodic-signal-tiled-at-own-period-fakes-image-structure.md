# A periodic waveform tiled at its own period renders as a convincing gradient image

**When it bites:** you classify an unknown blob by byte autocorrelation, find a
strong peak at lag N, render the data as an N-wide greyscale bitmap, get a
clean non-noise 2D structure (diagonal wedges, gradients, moiré), and are about
to write it up as "confirmed image-like" or "a real, non-noise 2D structure."

**The render is circular evidence and adds no information.** Any periodic 1D
signal tiled at (or near) its own period *necessarily* produces smooth diagonal
banding: each row is the previous row phase-shifted by a constant, which is the
definition of a diagonal. You picked the width *because* the data repeats at
that lag, so a clean result is guaranteed and confirms nothing beyond the
autocorrelation peak you already had.

Confirmed on Epic (Ocean, 1992, Amiga, `hunter` project). `GR3D2` was
documented as "**Confirmed image-like**: rendered as a 176-wide greyscale
bitmap, shows a clean diagonal gradient/wedge pattern (two dark triangular
wedges meeting at a point, fanning into a lighter gradient) — this is a real,
non-noise 2D structure." It is a raw 8-bit signed PCM **sound sample** whose
waveform period is 176 *samples*. Its sibling `GR3D18`'s weaker "width 94" was
the same artifact. The wrong conclusion survived two sessions and shaped a
whole escalation brief.

**Cheap discriminators to run before writing up any autocorrelation-derived
render** (all pure Python, no numpy needed):

- **Lag-1 autocorrelation of the signed reading.** GR3D2 scored `r1 = 0.997`;
  adjacent bytes in real bitmap data are nowhere near that correlated. A very
  high `r1` says "smooth 1D signal", i.e. audio or a ramp, not pixels.
- **Zero-crossing rate of the signed reading** (GR3D2: `0.013` — a slow
  oscillator, not an index/pixel stream).
- **Short-time RMS envelope over ~16 windows.** A real sound effect either
  decays monotonically (Epic's other 13 samples: envelope-vs-time correlation
  down to `−0.985`) or has an attack; an image has no reason to.
- **Mean of the signed reading**, peak amplitude, and distinct-byte-value
  count. Signed PCM is DC-centred (`|mean| < 8`), a normalised rip touches full
  scale (`peak ≥ 120`), and uses most of the byte range.

**And always run null controls.** Five known non-audio files from the same
corpus (a `.3D` model, an `.IGD`, an `.LBM`, a font) all failed that PCM
signature, while 15/15 candidates *and* an independently-named reference sample
(`BANG.SPL`) passed — that contrast is what makes the classification a
confirmation rather than a plausible story. Two of the controls failed on
`|mean| ≈ 15` alone, one on having only 40 distinct byte values.

**General rule:** a render whose only supporting evidence is the periodicity it
was derived from proves nothing. Confirm the *data class* with a statistic the
render cannot produce, and run known non-members of the class through the same
test as a null control.

Sibling lesson, opposite symptom: when the render at the derived width comes out
*striped* rather than clean, see
`autocorrelation-period-is-the-scanline-stride.md` — there the period may be a
real row stride, or a non-pixel record stride.
