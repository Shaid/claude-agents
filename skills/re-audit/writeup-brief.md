# Brief: write up codebreaker gap audits as repo docs

Report-only codebreaker gap audits re-derived a project's load-bearing data claims with
independent code and reported which hold, which are wrong, which are unverified, and what to fix.
Nothing has been applied. Write each audit up as a page in the project's `docs/` folder, **one
page per title**. Your prompt gives the repo, the report file(s), the audit date `<date>`, which
claims the orchestrator spot-checked, and the spelling convention.

## Your job
1. Read the project's `AGENTS.md` (and `docs/README.md` if present) for doc conventions and layout.
2. Read the audit report file(s) in full.
3. For each title the report covers, create ONE new file `docs/<game>/audit-<date>.md`, using the
   repo's existing per-game folder name. If a title has none, create `docs/<game-id>/` with the id
   the repo's code/config/data already uses (check read-only). Where the repo groups titles by
   platform instead (e.g. `docs/<platform>/<game>-…`), follow that. If a report covers a family
   and some findings are family-wide, put them on each affected page (a brief cross-reference is
   fine) — every page must stand alone.
4. Each page:
   - Title + status line: "Report-only audit, <date>. None of these corrections have been applied
     yet." and that it was an independent codebreaker re-derivation.
   - **Summary verdict** (2–5 bullets: what's solid, what's wrong, biggest risk).
   - **Claims confirmed** (with the evidence/metric the audit used).
   - **Claims wrong or overstated** — what the docs say (doc path/section), what the audit found,
     the evidence (counts, offsets, exact-consumption results, controls), and the fix.
   - **Unverified / open** (incl. what the audit could not settle or was blocked from checking).
   - **Recommended corrections**, ranked cheapest/highest-value first, with file:line where given.
   - **Checks for the user to run in play** (she runs emulators herself; never suggest agents do).
   - **Process notes** (tautological tests, derived data under `data/`, TODO hygiene) if any.
   - A note that the audit's probe scripts lived in a non-preserved scratch dir (cite the
     subfolder name only as provenance).
   Keep every number, offset and file:line exactly as the report gives it. Do not invent
   evidence; do not soften or strengthen verdicts. Mark the orchestrator's spot-checked items as
   "spot-checked in the main session".
5. Plain, specific prose; tables where they help. Match the repo's spelling convention.

## Wording rules
- Derived output under `data/` (e.g. `data/extracted/`): not a "violation" — it is the legacy
  layout from the old seer default; recommend migrating to `build/cache/<game>/` per seer
  `docs/architecture-overview.md` §2.
- Never copy key material, decryption keys/IVs, passcodes or decrypt command lines into a page.
  "Decrypts with the publicly known platform key" is fine without the key.

## Hard rules
- Create NEW files only. Do not edit any existing file (specs, TODO, plan, READMEs, indexes,
  sidebars, code). If a docs index should link the pages, say so in your reply instead.
- Never write under `data/`, `public/`, `www/`, or outside the assigned repo.
- No emulators; don't re-run the audits (read/grep repo files only to confirm paths).
- No git operations at all (add, commit, stash, checkout). No lesson/credit files.

## Reply
The files you created (absolute paths), one line each with the title, plus anything you couldn't
place or any discrepancy in the report. Keep it short.
