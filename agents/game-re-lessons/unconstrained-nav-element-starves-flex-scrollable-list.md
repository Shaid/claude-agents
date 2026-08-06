# An unconstrained variable-height nav element above a flex-scrollable list starves it of layout space — looks like an automation bug, is really CSS

**When it bites:** adding a new variable-content-height UI element (a
button grid, breadcrumb bar, filter panel — anything whose row count isn't
fixed) above an existing `flex: 1; overflow-y: auto` scrollable list inside
a flex column, and a Playwright (or other automated) click on a list item
starts failing with confusing, seemingly-unrelated errors: "element is
outside of viewport," then on retry "element intercepts pointer events"
(naming a *different*, unrelated sibling element like a status/meta bar),
then "element was detached from the DOM, retrying" in a loop.

Confirmed on Drakengard 3's asset viewer (`flower` project): a new
category-navigation button grid (21 buttons for one category, wrapping
into many rows) was inserted above the existing `#list` (`flex: 1;
overflow-y: auto`) in the same flex-column sidebar. The new element had no
height constraint of its own. Result: its content — several hundred pixels
of wrapped buttons — pushed every element below it (`#type-filters`,
`#list-meta`, and `#list` itself) toward/past the bottom of the visible
sidebar instead of `#list` keeping its `flex: 1` share of the remaining
space. `#list`'s content was still logically correct (the DOM data,
selectors, click handlers were all fine) — it just had no visible/clickable
screen area left to render into, which real-browser rendering and
Playwright's own layout-aware click logic both react to identically: "I
can see the element exists, but its computed position/size say it isn't
somewhere I can actually click."

**The trap**: every error message in the retry loop points at the *symptom*
site (the list item, or whatever sibling element the click coordinate
happened to land on) rather than the *cause* (the sibling element above it
that grew unbounded). This reads exactly like a flaky-selector or
virtualization timing bug — especially if the list was *just* changed to
add windowing/virtualization in the same session, which is the natural
place to suspect first. It is neither; it's a layout bug that would affect
manual mouse clicks identically, Playwright is just the first thing that
surfaced it because it asserts on element visibility/stability rather than
clicking blindly at stale coordinates the way a screenshot-driven manual
check might miss.

**The fix**: any new variable-height element inserted into a flex column
above a `flex: 1` scrollable region needs its own explicit height cap with
internal scrolling (`flex: none; max-height: <N>px; overflow-y: auto;`) —
don't rely on it "usually" being short. Confirm by re-running the exact
same automated click sequence after the CSS fix, not just visually
eyeballing one screenshot at the grid's smallest/default state (a category
with few groups may never trigger the overflow, hiding the bug until a
larger category is tested).
