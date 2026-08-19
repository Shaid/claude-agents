# A stride-based marker-grouping technique that works on a sparse region can catastrophically false-merge in a denser one

**When it bites:** you've confirmed a multi-channel/multi-part record's
channel count by chaining discrete marker positions (terminators, sync
words, sentinel blocks) that sit an exact fixed byte stride apart — and
you're about to reuse that exact grouping technique, unmodified, on a
*different* region of the same file/format that's known or suspected to
contain many more, shorter, more densely-packed instances than the region
it was validated on.

Confirmed on Chaos Legion (PS2)'s streamed-audio region (`chaoslegion`/
flower project). The 17 background-music tracks were correctly identified
by chaining VAG codec terminator blocks that sit exactly `0x3800` bytes
apart (the confirmed per-channel interleave) — with only 17 widely-spaced
tracks in ~1.5 MB of terminator positions, no two *unrelated* terminators
land at that exact stride by chance, so "terminator at T and terminator at
T+0x3800 ⇒ 2 channels of one stream" is a safe inference. Reusing the
identical technique on the game's much denser SE/voice region (560+ short
sound-effect samples packed into ~287 MB) produced a handful of "channel
groups" spanning tens to hundreds of thousands of sectors each — one
computed at 8,843 seconds (2.45 hours), which is larger than the entire
region's own byte budget, an immediate tell that something was wrong. The
cause: with hundreds of terminators scattered through the region, the
*birthday-paradox* probability that at least a few unrelated pairs land
exactly one fixed stride apart by pure coincidence becomes real, and the
grouping logic (which has no way to tell "genuinely paired channel" from
"coincidentally-spaced unrelated terminator") chains them into one bogus
multi-part group whose reported span balloons to cover everything between
the two accidentally-aligned positions.

**Fix:** don't reuse a marker-stride-grouping technique across a
population-density change without re-deriving or re-validating it. In the
dense case, fall back to a more conservative construction — treat every
marker as ending exactly one (mono/single-part) unit rather than searching
for stride-aligned siblings, accepting that this may under-group (split a
genuine multi-channel instance into several single-channel pieces) but
cannot over-group into a nonsensical merge. If multi-channel grouping is
still needed in the dense region, corroborate any stride match with an
independent signal before trusting it (e.g. actual cross-channel sample
correlation on the candidate channels' decoded content, not just the raw
byte-position coincidence) — a real channel pair should correlate more
than an arbitrary two segments of similar-sounding audio; a coincidental
stride match has no reason to.

A cheap sanity check that catches this class of bug immediately: bound any
derived "one instance" size against the *smallest* independently-known
scale for that content type (a game asset that computes to hours of audio,
or gigabytes of texture, when its own domain never ships single assets
anywhere near that size, is a grouping-logic bug, not a real find).
