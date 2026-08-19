# A generic demuxer's shallow audio read on a game movie — zero streams, or a plausible-looking codec tag — can be wrong either way; only a real decode attempt tells you

**When it bites:** `ffprobe`/`ffmpeg`'s default probe reports zero audio
streams (or auto-detects the wrong codec, e.g. `mp2`) on an MPEG-PS/PES-
based game movie, especially a title/logo loop sample checked first — before
concluding the movie is genuinely silent or scored by a separate,
non-embedded music track. **Also bites in the opposite direction**: the
probe confidently reports a specific, plausible-sounding codec name with
correct-looking sample rate/channel/duration metadata — that identification
can *still* be wrong, and container-level probing alone won't catch it; only
attempting a real decode (not just `-show_streams`) exposes the mismatch.

Confirmed independently in **two unrelated PS2 Capcom titles from the same
project pass**: Chaos Legion's hidden FMV region (`docs/chaoslegion/ps2/
data-structure.md` §9.4) and, later the same project, Devil May Cry's
regular, ISO9660-catalogued `.PSS` movies (`docs/devilmaycry/ps2/
data-structure.md` §9) — both use a **custom `PRIVATE_STREAM1` (`00 00 01
BD`) PES framing wrapping a Square-family `SShd`/`SSbd` PCM chunk pair**
(the same tag convention independently confirmed a third time, in Cavia's
unrelated "cavia stream format v1.01" container — genuinely shared PS2-era
streaming-audio middleware, not developer-specific). Generic demuxers don't
recognize this framing: on Chaos Legion, `ffprobe` mis-auto-probed it as
`mp2`; on Devil May Cry, an initial pass sampled only `TITLEP.PSS` (the
title loop) and `ffprobe` found literally zero audio streams, which the doc
recorded as "plausibly silent." Widening the check with a raw byte-level
census — count of `00 00 01 BD` markers and `SShd` occurrences — across
Devil May Cry's whole 18-file `.PSS` corpus found **every single file**
(including `TITLEP.PSS` itself) carries a real embedded audio track; the
original "silent" read was purely a probe artifact.

**A third instance, the opposite failure shape (false positive, not false
negative)**: confirmed on NieR (2010, Xbox 360)'s `media/movie/*.sfd` files
(`~/Development/flower`, `docs/nier/x360/data-structure.md` §3.4). ffprobe
confidently tags the audio elementary stream `adpcm_adx` with plausible
metadata (48kHz stereo, correct-looking bitrate/duration) — a real, known
CRI codec, not an unfamiliar tag, which made it easy to trust at face
value. A full transcode attempt (`-c:a aac`, an actual decode) instead
fails on **every one** of the 4 real files with a ~99% packet decode error
rate (`Error submitting packet to decoder: Invalid data found`). Stream-
copying the raw bytes out (no decode) revealed why: the payload begins with
`AIXF` — a real CRI **AIX** container (multi-segment, multi-layer — here 3
stereo ADX layers muxed as 6 channels), not a flat ADX bitstream at all.
ffprobe's shallow per-stream probe apparently classifies the *first
sub-layer's* codec correctly (`adpcm_adx` is technically what's inside
AIX) while missing the outer container framing entirely, producing a
confident-looking but structurally incomplete identification. The fix that
found it: attempt a real decode (not just `-show_streams`) before trusting
a codec tag on any unfamiliar-provenance game movie, especially before
wiring that tag into a pipeline's transcode step.

**The fix, in all directions:**
1. **Detection**: don't trust a generic demuxer's stream count on an
   unfamiliar/in-house game movie container — do a raw marker census
   (`00 00 01 BD` PES packet count, plus a search for known chunk tags like
   `SShd`) across the *whole* corpus, not one sample file, before concluding
   "no audio."
2. **Verification, once real audio is suspected**: decoding the raw PCM
   directly and cross-checking its duration against an *independently
   known* duration for the same asset is a strong, cheap oracle even with
   no working reference player — Devil May Cry's decoded audio duration
   (63.926s) matched that same file's own `ffprobe`-reported **video**
   stream duration (63.880s) to within 0.07%, decisive confirmation without
   needing to hear it.
