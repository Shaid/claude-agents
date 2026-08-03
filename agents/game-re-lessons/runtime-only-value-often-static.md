# "This value only exists at runtime" is usually an untested assumption — exhaust the static trace first

**When it bites:** a project doc says some value can only be captured from a
running game, live-debugging attempts have already failed, and you're about to
attempt another one (or to build savestate-parsing infrastructure to get at it).

Live capture is expensive, fragile, and — on emulators with partial debugger
support — often simply unavailable. Before committing to it, check whether the
"runtime-only" claim was ever actually established, or whether it was inferred
once from a failed static attempt and then inherited by every later doc.

Worked example (War in Middle Earth, Amiga, `middilgard` project): the screen Y
position of scene decoration sprites was documented across several sessions as
computed at runtime and capturable only with a debugger. Three separate live
routes were tried and all failed — IPC single-stepping (the CPU parks in the
Kickstart idle loop because the game polls instead of using interrupts), the
emulator's own debugger console (crashed on return to the game), and IPC
breakpoints (silently never halted). A fourth route, offline savestate parsing,
was half-built to get around them.

The value was a **static table lookup**:
`Y = groundLine - anchorHeight[imagId - 300]`, an 18-entry table sitting in the
DATA hunk the whole time. There was never anything to capture.

The root cause of the multi-session detour was tracing **the wrong function**.
An earlier pass had identified a plausible-looking placement routine and derived
a formula from it (`X = idx * 9 + 16`) that was internally consistent and
completely inapplicable — it belonged to a different subsystem. Every later
session inherited both the formula and the "Y is runtime-only" conclusion drawn
beside it, and none re-checked whether the function was the right one.

**Fix:** treat "runtime-only" as a hypothesis with an owner and a date, not a
property of the data. Before any live-capture work, (a) find where the claim was
first made and what was actually tried, and (b) independently confirm you are
looking at the right function — check that its callers and its written-to
structures match the behaviour you're chasing, rather than that its arithmetic
looks plausible. A formula that produces sensible numbers is not evidence that
it is *this* subsystem's formula.

Related: `static-xref-misleads.md` (an xref found is not the consumer), and
`amiberry-live-capture-workflow.md` for when live capture genuinely is the
answer.
