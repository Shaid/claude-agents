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
