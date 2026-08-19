# An interrupted smoke-test transcode looks exactly like a genuine decode-truncation bug

**When it bites:** a video/audio transcode pipeline's smoke test (run under
an artificial `timeout` wrapper, or killed by a background-job interruption
while multiple concurrent ffmpeg/decoder jobs are still in flight) produces
output with a suspiciously short duration or truncated content, and the
instinct is to start debugging the pipeline's own decode/demux logic (a
"subfile"-protocol offset bug, a codec limitation, a container-parsing
error) rather than first asking whether the evidence itself came from a run
that was cut off mid-flight.

## What went wrong

Confirmed on NieR Replicant ver.1.22474487139 (PC)'s movie pipeline
(`MARC`-wrapped ASF/WMV2+WMA2 → MP4 via ffmpeg's `subfile` pseudo-protocol).
A smoke test wrapped the whole pipeline invocation in `timeout 180` while
`concurrency: 2` meant several multi-hundred-MB ffmpeg transcodes were
still running when the 180s cap hit. Two of the nine output files
(`MOVIE_EID_6000.arc`/`MOVIE_EID_6000_a.arc`, real source durations
235s/208s) showed only ~53-57 seconds of content afterward — a plausible-
looking, non-corrupt, playable MP4, exactly the shape a real demuxer bug
would produce. Real time was spent hypothesizing an ffmpeg `subfile`-
protocol concurrency bug before the actual cause was found: re-running the
*exact same* transcode command solo, via direct shell, with no timeout
wrapper, produced the full, correct 235.268s output byte-for-byte matching
the source's own real duration. The pipeline was correct throughout; the
only bug was the smoke test's own `timeout` cutting off in-progress ffmpeg
child processes and leaving whatever partial MP4 they'd flushed to disk at
that instant.

A second, real (not test-artifact) truncation-shaped finding was
discovered in the *same* session on two *other* files in the same corpus
(`MOVIE_ATRACT_GESTALT.arc`/`_REPLICANT.arc`) — see
`container-declared-size-may-be-stale-not-decoder-bug.md`. The two
phenomena produce visually identical symptoms (short duration, clean
non-error output) but have opposite root causes and opposite correct
responses (one needs zero pipeline changes, the other is a genuine,
byte-level-provable source-data property worth documenting) — which is
exactly why distinguishing them matters and why this file exists as a
separate, more general lesson from that one.

## The fix

Before treating short/truncated transcode output as a real decode bug:

1. **Check whether the run that produced the evidence could have been
   interrupted** — an artificial `timeout` wrapper around the whole
   pipeline, a backgrounded job that got killed, a host running low on
   time/resources mid-batch. If concurrency > 1 was in play, ANY in-flight
   job at the moment of interruption is suspect, not just the one you
   happened to inspect.
2. **Re-run the single suspect item solo, in the foreground, with no
   timeout**, directly via the same underlying command the pipeline uses
   (not just re-invoking the whole pipeline, which reintroduces the same
   interruption risk). A clean, uninterrupted reproduction that produces
   full-length correct output conclusively rules out a pipeline bug.
3. Only after that reproduction *also* shows truncation should you start
   looking for a real decode/demux issue — and even then, check the
   container's own declared-size metadata first (see the companion lesson
   above) before assuming the decoder itself is wrong.
