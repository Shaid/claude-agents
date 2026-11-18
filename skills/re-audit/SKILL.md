---
name: re-audit
description: Gap-audit what a seer-framework project believes it knows about its game data, then (on request) write the findings up and apply the corrections. Orchestrates report-only re-codebreaker audits per title/engine family, writes one audit page per title into the repo's docs/, applies verified fixes title by title with a per-title changes file, and harvests the recurring lessons. Use for "audit <project>", "run the codebreaker audit over ../<repo>", "how solid is what we know about <game>", "write the audit findings up", "apply the audit findings". Runs in the main session (it spawns and coordinates background agents); it does not decode formats itself.
argument-hint: "[audit|writeup|apply|harvest] <repo path(s) or game ids> [notes]"
---

# re-audit — gap audit → write-up → apply → harvest

You are the **orchestrator**. The work is done by background agents; your job is
scoping, briefing, spot-checking, relaying, protecting the user's uncommitted work,
and closing the loop. Each phase runs only when the user asks for it — an audit
request is report-only until they say "write it up" / "apply it".

Reference briefs (read the one for the phase you are in, and point agents at it):
- `audit-brief.md` — the report-only codebreaker audit (phase 1)
- `writeup-brief.md` — turning reports into per-title audit pages (phase 2)
- `apply-brief.md` — applying findings with changes files (phase 3)

Keep a scratch folder for the run (your session scratchpad): save each agent's final
report verbatim as `<scratch>/reports/<agent-or-title>.md` as it arrives — the agent
transcripts are not durable, and every later phase reads from these files.

## Phase 0 — scope (every phase starts here)

For each repo: read `AGENTS.md`/`README`/`docs/` layout, list `data/<game>/<platform>/`,
and run `git status --short` + `git log -1`. Classify the repo:

| State | Treatment |
|---|---|
| Clean / small, unrelated WIP | normal: agents edit and commit their own paths |
| WIP in some files the audit touches | agents must not edit or stage those files; fixes for them become **proposed diffs** in the changes file |
| Mostly WIP (hundreds of modified files, old last commit) or a whole title untracked | **proposals only**: agents commit nothing; changes file left uncommitted |

Snapshot the WIP list to `<scratch>/reports/<repo>-WIP.txt` and hand agents the path —
don't retype it. The user may grant explicit exceptions ("you may edit my uncommitted
X"): then agents edit but **never commit** those files (her hunks would ride along).
Approval for one repo or file set does not extend to another.

Group titles into agents by **engine family / shared format docs**, not one agent per
repo: a family audited together catches cross-title contradictions and shared-code bugs.
Note data dirs with no docs (uncovered titles, extra platforms that are free oracles)
and give them to the nearest family agent as a "what's here, is it usable" item.
Keep concurrency to what the user's workflow size allows (default: under ~10 agents).

## Phase 1 — audit (report-only)

One background agent per family: `subagent_type: game-re`, `model: opus`,
`run_in_background: true`, prompt beginning "Read ~/.claude/skills/re-codebreaker/SKILL.md
first and operate as it says. Then read and follow <this skill>/audit-brief.md" plus:
project root, titles with data/doc paths, shared docs, cross-platform oracles to use,
the WIP list path, the scratch folder for probes, and any hard limits.

**Briefing hazards** (each caused a real failure):
- Never ask an agent to decrypt with the user's keys or read key files — the request
  is refused outright. Say "work only from data already on disk in decrypted form; do
  not decrypt; record no key material".
- Agents must not drive emulators; the user runs live checks herself.

As each report lands: save it, **spot-check the headline claim yourself** with a quick
byte-level look (one offset, one count) before relaying, and tell the user in plain
language what is wrong, what holds, and what they could check in play. Mark anything
you could not reproduce as unverified (e.g. a cited constant that isn't in the binary).
Strip key material, decryption keys/IVs and decrypt command lines from anything you
relay or save.

## Phase 2 — write-up (new files only)

On request, one writer agent per repo (`general-purpose`, a cheaper model is fine):
"Read <this skill>/writeup-brief.md and follow it", plus the report paths, the audit
date, which claims you spot-checked, and the repo's spelling convention.
Output: one `docs/<game>/audit-<date>.md` per title, nothing else edited, no git.
Check the pages for leaked key material afterwards (`grep` the key prefix).

## Phase 3 — apply (in the order the user gives, usually the audit order)

Work **one repo at a time**; inside a repo, one `game-re` agent (default model) per
title or tight family, in parallel: "Read <this skill>/apply-brief.md and follow it",
plus repo, titles, audit page + full report path, headline (with what you spot-checked),
the WIP list and any WIP mode override from Phase 0, and the sibling agents in the repo.

When each agent reports, relay it. When a repo's agents are all done:
1. `git status` — anything left that's neither the user's WIP nor intended? Agents
   sometimes land a hunk in a sibling's commit (harmless; note it) or leave edits
   uncommitted when a sibling held the file.
2. **Leftovers**: items an agent skipped only because a *sibling agent* had the file
   open (not user WIP) — apply them yourself now, small and exact, with a dated
   correction note, and update that title's changes file to "applied afterwards".
3. Run the repo's full test suite. A failure that passes in isolation and only times
   out in the full run under load is a timeout, not a regression — confirm by running
   it alone (and, if needed, on the pre-change commit in a temporary worktree, then
   remove the worktree). Report it; don't silently raise timeouts.
4. `git stash list` must be unchanged — agents are told never to stash; check.
5. If an agent fixed shared upstream code (e.g. a seer package), say so explicitly:
   every consumer of that package inherits it.

Then move to the next repo.

## Phase 4 — harvest

After the sweep (or a large batch), run `Skill: re-learn` over the reports for the
recurring patterns (tautological checks, missing null controls, sampled-subset rates,
unread container regions, byte-identical ports as oracles, fan-patched corpora, …).
Separately fix **stale corpus summaries** the apply agents flagged
(`~/.claude/agents/game-re-corpora/<project>.md`): small edits under the curator lock
(`~/.claude/skills/re-learn-curate/lock.sh acquire manual` → edit → `python3
~/.claude/skills/re-learn/check.py` → commit only those paths → `lock.sh release <token>`).
If the audits showed a framework-level convention conflict (e.g. a scaffold default the
audits kept flagging), raise it with the user as a seer convention change rather than
"fixing" it per repo.

## Relaying results

Per title: what changed (with commit hashes), the before→after metric that proves it,
what was deferred and which TODO row tracks it, disagreements with the audit, fixes
left as proposals for the user's WIP (and where the diff is), and the in-game checks
for the user. At the end of each repo: test-suite result and anything left in the tree.
