# A documented overlay-hunk "payload offset" can silently be its `HUNK_HEADER` tag position instead

**When it bites:** citing or reusing an existing doc's per-hunk file-offset
table for an AmigaDOS overlay-linked executable (`blink OVERLAY`-style,
several independent `HUNK_HEADER`/`HUNK_CODE`/`HUNK_END` blocks past the
root hunk set) — especially right before extracting raw bytes at that
offset to disassemble standalone, byte-signature-match against a savestate/
memory dump, or feed to any tool that assumes "this is where the code
starts."

A hunk's *segment-locator* table (the kind found in a `HUNK_OVERLAY` block,
or independently re-derived by a prior session) naturally lists each
overlay's `HUNK_HEADER` tag position — that's the byte offset AmigaDOS's
own overlay manager needs to load the segment. But the position a
disassembler or a static-analysis script actually wants is the `HUNK_CODE`
*payload* start, which sits a fixed number of bytes later: past the header
tag, the resident-name-list terminator, the `table_size`/`first_hunk`/
`last_hunk` fields, the per-hunk size-with-flags longword, and the
`HUNK_CODE` tag + length longword — 32 bytes total for a plain single-hunk
overlay segment with no resident names. If someone reused the *header*
address as the "payload offset" in a hunk-map table without checking the
actual bytes there, that table now silently underreports the payload start
by exactly 32 bytes for every hunk it happened to mislabel.

Confirmed on Wings (Amiga): the project's own "hunk map" table listed hunk
4's payload at `0x15e18` and hunk 5's at `0x2a90c`. Reading 4 bytes at each
gave `000003f3` — the `HUNK_HEADER` tag itself, not code — while a sibling
row for hunk 3 in the *same table* (`0xd93c`) was already correct (real
`4E55...` `LINK.W A5` bytes). The true payload offsets were `0x15e38` and
`0x2a92c` (`+0x20` past the wrong values); a third hunk's listed offset
(`0x38038`) was worse still — past the end of the 224,424-byte file
entirely, an impossible value that should have been caught immediately.
All three wrong hex values sat next to *correct* decimal parentheticals in
the same table cells, so a superficial read ("the numbers look consistent,
decimal matches hex-ish") wouldn't catch the bug — only actually reading
the bytes at the cited offset would.

**Fix:** never trust a hunk-map table's payload offset at face value before
using it as a byte-extraction anchor — read the first 8-16 bytes at that
exact file offset and confirm they decode as plausible 68k code (a `LINK.W
An,#n` prologue `0x4E5x` is a good, common tell) rather than a `HUNK_HEADER`
tag (`0x000003f3`) or any other structural longword. This is a two-second
check that catches both "the whole table is off by the header-block size"
and "one specific row got copy-paste-corrupted to an out-of-bounds value."
When rebuilding the table from scratch, derive the payload offset
programmatically (header position + resident-name-list length + `0x20`)
rather than by hand, and cross-check every row this way, not just the one
you're about to use.
