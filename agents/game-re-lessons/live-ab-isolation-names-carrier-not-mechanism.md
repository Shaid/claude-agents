# A live A/B isolation ("removing X removes the crash") names the carrier, not the mechanism

**When it bites:** a live test has cleanly isolated one installed variable
(a mod, a patch layer, an archive edit, a data file) as "the cause" of a
crash, and the write-up is about to attribute the crash to that variable's
*own mechanism* — its loading path, its container quirk, an unusual field
in its header — before checking what content the variable merely *carries*.
Also: the crash's fault address + LR match an already-root-caused earlier
crash exactly, and a *new* mechanism is being theorised for it.

## What went wrong

Fire Emblem: Three Houses (Switch, `chimera`), 2026-09-02: six pipeline-
built PACKs were installed through two carriers — character hijacks on the
ordinary `patch4` override path, and an edit of the New Attire DLC's own
archive (a genuinely different AOC-merge load path). The game crashed. The
hijacks were disabled first; the crash persisted. Removing the DLC edit
removed it; two clean runs confirmed. The DLC edit was written up as the
cause, first via its loading path, then via its "non-standard 9,968-byte
slot 19" (a real oddity that had been flagged as a risk beforehand — which
made it a satisfying answer). A `TODO.md` row was closed as RESOLVED on that
basis.

Both were wrong. The DLC edit was simply the *only remaining reachable copy*
of a pipeline-built PACK after the hijacks were disabled; the crashing build
of it had a standard 8-byte slot 19 (the 9,968-byte one belonged to an
earlier build that had loaded fine through the identical path); and the
hijacked PACKs had crashed with the same signature hours earlier on the
`patch4` path. The real cause was inside every pipeline-built PACK
(`unknown-constant-field-is-engine-grammar-load-bearing.md`). The
isolation was correct; the attribution skipped a step.

## The fix

1. **After an isolation, enumerate what the removed variable *carries*** —
   which assets/records become reachable only through it — and check that
   content against the whole timeline: does it (or its family) appear in
   every crash and in no clean run? An install log with timestamps is
   enough; here it showed "a pipeline-built PACK is reachable" was the one
   variable common to every crash and absent from every clean run, while
   "DLC path" and "slot 19" were each present in a clean run.
2. **Distinguish "the path" from "the payload" with the cheapest
   counterexample**: the same payload through a different path (it crashed
   there too → payload), or a different payload through the same path (it
   loaded → not the path). Both existed in the logs before the wrong
   write-up.
3. **An identical crash site is evidence for the same *null*, not the same
   *story*.** When fault VA + LR match a previously root-caused crash
   exactly (here: the same unguarded dereference of a NULL parser result
   as a slot-18 bug fixed days earlier), enumerate *every* reason that
   pointer can be NULL — each parser handler's false-return — before
   theorising a new mechanism (a lazy-singleton race was proposed and
   pursued for a day). See `shared-landing-pc-reached-by-disjoint-branches.md`
   for the same principle applied to a PC rather than a fault address.
4. **Don't close the status row on the isolation alone.** "Removing X
   fixes it" is a status of `blocked:root-cause`, not `RESOLVED`, until the
   mechanism is shown at the instruction level or by a counterexample.
