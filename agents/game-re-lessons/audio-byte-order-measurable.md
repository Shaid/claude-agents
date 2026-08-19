# Wrong-endian PCM sounds like noise, not like failure — discriminate numerically

**When it bites:** you're decoding raw PCM (CD audio, `.raw`/`.pcm`/`.snd`
blobs, sample banks) whose byte order isn't declared, and you're about to pick
one and move on.

Byte-swapped 16-bit PCM does not fail loudly. It decodes to a full-length,
correctly-shaped waveform that is pure hash. If you only listen briefly, or only
check that the decode ran, you can ship the wrong endianness and never notice —
and rippers built on big-endian-native tooling (Amiga, classic Mac) do emit
byte-swapped output for formats whose spec says little-endian.

The discriminator is **mean absolute sample-to-sample difference**. Real audio is
massively oversampled relative to its content: consecutive samples are highly
correlated, so successive differences are small. Byte-swapping puts the noisy low
byte in the high position, decorrelating adjacent samples and driving the mean
difference toward a large fraction of full scale.

Worked example (Spirit of Excalibur CDTV, `middilgard` project), measured on a
10-second excerpt from the middle of each of 26 CD audio tracks:

| Reading | Mean abs sample-to-sample difference |
|---|---|
| Little-endian (correct) | 700 - 4,300 |
| Big-endian (swapped) | ~21,800 (RMS ~18,900) |

Roughly two thirds of full scale, sample to sample, on 20 of 26 tracks —
unambiguous, and unanimous across the whole set. No listening required.

**Fix:** always measure both readings before choosing. Mean absolute first
difference is the cheapest test; the correct order is the one that produces a
value small relative to the signal's own RMS. The same statistic doubles as a
sanity check that the data is audio at all — a filesystem or a bitmap read as
PCM also produces a large first difference.

Useful companions for the same investigation: L/R channel correlation (near 1.0
means mono content stored as stereo, which usually means speech), and long-term
average spectrum (speech concentrates 300 Hz - 1 kHz with very little above
4 kHz).

**Byte order can vary *per file* within one game's own corpus, with zero
header field announcing it — don't stop at "pick one for the whole
format."** Confirmed on Chaos Legion (PS2)'s FMV audio
(`chaoslegion`/flower project): 15 of 16 audio-bearing clips are
big-endian 16-bit PCM, but one clip (a "Liv" logo/theme-song vanity card,
plausibly authored by an external production house rather than the
game's own in-house FMV pipeline) is little-endian — the *opposite* byte
order, with an equally decisive margin. The two cases' `SShd` sub-headers
are byte-identical (same `format_tag`/`sample_rate`/`channels`, same
unlabeled reserved fields) — nothing in the container format distinguishes
them. This is exactly the class of bug that passed every prior
structural/statistical check (duration-from-byte-count, RMS/peak range,
even a cross-track cross-correlation check) silently, because none of
those checks are sensitive to a per-sample byte swap — duration only
depends on byte *count*, and RMS/peak of scrambled samples still land in a
plausible numeric range. The general fix: run the discriminator
(mean-squared first difference / "roughness," or mean absolute
sample-to-sample difference) **per file**, not once for the format, and
auto-select per file — treating byte order as a fixed, corpus-wide
constant is itself an unverified assumption. A spectrogram
(`ffmpeg -lavfi showspectrumpic`) makes the same point visually: wrong
byte order renders as flat, uniform-energy broadband noise across the
whole frequency range; correct byte order shows normal energy roll-off
with frequency plus real transient/dynamic structure — a fast way to
sanity-check a fix by eye before trusting the numeric margin alone.
