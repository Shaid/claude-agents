# A keyframe animation VM's "hold frame forever" sentinel is a real, visible pose — not a placeholder

**When it bites:** decoding a keyframe-based sprite/animation VM (a
per-object script cursor advancing through fixed-size records, with a
`cmd`/flag field whose special value means "don't auto-advance") — before
assuming that sentinel value marks an off-screen, invisible, or
placeholder frame and skipping to a later keyframe index for "the real
visible pose."

## What went wrong

D&D: Shadows over Mystara (CPS2, `kolbold`): a newly-found animation VM's
"advance one tick" routine tests a keyframe's `cmd` high byte against
`0xfe`; when it matches, the routine forces the duration counter back to 1
and returns *without* loading the next keyframe — i.e. this frame repeats
forever until some other code explicitly changes state. The first
decoding pass assumed "never advances" meant "not really shown" (an
off-screen placeholder before the boss's real appearance) and used
keyframe index 2 instead — which turned out to be un-authored bytes past
where the VM's own control flow can ever reach (since a `0xfe` frame never
lets the cursor advance past it), and correctly failed the decoder's own
tile-count sanity check when interpreted as a sprite-definition pointer.

The correct reading is the opposite: a "hold forever" cmd is exactly what
a real, permanent **idle pose** looks like in this class of engine — it's
a real, fully-authored frame, just one the animation system doesn't
auto-cycle away from. Index 0 (the actual hold frame) decoded cleanly into
a real, non-degenerate sprite-definition blob; index 2 did not.

## Fix

In any keyframe/script-cursor animation format, a "don't advance"/"loop
here"/"hold" sentinel describes the *auto-advance* semantics only — it
says nothing about visibility. Treat it as "this is the frame shown for as
long as nothing else changes state" (very often the idle/default pose,
the single most commonly-rendered frame in the whole table), not as
"skip past this to find the real content." When a format has such a
sentinel, decode the **sentinel frame itself** first, and only reach for
later indices if the sentinel frame's own payload fails a structural
sanity check (as it did here) — a failing sanity check on a
skipped-past-the-sentinel index is itself a strong signal you've mis-read
the sentinel's meaning, not that the format is broken.
