# A concurrent sibling agent can be editing the same shared-decoder repo file live, not just leaving static scratchpad artifacts

**When it bites:** the task brief says a separate, concurrently-dispatched
agent is working a related target that shares an engine/format family with
yours (e.g. "if either of you crack the shared format, it helps the other"),
and you `Write` a new decoder module to the project's shared decode-library
path (`src/data/formats/<format>.ts` or equivalent) — then a subsequent
`Read`/`Edit` on that exact path reports content you never wrote, or an
`Edit` fails with "file has been modified since read."

## What happened

Two concurrently-dispatched sessions in the same Chimera project (one on
Fire Emblem Warriors, one on Fire Emblem: Three Houses) both independently
identified that their target's model format was the shared Koei Tecmo G1M
container, and both wrote their own from-scratch TypeScript port to the
*same* canonical path, `src/data/formats/g1m.ts` — the correct shared
location per this project's "decode once, consume everywhere" convention,
not a coincidence of naming. This is meaningfully different from
`shared-scratchpad-has-sibling-agent-tooling.md`: that lesson covers
*static* artifacts (scripts, dumps) sitting in a session-scoped scratchpad,
explicitly noted as carrying no race risk. A shared, canonically-named repo
source file is not scratch — it's live, contested state, and the other
agent kept editing it (bug fixes, API refinements) across several turns
while this session was also actively building against it.

The first `Write` landed, then vanished — overwritten within the same turn
sequence by the sibling's own version, mid-session, more than once (each
follow-up `Edit` attempt reported "file has been modified since user/other
process, re-read before editing"). The sibling's version turned out to be
independently correct (verified field-for-field against the same real
bytes) with one live bug the sibling fixed themselves moments later, and a
richer API shape (multi-skeleton support, a `parseG1MAt`/`parseG1M` split)
that the original session's own version lacked.

## The fix

1. **Never assume a `Write` to a shared canonical path is your file to keep
   iterating on** when a sibling agent's task brief mentions the same
   format/engine family — re-`Read` before every `Edit`, every time, not
   just after an explicit tool error.
2. **Don't fight over ownership; verify and adopt.** Diff the current
   on-disk content against your own independently-derived byte-level
   understanding of the format (not against your first draft) before
   deciding whether to patch a bug into it or defer to it as-is. If it's
   independently correct, rewrite your *consumer* code (the glTF/asset
   exporter, in this case) against its actual exported API rather than
   reverting the shared file to your version — reverting a sibling agent's
   live, in-progress work on a shared file it's actively iterating on
   destroys real concurrent progress for no benefit, since both sessions
   converge on the same ground truth anyway.
3. **Small, well-justified fixes to the shared file are fine** (a real bug,
   confirmed against real bytes) — normal collaborative correction, not
   "reverting." Expect it to keep changing on its own between your edits
   regardless.
4. Build any downstream code (exporters, pipeline stages) as a **thin
   consumer of the shared module's actual current exports**, re-checking
   `tsc --noEmit` after every re-read — the shared file's field names,
   struct shapes, and even function signatures may shift more than once
   across a session as the sibling iterates.
5. **When you must legitimately add your own, non-overlapping content to
   the same file** (not a duplicate/competing decoder for the same format —
   a genuinely different finding that happens to belong in the same module,
   e.g. two sessions each adding their own game's variant of a shared
   renderer), prefer surgical, string-anchored edits (`Edit`'s targeted
   replace) over a full-file `Write`/rewrite, even when your own change
   spans a large new section. Confirmed on Final Fantasy VII/VIII/IX
   (`siren` project): one session added new FF7-specific rendering
   functions to `tools/shared/akao-render.ts` while a concurrent session
   added unrelated FF8/FF9 instrument-table logic to the same file's
   existing section — both landed with zero data loss because neither
   session ever rewrote the whole file, only inserted/edited their own
   targeted regions. A full-file overwrite from either side would have
   silently destroyed the other's concurrent work.
