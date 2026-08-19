# An offline scene compositor that renders the full scrollable content, not a cropped viewport, empties out under a "real" camera-range pan

**When it bites:** exporting a parallax-shifted or camera-panned extra
frame from an already-working offline compositor for a scrolling/
multi-layer 2D scene (a room, a level, a parallax background stack),
using the game's own real, instruction-confirmed camera-range formula
(e.g. "camera can move from 0 to `contentExtent - screenSize`") to pick
the pan amount.

The game's own camera formula describes what the *live, viewport-cropped*
renderer would show — but an offline compositor built to flatten a whole
scrollable area into one static image for browsing/preview purposes
routinely renders onto a canvas sized to the **content's own full
extent**, not the hardware's small screen window. Panning a 1:1 (or
faster) parallax layer by the real full camera range shifts it almost
entirely off that larger-but-still-fixed canvas, leaving the "panned"
frame mostly or entirely empty — this looks exactly like a broken export
(and is easy to mistake for a decode bug in the parallax math itself)
even though the underlying per-layer camera formula is byte-exact
correct. Confirmed on Valkyrie Profile (PSX)'s room compositor (`valkyrie`
project): `composeRoom` always renders a room's own full pixel extent
(e.g. 960x770), not a 320x224 viewport crop; panning the main camera by
its real full range (`roomWidth - screenWidth` = 640px) left only a small
sliver of content visible in the exported frame on a real test room,
while a quarter-screen pan (80px) kept the scene fully recognizable and
still showed the correct relative-rate parallax shift between near/far
layers.

**Fix:** when adding a camera-panned export frame to an offline
compositor whose canvas is the *content's* full extent rather than the
hardware's screen size, don't reuse the live renderer's real camera-range
formula verbatim to pick the pan magnitude — that range was sized for a
small viewport crop, not your larger fixed canvas. Use a modest fraction
of the real range (enough to make relative-rate parallax visibly
different between layers, e.g. a quarter of the hardware screen
dimension) and actually render + look at the result before trusting it;
a purely numeric/structural check (bounds-valid indices, no
out-of-canvas samples) will not catch "technically valid, but the frame
is 95% empty."
