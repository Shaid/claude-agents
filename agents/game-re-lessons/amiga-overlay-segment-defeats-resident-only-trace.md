# A HUNK_OVERLAY executable's non-resident segments are invisible to a resident-rooted trace — check for overlays before trusting a whole-file negative

**When it bites:** a call-graph trace or string search on an Amiga
executable comes back completely empty despite strong circumstantial
evidence the functionality must exist somewhere in the file (a confirmed
data table range-excludes certain ids with no fallback path, a sibling
resource family is missing one obvious member, etc.) — before concluding
the code genuinely doesn't exist, or escalating further.

Treasures of the Savage Frontier's wilderness-geo (ids 51-62) rendering
code was believed unfindable: the confirmed `getAreaWallsets` dispatch
range-excludes those ids outright, and a whole-executable ASCII string
search for `"Sky.tlb"`/`"wildcom"`/`"randcom"` (with the `.tlb` extension)
came back with zero hits. Both searches were legitimate but incomplete: the
executable is a 7-segment `HUNK_OVERLAY`-linked binary (1 resident root + 6
on-demand overlay segments), and every prior disassembly pass — including
the already-confirmed dungeon-render call graph — had only ever loaded and
covered the resident root. The wilderness code isn't hard to find; it
simply isn't present in any segment a normal single-segment disassembly
session sees.

A raw scan of the whole file for `HUNK_HEADER` (`0x3F3`) magic at more than
one file offset, plus `HUNK_OVERLAY` (`0x3F5`)/`HUNK_BREAK` (`0x3F6`)
markers, found the 6 overlay boundaries in minutes and immediately
explained the dead end. A follow-up **whole-file** string search
(deliberately unscoped by segment, since string literals don't respect hunk
boundaries the way code xrefs do) then found the real resource basenames —
`"Sky"`, `"DungCom"`, `"WildCom"`, `"RandCom"` — sitting inside 2 of the
non-resident overlays. They were bare names with no `.tlb` extension, which
is *also* why the original extension-included string search missed them:
the extension is synthesized at runtime by a generic `sprintf('%s.tlb',
name)` helper, so only the bare name is ever stored as a literal. A
follow-up disassembly of that exact overlay region then found and confirmed
a real dungeon/wilderness selector flag.

Past that point, a second, genuinely different limitation applies: the
selector's registration call resolved through a small-data trampoline slot
whose on-disk bytes were a literal unpatched `JMP.L $0` — the real callee
is itself overlay-resident and is patched into that slot only by AmigaOS's
overlay manager at runtime. This is a real, confirmed stopping point for
static analysis (the `HUNK_OVERLAY` control-table/patch-record format has
no public specification), not an incomplete trace to keep pushing on — the
next step needs either that private record format or a live emulator
capture.

**Fix, generalized:** on any Amiga executable, before trusting a
call-graph or string-search negative as proof functionality doesn't exist,
check for `HUNK_OVERLAY` structure — a cheap, minutes-long raw magic-byte
scan for more than one `HUNK_HEADER` occurrence in the file. If overlays
exist, re-run string/data searches unscoped by segment (they can reach
non-resident data a resident-rooted call-graph trace structurally cannot),
but recognize that an on-disk trampoline slot showing an unpatched
`JMP.L $0` pointing at overlay-resident code is a legitimate, different
kind of dead end that static analysis alone cannot resolve further.
