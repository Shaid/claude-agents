# A linear byte-scan for a target opcode/call in a bytecode VM can find a hit real execution never reaches

**When it bites:** hunting a small per-record bytecode VM (an ECL/script/
event-stream format) for whether a specific opcode or call (a resource load,
a state write, a "does this record ever do X" question) is reachable from a
record's entry point, and the check so far is "scan forward from the entry
point/header address and see if opcode X ever appears" — especially right
before treating that appearance as proof the record's real execution path
reaches it.

A flat forward/linear scan over a bytecode stream finds every byte pattern
that looks like the target opcode, regardless of whether real control flow
ever lands on that byte. Unlike native-code disassembly desync (see
`linear-disasm-desyncs-through-inline-data.md`, a *false-negative* failure
from losing instruction alignment through inline data), this is a
*false-positive* failure that needs no misalignment at all: the scanned
bytes can be perfectly valid, correctly-aligned opcode+operand groups that
are simply on a branch never taken, inside a subroutine never called from
this entry point, or past an unconditional jump/return that real execution
never falls through.

Confirmed on the SSI Gold Box ECL bytecode format (`crawl` project,
`tools/shared/goldbox-ecl.ts`): an initial linear scan for Pool of
Radiance's "LOAD PIECES" opcode from a level's block start found a hit: a
worklist-based reachability walk that actually followed the block's real
`GOTO`/`GOSUB`/`ON GOTO`/`ON GOSUB` targets (not linear fallthrough) from
the same start point found **zero** reachable hits — the linear scan's
"hit" sat in bytes never actually reached by any real control-flow path
from that entry point.

**Fix:** build a worklist-based CFG walker, not a linear scan, for any
bytecode reachability question. Seed the worklist with the real entry
point(s); on each visited instruction, decode its own opcode + operand
byte-consumption (never assume a fixed instruction width), and push the
real successor set: unconditional jump targets, both jump-table dispatch
targets (a jump table also has its own row-selection width — don't assume
its declared size field is trustworthy if it's ever proven to consume a
different number of operand bytes than declared) and control-flow
fallthrough for a subroutine call, and ordinary linear fallthrough
otherwise. Treat `RETURN`/`EXIT`-class opcodes as walk-terminal, not
skippable. Then use the *visited set itself* as a self-consistency oracle
when there's no external reference decoder to check byte-exactness against
directly: zero unknown opcodes and zero desyncs (every decoded instruction
starts exactly where the previous one's declared operand consumption says
it should) across the whole visited set is strong evidence the VM's own
opcode table and operand-width rules are right, even without ground truth
for that specific record's *content*.
