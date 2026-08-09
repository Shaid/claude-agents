# A third-party reference tool's own interpreter gap is not evidence about the real game's behavior

**When it bites:** a project's docs flag an "unresolved discrepancy" or
"not settled by this source" between a reference tool's *declared* string/
description for some game logic (an opcode's display text, a documented
formula) and what that same tool's *own interpreter code* actually does —
especially when the doc's phrasing treats this gap as an open question
about the *original game's* real behavior, rather than as a limitation of
the reference tool's reimplementation.

A reimplementation's source is guidance for where to look in the real
game, not a second oracle equal in weight to the real executable — but
it's easy to slide into treating "the reference tool doesn't implement
this" as meaningful negative evidence ("maybe the real game doesn't do
this either, or the display text is aspirational"). It usually isn't:
fan/community reimplementations are frequently incomplete precisely in the
corners that don't affect what the tool's own author needed working
(e.g. a dungeon-viewer only needs to *display* an action record
correctly, not correctly *execute* every opcode's game-state mutation).

Confirmed on Phantasie I (Amiga, `nicodemus` project): a fan tool's C#
source documented opcode `0x12` ("Set character stat") with a P1-specific
display string that reads as conditional ("If Stat < value Then Stat =
value"), but the tool's own `ExecuteAction` interpreter never actually
performed any mutation for this opcode — just showed the string. A prior
project pass had faithfully carried this forward as "not settled... the
interpreter code doesn't implement either interpretation's mutation, only
a display string," implying the real game's behavior here was genuinely
ambiguous. A real disassembly trace of the actual P1 `game` executable
(the `GetStat`/`SetStat`-adjacent opcode-`0x12` handler, byte-verified
against the file) found the **real game does implement** exactly the
conditional mutation the display string describes — applied per living
party member, not just once. The "ambiguity" was entirely an artifact of
the fan tool never having bothered to implement the mutation it displayed
a string for; it said nothing real about the original game.

**Fix:** when a project doc frames something as "the reference source is
internally inconsistent, so the real game's behavior is unclear," treat
that framing itself as unverified — the inconsistency only proves the
*reference tool* is incomplete or buggy there, not that the *original
game* is ambiguous. If the item matters (blocks a real opcode/format from
being usable), it's worth an actual disassembly trace of the game's own
executable rather than accepting the reference tool's internal
contradiction as the final word; if it doesn't matter enough to trace,
label the open item as "the reference tool's own interpreter gap," not as
"real game behavior is unresolved" — the two are different claims with
different confidence, and conflating them can leave a resolvable question
sitting in a project's open-questions list indefinitely.
