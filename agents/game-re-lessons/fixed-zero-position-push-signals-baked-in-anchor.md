# A shared draw routine's call sites can reveal static-vs-dynamic content from the pushed-argument shape alone, with no render needed

**When it bites:** several call sites all invoke the same already-confirmed
"draw a sprite/frame struct at (x,y)" routine, some frames in the
underlying corpus are already known to be dynamically positioned (a game
object tracked every tick), and others are unclassified — before spending
render/probe budget on the unclassified ones to guess whether they're
fixed HUD chrome or another moving object.

Confirmed on Wings (Amiga, `hunter` project): the confirmed enemy-plane
sprite draw calls always push a **freshly computed** screen X/Y (the
output of a per-tick world-to-camera projection). A separate cluster of
call sites to the exact same shared draw routine, found by extending the
same call-site census to cover *all* 66 invocations rather than the 25 a
prior session had scoped to, instead pushed a **literal `CLR.W`/`(0,0)`**
for the position argument every time. Per the draw routine's own
already-confirmed spec, a frame struct carries its own baked-in `+10`/
`+12` anchor-offset fields that get added to whatever position the caller
supplies — so pushing `(0,0)` is the call-site signature of "let the
frame place itself at its own fixed, authored position," while pushing a
computed value is the signature of "this is a tracked, moving object."
This distinction was visible purely from the pushed-argument shape at each
call site, before any of those frames had been rendered or semantically
identified — it correctly predicted (and was independently confirmed by
visual inspection of the already-rendered PNGs) that the `(0,0)` cluster
was static cockpit-canopy/HUD chrome and the computed cluster was the
moving enemy-plane sprite.

A second corroborating signal at the same call sites: whether the
*destination* buffer argument is the "current" or "previous" screen-buffer
slot, and whether the **same** frame gets drawn into *both* slots in
immediate succession right after a mode/screen transition. Content drawn
into both halves of a double-buffered display once, back-to-back, at mode
entry — and never referenced again per-tick — is being baked into both
buffers exactly once because it doesn't change frame-to-frame; content
drawn into only the currently-inactive buffer every tick is the opposite.
Both signals are readable from the call site's instruction shape alone,
without decoding or rendering the frame content, and without tracing the
draw routine's own body beyond what's already confirmed about its
argument-to-anchor-offset relationship.

**The general move:** once one shared draw/blit routine's calling
convention is confirmed (which argument is position, which is content,
whether content supplies its own offset), a corpus-wide census of *how
each call site fills that argument* — literal zero/constant vs.
freshly-computed register value, single-buffer vs. both-buffers-back-to-
back — classifies static/fixed-position content vs. dynamic/tracked
content for free, and can be done before any semantic identification
(rendering, palette work) of the individual frames involved.
