# When the executable resists static tracing, a shipped canned save/restart file is often the easier oracle

**When it bites:** a DOS/16-bit executable has no symbol table and shows
structural signs of resisting static analysis (an embedded overlay-manager
error string, an unusually large header/stub region, `list_strings`/
`list_all_strings` returning almost nothing readable anywhere in the
binary) — before sinking further time into tracing its data tables through
that structure.

A game's own shipped "restart"/"new game"/canned-state file (the same role
as a save file, but authored at build time and distributed with the game
rather than written by a player) is produced by *writing out the exact same
in-memory struct* the executable would otherwise construct at runtime — so
it mirrors the real data layout without requiring a single instruction of
the executable to be traced. Unlike a genuine player save (see
`save-file-not-asset.md` for the inverse mistake — an unexplained blob
turning out to be a save, not an asset), a canned/restart state file is
worth checking proactively as a *source* of ground truth, not just ruling
out as a false-positive "asset".

Confirmed on Warriors of Legend: `wofl.exe` (`data/legend/dosvga/`) opened
fine in radare2 (758 functions at analysis level 2) but carries no symbol
table, an embedded `"Runtime overlay error"` string, and an unusually large
`0x1800`-byte MZ header — all consistent with a Borland/Turbo-style
in-file-overlay executable, where large parts of the visible CODE segment
are runtime-swapped and don't coexist in one static image (a materially
harder static-tracing problem than a straightforward LZEXE-compressed
executable, which just needs decompressing first). Static `list_all_strings`
found almost no readable text in the executable at all. Running plain
`strings` against the game's own `restart.dat` (47 KB, sitting right next
to the executable, previously catalogued only as "save/restart data")
immediately surfaced plaintext item and character names ("Battle Axe",
"Steel Helm", "Brand", "Ataris"), and the file turned out to hold a clean,
self-describing fixed-29-byte-stride item-type record array — real
gameplay data extracted with zero disassembly, verified structurally (a
self-delimiting table end, consistent price/defense progressions across
material tiers) rather than by an executable trace.

**Fix:** when a target executable shows resistance signals (no symbols,
overlay/compression structure, near-empty string list) before investing in
deep static tracing, run `strings` against every other file the game
ships alongside it — save files, canned restart/new-game states, and
config/preference files are common, cheap, and frequently either
uncompressed or only lightly obfuscated compared to the executable that
would otherwise produce the same data at runtime.
