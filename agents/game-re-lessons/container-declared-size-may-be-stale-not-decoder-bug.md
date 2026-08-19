# A standard container's own declared duration/size can be stale — verify against its own binary header field, not just the decoder's behavior

**When it bites:** a standard, publicly-documented container format (ASF,
RIFF, MP4, any format with a binary header field that declares its own
total size/duration/packet-count) decodes *cleanly* — no errors, no
warnings, a well-formed muxed/finalized output — but the result is much
shorter than the source file's physical size would suggest, or than a
sibling file with a similar name/role. The instinct is to suspect the
decoder or an intermediate protocol (a byte-range/subfile read, a custom
demux wrapper) is truncating input it shouldn't.

## What went wrong / real finding

Confirmed on NieR Replicant ver.1.22474487139 (PC)'s
`MOVIE_ATRACT_GESTALT.arc`/`MOVIE_ATRACT_REPLICANT.arc` — two sibling
"attract mode" movie files whose real (post-header-strip) payloads are
592,719,054 and 659,320,780 bytes respectively. Both transcode cleanly via
ffmpeg (zero warnings even at `-v info`, a proper muxer-finalized end of
stream) to only ~36 seconds of output, byte-identical between the two despite
the very different real file sizes. Rather than accept "ffmpeg is
truncating this file" as the explanation, the ASF container's own **File
Properties Object** (a standard, documented, directly-parseable binary
header field — GUID `A1DCAB8C-47A9-CF11-8EE4-00C00C205365`, containing
`file_size`, `data_packets_count`, `play_duration`, `max_pkt_size`, etc.)
was parsed by hand from the raw bytes. It declared `file_size=55,063,748`
and `play_duration≈36s` — values that don't match either GESTALT's or
REPLICANT's own real container size, but **match a third, genuinely
smaller sibling file's real values exactly** (`MOVIE_EID_9400_memory.arc`,
whose real payload is 55,063,748 bytes). This is conclusive: the two large
files' ASF headers were never regenerated when their payloads were
replaced/grown — a stale, cloned, or copy-pasted header, not a decoder
truncation. ffmpeg (and, very likely, the game's own ASF/Windows-Media-
family player, since respecting a container's own declared packet count is
standard, correct demuxer behavior) is doing exactly the right thing:
believing the header. Confirmed real, non-zero, bitstream-shaped bytes
continue physically past the declared boundary in the file — the header is
wrong about the payload's extent, not the payload itself missing.

A second file in the same corpus (`MOVIE_EID_6000.arc`) showed a
similar-looking short-duration symptom from a *different*, non-source-data
cause (a smoke test's own timeout interrupting an in-flight transcode) —
see `interrupted-transcode-mistaken-for-truncation-bug.md`. Telling these
apart required checking the container's own header field directly, not
just re-running the transcode.

## The fix

When a standard container's real playable content is shorter than its
physical file size suggests it should be:

1. **Parse the container's own declared-size/duration binary field
   directly** (ASF's File Properties Object, RIFF's chunk-size fields, an
   MP4 `mvhd` atom's duration, etc.) rather than relying only on a
   probe tool's (ffprobe's) *summary* — some summaries themselves fall back
   to a bitrate-based *estimate* when the declared field is absent/unusual
   (ffmpeg logs this explicitly: `"Estimating duration from bitrate, this
   may be inaccurate"` — a signal worth grepping for) and can mask exactly
   this kind of stale-header condition.
2. **Compare the parsed values against a sibling file's own real values** —
   a stale/cloned header often matches a *different, real* file's
   properties exactly (as here), which is much stronger evidence of
   staleness than "the numbers look implausible."
3. **Trust the decoder's own final output duration as ground truth**, not
   the source's declared value, once you've confirmed the mismatch is a
   real source-data property (matches this project family's established
   convention for unreliable container-declared durations, e.g. CRI USM's
   own `format.duration` field being independently known-unreliable for
   the same reason).
4. Document this as a real, verified source-data finding (with the
   byte-level parse as evidence) rather than "fixing" anything at the
   extraction layer — there is nothing to fix; the decoder is behaving
   correctly relative to what the container honestly declares.
