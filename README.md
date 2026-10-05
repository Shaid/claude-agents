# game-re — an autonomous game reverse-engineering agent

A [Claude Code](https://claude.com/claude-code) agent system for reverse
engineering classic game data files and executables, built for
[seer](https://github.com/Shaid/seer)-framework projects. Ask it to
*"scan the game data in `<dir>` and work out the structure"* and it will
triage the files, trace the game's own loaders in disassembly, test decode
hypotheses, verify against ground truth, publish web-native assets, and write
byte-level format documentation — prompting the user only when genuinely
blocked.

Distilled from reverse-engineering **Black Crypt** (Amiga), with prior art
from the Eye of the Beholder series, War in Middle Earth, the Excalibur
series, Conan, Warriors of Legend, Dune, and KGB.

> This repo lives at `~/.claude` on purpose, with a strict whitelist
> `.gitignore`: only the files below are tracked — never credentials,
> sessions, memory, or settings. The reason: the `re-learn` skill lets the
> agent **edit its own definition in place**, and rooting the repo where the
> live files live means every self-modification lands in the working tree as
> a reviewable, revertable diff.

## The pieces

| Piece | File | Model | Role |
|-------|------|-------|------|
| `game-re` agent | `agents/game-re.md` | Sonnet | The workhorse: full RE loop, orchestrates everything below |
| `re-codebreaker` skill | `skills/re-codebreaker/SKILL.md` | Opus | Escalation for hard *bounded* sub-problems (forked specialist) |
| `re-oracle` skill | `skills/re-oracle/SKILL.md` | Fable | Last-resort escalation: whole-corpus synthesis, contradictions (forked specialist) |
| `re-learn` skill | `skills/re-learn/SKILL.md` | Opus | The learning loop: distills durable lessons into the knowledge base below |

### Escalation ladder

`game-re` runs on a fast model and does the routine work itself. When a
sub-problem defeats it (two well-formed decode hypotheses failed, a
decompressor won't crack, a disassembly trace keeps dead-ending), it forks
`re-codebreaker` on Opus with a self-contained brief. Problems that defeat
*that* — contradictory evidence, whole-corpus synthesis — go to `re-oracle`
on Fable. Both forks run with the full `game-re` system prompt (same
conventions, same verification bar), just a bigger engine. Specialist
findings are re-verified by the orchestrator before anything is marked
confirmed.

### Knowledge base

`agents/game-re.md` is loaded on every invocation, so it is kept to a contract
plus one-line indexes (≤ 30 KB, enforced). Everything else is read on demand:

| Path | Read when | Budget |
|------|-----------|--------|
| `agents/game-re-corpora/<project>.md` | first thing in every task in that project | ≤ 8 KB summary |
| `agents/game-re-corpora/details/<project>.md` | evidence behind a specific item | — |
| `agents/game-re-lessons/INDEX.md` → `<lesson>.md` | before trusting a decode (by category or grep) | ≤ 8 KB per lesson |
| `agents/game-re-lessons/_archive/` | rarely — verbatim instance logs of condensed lessons | — |
| `agents/game-re-method/`, `agents/game-re-tooling/` | the technique / platform at hand | — |

`python3 ~/.claude/skills/re-learn/check.py` validates budgets, index ↔ file
sync, and cross-references.

### Learning loop

After any task that produced a generalizable lesson, the agent invokes
`re-learn` (harvest mode). Because many sessions run in parallel, a harvest
never edits the shared files: it writes candidates to the git-ignored
`agents/game-re-inbox/`, then tries to take a lock
(`agents/.re-learn.lock/`). Whoever holds the lock curates the whole inbox —
merging into lessons/corpora/method/tooling under the bar (generalizes, was
expensive, verified), running `check.py` until clean, and committing **only the
paths it touched**. Pointed at an unfamiliar project
(`re-learn: learn from ~/Development/<project>`), it absorbs that project's
solved formats as prior art. `re-learn curate` drains a backlog by hand.

## Method (what the agent actually does)

1. **Inventory & triage** — sizes, magic, strings, entropy, record-structure
   scans, sibling-file diffs, file catalogs.
2. **Find the reader, not the format** — the game's own loader/decompressor/
   blitter code is the authoritative spec; guessing dimensions is the last
   resort.
3. **Hypothesis probes** — throwaway Python (numpy + PIL) renders, greyscale
   first until the palette is independently confirmed.
4. **Ground truth before "decoded"** — emulator screenshots, cross-platform
   ports, third-party decoders, or zero-deviation structural invariants;
   verification is quantified, never "looks right".
5. **Emulate hostile decompressors** — run the game's own routine under an
   emulator core instead of debugging a hand-port.
6. **Promote** — verified probes become committed extractors using the
   project's shared decode libraries, pixel-exact regression-checked; findings
   land in `docs/<game>/<platform>/data-structure.md`, assets in
   `public/assets/<game>/<platform>/`.

## Usage

From a seer-framework project in Claude Code:

```
use the game-re agent to scan the game data in data/eotb2/amiga and work out the structure
```

Direct skill invocations also work:

```
/re-codebreaker <self-contained brief for one hard sub-problem>
/re-oracle      <brief including the failed codebreaker attempt>
/re-learn       learn from ~/Development/wyrm
```

## Requirements

- **Claude Code** with agent/skill support (`model:`, `context: fork`,
  `agent:` frontmatter).
- A **seer-framework project** (four-zone layout: `data/`, `tools/`, `src/`,
  `public/assets/`) — the agent's output conventions assume it.
- Optional but heavily used when present:
  - `ira-disasm` and `radare2-amiga` skills (static/interactive 68k work)
  - **radare2 MCP** (interactive disassembly, any architecture)
  - **amiberry MCP** (Amiga emulator: screenshots, memory dumps, breakpoints —
    the ground-truth machine)
  - **openground MCP** with the `amigadocs` library (HRM/RKRM references)

## Versioning the agent's brain

```sh
git -C ~/.claude log --oneline -- agents skills   # how the brain evolved (re-learn: commits)
git -C ~/.claude show <hash>                      # audit one curation pass
git -C ~/.claude revert <hash>                    # reject a bad curation
ls ~/.claude/agents/game-re-inbox/                # candidates still waiting for curation
python3 ~/.claude/skills/re-learn/check.py        # budgets + integrity
```
