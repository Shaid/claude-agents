# ffmpeg's `libmp3lame` can reject a direct non-PCM-source-to-MP3 transcode outright

**When it bites:** transcoding a compressed audio codec (ADPCM variants —
CRI ADX, PS-ADPCM, IMA, etc. — or any non-PCM source) directly to MP3 in
one `ffmpeg -i <compressed> -c:a libmp3lame ... out.mp3` call, skipping an
intermediate PCM WAV decode step, and the command fails outright with
`frame_size (1152) was not respected for a non-last frame` /
`Error submitting audio frame to the encoder` (ffmpeg exit code 234, zero
bytes of output) — not a quality/artifact issue, a hard failure.

Confirmed on NieR (2010, PS3, `flower` project): a shared `transcodeToMp3()`
helper (`tools/shared/ffmpeg.ts`) had previously only ever been fed clean
PCM WAV (decoded upstream by vgmstream for a sibling game's Wwise audio).
Feeding it a raw CRI ADX stream directly hit this failure on some real
files: the decoded packet framing from ffmpeg's own `adpcm_adx` decoder
doesn't always deliver frames whose sample count evenly divides MP3's
fixed 1152-sample frame size, and a modern ffmpeg's `libmp3lame` wrapper
rejects a mid-stream ("non-last") frame of the wrong size rather than
padding/buffering around it.

**The fix:** add `-af aresample` to the ffmpeg command line. This is a
behavior-preserving pass through libavfilter's own audio resampler *even
when source and destination sample rates match* — it re-buffers the
decoded audio stream into clean, MP3-frame-aligned chunks regardless of
the upstream decoder's own packet framing, and produces byte-for-byte-
equivalent-quality output on sources that were already framed cleanly
(confirmed non-regressive against an already-shipped WAV-sourced pipeline
in the same project). Cheaper and more general than manually resampling,
padding, or forcing an intermediate WAV write purely to sidestep this.
