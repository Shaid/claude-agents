# Background jobs (Bash `run_in_background`, Monitor) do reliably push completion notifications — but a self-imposed timeout wrapper can still silently truncate the job before it ever gets the chance

**When it bites:** launching a long-running full-corpus batch/extraction job
(a `buildAssets` run over dozens of archive files, a full-directory decode
sweep spanning many chained batches) via the Bash tool's `run_in_background:
true`, or watching one with `Monitor`, and deciding whether to trust that a
later completion event will arrive and wake you up.

> **Correction:** an earlier version of this lesson claimed "a plain
> background Bash job... does not reliably [push a notification] in
> practice, regardless of what the tool's own description implies," based
> on two anecdotal failures. A later session (NieR Replicant PC's ~28,600-
> clip audio pipeline, run across 10 sequential batches over roughly 40
> minutes of real wall-clock time) directly contradicts that blanket claim:
> **dozens of separate `run_in_background: true` Bash calls and `Monitor`
> watches all delivered their completion notifications correctly**,
> including several that legitimately ran past the tool's own 120-second
> foreground-to-background threshold and one that ran unattended for the
> full ~40-minute batch sequence. Re-examining the original two failures:
> both are better explained by the *other* pitfall this file already
> documented (a self-imposed `timeout` wrapper killing the job before
> completion) than by notifications themselves being unreliable — case 1
> explicitly says so already; case 2's "no notification arrived" is
> consistent with the job having been killed or having errored out
> silently before it could complete, which was not distinguished from a
> genuine notification-delivery failure at the time. **The correct default
> is now: trust that `run_in_background: true` and `Monitor` will notify
> you.** The real, still-live risk is a *self-imposed* timeout truncating
> the job, not the notification mechanism itself.

## What still goes wrong

A self-imposed `timeout N` wrapper (or an artificially tight bound derived
from a small-scale benchmark) around a long batch job kills its child
processes at exactly `N` seconds regardless of real progress — silently
discarding whatever work was still in flight, and (worse) potentially
leaving *partial, plausible-looking output* on disk for whatever items were
mid-decode/mid-transcode at that instant. This can then be mistaken for a
genuine pipeline bug rather than a self-inflicted interruption artifact —
see `interrupted-transcode-mistaken-for-truncation-bug.md` for a concrete
case where exactly this happened (a smoke test's `timeout 180` cut off
in-flight ffmpeg transcodes, and the resulting truncated output looked
identical to a real demuxer/decode-truncation bug until re-reproduced
without the timeout).

## The fix

- **For a job whose real duration you don't know yet, don't wrap it in a
  self-imposed `timeout`** — let the Bash tool's own 120-second
  foreground/background transition happen naturally (it does not kill the
  job, only moves it to background and returns a task id), then wait for
  the real completion notification. This is now the *preferred* default,
  not a fallback.
- **If you do need a hard cap** (e.g. bounding one batch of a
  resumable/batched pipeline), size it with real headroom over a genuine
  small-scale benchmark — a benchmark measured on read/decode time alone
  under-counts fixed per-item overhead (writing many individual output
  files, subprocess startup cost) that only shows up at full scale; double
  a linear extrapolation, don't match it exactly.
- **Never assume a short/truncated-looking result from a
  timeout-interrupted or otherwise possibly-interrupted run reflects the
  pipeline's real behavior** — re-run the specific suspect item solo, in
  the foreground, with no timeout, before concluding anything about the
  decoder/pipeline itself.
- A forked sub-agent (`Agent` tool), a `Monitor` call, and a plain
  `run_in_background: true` Bash call are all now confirmed to reliably
  produce a later out-of-band notification event in this harness — treat
  all three the same way when deciding whether it's safe to end a turn
  waiting on one.
