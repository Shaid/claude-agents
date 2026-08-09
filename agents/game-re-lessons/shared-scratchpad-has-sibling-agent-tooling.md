# Check the shared scratchpad for a concurrent sibling agent's already-built tooling before rebuilding it

**When it bites:** the task brief mentions a separate, concurrently-dispatched
agent already working the same binary/game (e.g. "a separate agent owns X,
don't touch it" — the concurrency-boundary framing this mission's own
autonomy contract uses), and the next step would otherwise be building a
disassembler, extracting a code/data blob, or writing an opcode table from
scratch.

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
race risk and are safe, useful reuse.
