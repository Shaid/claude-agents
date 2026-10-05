# An artbook section can juxtapose real-world reference photography with real in-game art — only the labeled in-game side is a valid identification oracle

**When it bites:** mining an artbook/strategy-guide/material-collection for
visual identification of a game asset (a background, a character, an item),
and a section shows imagery that could plausibly BE a screenshot or CG
render — before treating any picture in that section as ground truth, check
whether the section is actually a real-world-vs-game comparison, not a pure
game-art gallery.

Confirmed on Valkyrie Profile (PSX, `valkyrie`): the World Guidance artbook
(already known-good from a prior round's character-portrait match) has a
"Story" section (pp. 102-111) that illustrates the game's real-world Norse
mythology source material using actual stock photography and historical
paintings — real longships, real runestones, real Yggdrasil-tree
illustrations — deliberately placed near the game's own lore text. None of
that imagery is a game asset at all, despite living in the same official
artbook, on pages structurally similar to the character/background CG
pages, and despite the book explicitly captioning some spreads 現実
("reality") side by side with ゲーム中 ("in-game") to make the comparison
clear. Only the ゲーム中-labeled side is a valid identification oracle;
treating the 現実 side as candidate game art would have wasted a match
attempt against content that was never rendered by the PSX at all.

**The generalizable trap**: a licensed/mythology-themed game's own official
art book is a natural place for the publisher to run "here's the real myth,
here's how we depicted it" educational spreads — WWII games do the same
with real archival photos next to in-game recreations, sports games with
real athlete photos next to in-game models, etc. These sections are
visually similar to (and often physically adjacent to) the pure game-CG
gallery pages an identification search is actually looking for. Before
matching a candidate picture from an artbook page, check the page/section's
own labels and surrounding captions for a reality-vs-game framing device,
and prefer sections explicitly dedicated to game CG only (e.g. a
themed "CG art museum"/"gallery" page distinct from a "history"/"story"/
"world lore" section) as the reliable oracle.
