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
| `re-learn` skill | `skills/re-learn/SKILL.md` | Opus | The learning loop: distills durable lessons back into `agents/game-re.md` |

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

### Learning loop

After any task that produced a generalizable lesson, the agent invokes
`re-learn` (harvest mode) to fold it into its own definition: the prior-art
corpora table, the hard-won-pitfalls list, tooling caveats. Pointed at an
unfamiliar project (`re-learn: learn from ~/Development/<project>`), it
absorbs that project's solved formats as prior art first. The skill curates
rather than logs — lessons must generalize, have been expensive, and be
verified; per-game details stay in each project's `docs/`. Self-edits show up
here as git diffs: `git -C ~/.claude diff agents/game-re.md`.

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
git -C ~/.claude log --oneline agents/game-re.md   # how the brain evolved
git -C ~/.claude diff agents/game-re.md            # pending self-edits
git -C ~/.claude checkout -- agents/game-re.md     # reject a bad lesson
```

Commit after reviewing a harvest you agree with; revert the ones you don't.
