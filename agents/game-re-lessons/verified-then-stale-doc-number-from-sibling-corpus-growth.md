# A doc's headline verification number can have been genuinely correct when written, then gone stale as the corpus grew from unrelated later work

**When it bites:** re-running an already-documented full-corpus decode
pass (a battle-anim/patch-resolution sweep, an item/name-table census, any
"X/Y records solved" figure) as a *regression check* or a *comparison
baseline* for new work, and the live number disagrees with the doc's own
previously-confirmed figure — before treating that as a bug in your
change, check whether the underlying corpus itself grew in the meantime
from a completely unrelated fix landing later in the project's history.

This is a different failure mode from `tracker-prose-is-not-evidence.md`
(a claim that was never actually verified in the first place). Here the
number *was* rigorously derived and correct at the time — real disassembly,
a real corpus-wide scan, a real percentage — but the project kept moving
after that doc section was written, and a later, unrelated fix increased
the record/entry population the same live scan now walks. The old
percentage and the old absolute counts both drift, even though the
mechanism the doc describes is completely unchanged and still correct.

Confirmed on Valkyrie Profile (PSX, `valkyrie` project): `data-structure.md`
§13.3a documented the battle-animation patch-page supplement index as
"1,310/1,311 pages solved (99.9%)," with one specific unresolved case
(slot 1111 record 0) fully enumerated. Re-running the exact same
`collectBattleAnimations` collector (unchanged mechanism, being used only
as a *regression oracle* while porting the same algorithm to a second
platform) measured **1,376/1,394 (98.7%)** instead — 18 unresolved
groups, not 1. The disc-wide supply side was confirmed unchanged (636
containers, 178 unclaimed blobs, matching the doc's own historical
figures exactly) — what grew was the *demand* side: later, unrelated
record-discovery fixes (specifically, a 26-playable-character raw-record
gap-scan addition to `decodeBattleBundle`) increased the total record and
directory-entry population from 545/10,160 to more/11,011. The old "1
unresolved case" claim wasn't wrong when made; the corpus it was measured
against no longer exists in isolation.

**The fix:**
- When a live re-run of an already-documented full-corpus pass disagrees
  with the doc's own headline number, don't assume your current change
  broke something — first check whether a corpus-size proxy (total record
  count, total exported entry count) also differs from what the doc cites.
  If it does, the doc's number is stale from growth, not wrong from a
  regression.
- Verify the *mechanism* is unchanged before writing off the discrepancy:
  re-run with the code as it stood pre-your-change too (revert just the
  file(s) you're touching, e.g. via a scoped `git stash push -- <paths>`)
  and confirm the live number matches your post-change run exactly. If it
  does, the drift is corpus growth, independent of anything you did.
- Update the doc in place with a `> **Correction:**` block giving the new
  live figure and naming the cause (which later fix grew the corpus) —
  don't silently leave a now-wrong headline number sitting next to newly
  contradicting evidence. If the newly-widened residue (the extra
  unresolved cases beyond what was originally enumerated) hasn't been
  individually re-traced, say so explicitly and file it as a fresh,
  narrower follow-up rather than either re-closing the old item or
  silently expanding its scope.
