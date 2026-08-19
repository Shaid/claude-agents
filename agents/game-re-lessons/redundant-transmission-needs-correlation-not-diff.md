# A duplicated stream needs a correlation check, not a byte-diff, to tell "redundant copy" from "distinct channel"

**When it bites:** a container's records/packets carry a small toggle/parity
field (alternating 0/1, or any 2-valued discriminator) alongside otherwise
identical-looking payload, and you're trying to decide whether the two
groups are two *different* logical streams (e.g. left/right channel, two
language dubs, two LODs) that should be kept separate, or the *same*
content sent twice (redundancy/reliability buffering) that should be
deduplicated before use.

A raw byte-level diff is the wrong tool for this and can actively mislead:
real audio/data that's correlated-but-not-identical (the normal case for
genuine stereo content, or for the same signal re-quantized/re-dithered on
a second pass) can show a large diff fraction — confirmed on Chaos Legion
(PS2)'s FMV audio: two toggle-value groups of `PRIVATE_STREAM1` PCM packets
differed in **64.6% of raw bytes**, which reads like "these are different,
keep both." Concatenating both groups without deduplicating silently
**doubled** the decoded audio duration relative to the independently-known
video duration (exactly 2.000x, not a rounding artifact) — the tell that
caught the mistake.

**The fix: measure zero-lag cross-correlation on the decoded (not raw-byte)
signal**, not a byte-level diff. On the same data, zero-lag correlation
between the two toggle groups measured **0.99995** — decisively "the same
signal," despite the 64.6% raw-byte disagreement (byte-level diff is
dominated by low-order-bit dithering/rounding noise that correlation
ignores). The 0.99995 result, combined with near-identical RMS/peak levels
between the two groups, correctly identified this as a ping-pong
double-transmission (a read-reliability scheme for streaming off an
optical drive), not two independent audio tracks — despite the game's own
multi-language-texture-pack convention making "two dub languages" a
plausible-sounding alternative hypothesis going in.

General rule: when two candidate streams look like they *might* be the
same content sent twice, decode both to their native sample/value domain
first, then score correlation (ideally with a lag search, not just lag=0,
in case of any offset) — never conclude "distinct" or "redundant" from a
raw byte-diff percentage alone. A byte-diff answers "are the underlying
bits identical," not "is this the same signal" — those are different
questions once any encoding, dithering, or bit-level variation is in play.

> **Correction (2026-08-10, same game, later pass):** the 0.99995 figure
> above turned out to have been measured on a decode with an independent,
> undiscovered byte-order bug (see `audio-byte-order-measurable.md`'s
> Chaos Legion addendum) — the "decode both to their native sample/value
> domain first" step matters more than this file originally emphasized,
> because a wrong decode can still produce a deceptively clean-looking
> correlation number. Re-measured correctly-decoded, and across more than
> the original single clip/single aggregate figure (per this project's own
> "check every clip, not just one" convention): whole-clip zero-lag
> correlation ranged **0.37-0.96** across 4 clips (not a uniform ~1.0), and
> a per-window breakdown of one clip (12 one-second windows across its
> length) ranged **0.20-1.0000** — some windows genuinely bit-exact
> duplicates, others showing real, non-trivial amplitude divergence on both
> sides (not silence-dominated noise). A wide lag search (±1 second) found
> no better alignment, ruling out a simple fixed time offset as the
> explanation. **Two generalizable additions**: (1) always re-verify a
> correlation-based "redundant duplicate" conclusion *after* fixing any
> decode bug discovered later in the same investigation — a stale figure
> computed pre-fix can silently outlive the bug that produced it; (2) a
> single aggregate correlation number over a whole long stream can hide
> real per-window variance — break the stream into several windows spread
> across its duration (not just the start) before trusting one number as
> "confirmed duplicate," the same way a whole-corpus average can hide a
> per-file exception (see the sibling file's per-file byte-order point).
> The practical dedup decision (keep one copy, drop the other) can still be
> the right pragmatic choice even without a clean uniform correlation —
> just document it as "best available, not proven bit-exact everywhere"
> rather than closing the question.
