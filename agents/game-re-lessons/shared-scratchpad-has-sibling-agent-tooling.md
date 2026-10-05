# Check the shared scratchpad for a concurrent sibling agent's already-built tooling before rebuilding — or deleting — it

**When it bites:** the task brief mentions a separate, concurrently-dispatched
agent already working the same binary/game (e.g. "a separate agent owns X,
don't touch it" — the concurrency-boundary framing this mission's own
autonomy contract uses), and either (a) the next step would otherwise be
building a disassembler, extracting a code/data blob, or writing an opcode
table from scratch, or (b) about to run any deletion/cleanup command
(`rm -rf`, moving, overwriting) against a shared scratch directory while
tidying up your own throwaway probes at end-of-task.

## What happened

Auditing ceres's FFVI AKAOSNES V4 renderer against VGMTrans's full reader
required disassembling several real SPC700 VCMD handlers to check candidate
fixes against actual ROM bytes. A prior pass in this same overall session (a
concurrently-dispatched agent working the loop-nesting VCMDs, sharing the
same session-scoped scratchpad directory) had already built and *validated*
exactly this: a from-scratch SPC700 disassembler (cross-checked
instruction-for-instruction against several already byte-confirmed routines
before being trusted on new code) plus a raw dump of the uploaded driver
blob at its correct ARAM-aligned byte offset. Both were sitting in the
scratchpad directory, unrelated in name to the current task but discoverable
with a plain `ls`. Reusing them turned what would have been a from-scratch
disassembler build (a nontrivial, error-prone undertaking — the earlier
session's own docs describe several correction passes to get their table
right) into an immediate lookup-and-disassemble step, freeing the rest of
the session's budget for actually resolving the six real VCMD gaps this
audit was for.

## The fix

Before building any nontrivial static-analysis tool (disassembler, opcode
table, container parser) for a target, `ls` the scratchpad directory first
if the task brief indicates another agent has been or is concurrently
working the same binary in the same session. A validated tool built by a
sibling pass is strictly better to reuse than a fresh build: it's already
been cross-checked against known-good output (per this mission's own
verification discipline), and rebuilding it from scratch duplicates that
validation work for no benefit. This is a different concern from
`shared-tool-session-clobbered-by-fork.md` (which warns against trusting a
*stateful* tool's live state after a fork) — static artifacts (scripts,
extracted blobs, dumped tables) left in the shared scratchpad carry no such
race risk and are safe, useful reuse. If the sibling agent is instead
actively writing to a shared *repo* file (not scratch) at the same time —
e.g. both sessions independently landing on the same canonical decoder
path for a shared format — that's a live race with a different fix; see
`concurrent-sibling-agent-edits-shared-repo-decoder-live.md`.

**Second confirmed instance:** Black Tiger's (arcade, `kolbold`) audiocpu
Z80 sound-driver event-grammar work found a prior session's leftover
`radare2 -a z80` full linear disassembly text dump (~3000 lines) and its
matching assembled ROM-region `.bin`, both keyed to the exact same ROM
file this session needed, sitting in the shared scratchpad under an
unrelated filename. Using the dump directly (plus targeted raw-byte
re-reads for the handful of spots where the linear disassembly desynced
through embedded data tables) skipped re-running the disassembler
entirely and let the whole session go straight to tracing control flow.

**Third confirmed instance — the destructive-cleanup direction (`crawl`,
Elvira/Elvira 2/Waxworks AGOS session, with two other agents concurrently
working Bard's Tale and Dungeon Master in the same repo):** at end-of-task,
following the mission's own "clean up throwaway probes, don't leave them as
committed-looking deliverables" convention, `rm -rf tools/.scratch/` was run
against what turned out to be a directory *shared* across all three
concurrent agents in the session (not scoped to the AGOS work), without
first `ls`-ing it to check for sibling-agent content. It held two other
agents' in-progress probe scripts, a disassembly text dump, and reference
source files pulled for their own tasks — none of it git-tracked, so none of
it was recoverable. The affected agents had to be notified after the fact
via `SendMessage` so they'd know to regenerate/refetch anything load-bearing
that was lost, rather than silently discover missing files later. The fix is
identical in direction to the reuse case above, just applied before a
destructive command instead of before a build step: `ls` (and skim for
filenames/content unrelated to your own current task) before deleting
*any* scratch path shared across a session with concurrent siblings — the
same directory that's safe to freely reuse from is not safe to freely
delete.
