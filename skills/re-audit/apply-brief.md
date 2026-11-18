# Brief: apply a title's audit findings

Each title has an audit page in its repo (`docs/<game>/audit-<date>.md`, or the repo's own layout)
and the full source report at the path your prompt gives. You own the titles named in your prompt
— nothing else. Your prompt may override the WIP rules below (e.g. "proposals only"); the prompt
wins.

## Goal
Turn each verified finding into the right durable change, in this order of value:
1. **Code/data bugs with a clear fix** (wrong offset/field/bias, truncation, bit order, dropped
   records, stale published output). Fix the decoder/exporter, add or rewrite a test **that can
   fail** — real data where available (skip cleanly when absent) plus a null control that must
   fail (see `~/.claude/agents/game-re-lessons/check-that-cannot-fail-is-not-evidence.md`) —
   regenerate the affected outputs scoped to your title, and re-verify the audit's metric yourself.
2. **Doc corrections**: in the format spec add a dated `> **Correction (<today>):**` block where a
   premise was overturned (keep the old text as a documented dead end), fix counts/offsets/labels,
   upgrade evidence the audit proved stronger, demote "confirmed" claims that rested on
   tautological checks.
3. **TODO.md** per seer convention (`~/Development/seer/docs/corpus-onboarding.md` §5): one current
   row per open item; delete solved rows (incl. `fixed`/`resolved`/`closed`); add rows for
   untracked unknowns the audit found; no changelog or narrative blocks. If there is no TODO.md,
   create `docs/<game>/TODO.md` with columns `ID | Status | Question | Evidence | Updated`.
4. Stale status pages / READMEs the audit flagged: fix or note.

**Re-verify before changing.** The audit is strong evidence, not infallible. If your check
disagrees, don't apply that item — record the disagreement (with your numbers) in your reply and
the changes file. Say which audit figures you took on trust rather than re-ran.

## Changes file (required)
When a title is complete, write `<audit page name>-changes.md` next to its audit page. Contents:
date; one line per finding with its outcome (applied / partly / deferred / disagreed / no change
needed); for applied items the files changed, commit hash and the before→after metric you
verified; tests run and results; deferred items with the TODO row id now tracking them; proposed
edits for files you could not touch (quoted old→new or a unified diff against the working copy,
with evidence and verdict); in-game checks left for the user. Commit it with the title's changes.
Don't edit the audit page except to add a one-line link to the changes file at the top.

## Scope limits — deliberately conservative
- Don't migrate derived data from `data/extracted/` to `build/cache/` unless it is a one-line path
  change local to your exporter and its readers; otherwise add/keep `<game>-build-cache-migration`.
  Never delete existing derived data.
- Big new extractors (whole untracked content families) are out of scope: add TODO rows with the
  audit's pointers. Small, cheap ones on an already-proven codec may be done if time allows.
- **User WIP is untouchable.** Before editing any file, check `git status`. If a file you'd change
  has uncommitted changes you didn't make (or is untracked and not yours), do not edit it — put the
  exact proposed change in the changes file. If a *sibling agent* holds a file, say so: the
  orchestrator applies those leftovers once the sibling has committed.
- Shared files (e.g. `tools/shared/*`) may be touched by sibling agents in the same repo: keep
  edits minimal, additive where possible, re-read before editing, and run the other titles' tests
  if you change shared behaviour. Fixing shared upstream code (e.g. a seer package) is allowed only
  for a confirmed bug, with a test, committed in that repo by explicit path — and say so loudly.
- No emulators. No network requests to game services. Never write into `data/` except
  regenerating outputs the pipeline already writes there. No decryption; no key material anywhere.
- Scratch probes go in the scratch folder your prompt gives, never in the repo.

## Git
Commit per title (or tight group), **only your own paths**: `git add <explicit paths>` +
`git commit`. Never `git add -A`/`.`; **never stash, reset, checkout or restore**. If the index is
locked by a sibling, wait and retry. Message style `fix(<game>): …` / `docs(<game>): …`, ending
with the commit attribution lines given in the conversation. Don't push. Run the project's relevant
tests (narrowest first) before committing and report the results; a test that only times out
under load is not your regression — say so.

## Reply
Per title: applied (commit hashes) with verified metrics, deferred (why, TODO id), disagreements
with the audit, WIP files you needed but didn't touch (and where the proposed diff is), test
results, in-game checks for the user. Keep it tight.
