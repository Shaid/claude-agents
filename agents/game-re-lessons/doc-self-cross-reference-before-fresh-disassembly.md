# A doc's own already-solved section can silently answer a different section's "still open" row

**When it bites:** about to start fresh disassembly tracing on an item a
project's spec doc lists as open/unresolved (a "still open" table row, a
`TODO.md` residual) — especially when the item names a specific address,
table, global variable, or field that sounds like it could be shared
infrastructure (a per-level lookup table, a shared A5/frame-relative
pointer, a shared dispatch helper) rather than something unique to the
open item's own feature area. Also: about to trust (or about to write) a
dated status-update/"done" block's characterization of a specific asset —
see the addendum below.

Large format-spec docs accumulate dozens of independently-written sections
over many sessions. A section written early can fully solve a table or
write site, complete with address and verification, while a *different*
section written later — describing a different consumer of that same
table — still calls its own copy of the question "not verified, no write
site searched for," because nobody grepped the doc for the address/table
name before writing that later section. The two sections never got linked.

Confirmed on Black Crypt (Amiga, `crawl` project): the viewport-rendering
section's "Still open" table listed `$51A(A5)` — "the door-family position
variant... when nonzero each adds +0x24 to its position table... almost
certainly 'this doorway square also carries a door frame' — not verified,
no write site searched for." A direct disassembly search for the write
site found it in one instruction, and the value it stores comes from a
13-entry per-*level* lookup table — which turned out to be the **exact**
table already fully decoded, named, and verified five independent ways in
a completely different, already-`**SOLVED**`-tagged section of the same
document ("Dungeon tileset selection" → "Selector 1 — per-level default"),
which even already listed `$51A(A5)` by name as one of that table's three
known readers. The "still open" row's entire premise (a per-door
condition) was wrong; the real answer had been sitting fully solved
elsewhere in the same file the whole time, just never cross-linked.

**Fix:** before disassembling anything new for a "still open" item, `grep`
the whole spec doc (not just the section the item lives in) for the exact
address/offset/hex-constant/global-variable name the item cites. If it
turns up in an already-`SOLVED`/`confirmed` section elsewhere, read that
section first — the answer, or most of it, may already be written down,
just not linked to the item that needs it. This costs one grep and can
save a full disassembly pass, and it generalizes past this one field: any
doc built incrementally across many sessions is at risk of solving the
same fact twice under two different names, or solving it once and leaving
a sibling "still open" row unaware of the fact.

This is the doc-authoring-time twin of
`working-tree-may-already-solve-a-docs-open-item.md` (which checks whether
*uncommitted code* is ahead of the docs) — here the docs themselves are
internally ahead of one of their own rows, and a plain text search of the
committed file is the fix, not `git status`.

**Addendum — the newest text in a doc is not automatically the most
correct.** The same failure mode runs in reverse: a dated "status
update"/"done" block appended to a doc can itself be wrong even though
it's the most recent writing, if it never cross-checked an *older* but
still-standing section describing the same asset. Confirmed on Phantasie
III (Amiga, `nicodemus` project): an implementation-status update dated
2026-08-18 called `Dng.csh` "a 320×200 picture that is ~99% flat black
with a thin border frame... no per-cell tile set", and built a whole
flat-colour dungeon renderer on that conclusion — directly contradicting
a `graphics-formats.md` render-verification section written a week
earlier that had *already* correctly characterized the same file as
"small icon sprites... scattered... near the top-left", i.e. an icon
bank, not a backdrop. The newer pass never grepped the doc for the
file's own name before writing a confident "confirmed" verdict about it.
**Fix, generalized from the base lesson:** before trusting *or writing* a
status-update/"done" block's characterization of a specific asset/file/
table as ground truth, grep the whole doc (not just the section being
updated) for that asset's name — a "confirmed" claim from an earlier pass
is not superseded just because a later block sounds more current.
