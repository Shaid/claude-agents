# A blind, code/data-blind linear decode of a fixed-width-ISA corpus overstates rare/exotic instruction-class counts — use control-flow-verified reachability instead

**When it bites:** censusing instruction-class usage (FPU/COP1, syscalls,
breakpoints, branch-likely, "hardware register access," any "does this
corpus ever do X" question) across a corpus of small compiled-code blobs
with no symbol table and no code/data separation markers (arcade ROM
regions, PS1/N64/PSP MIPS resource blobs, ARM/PowerPC overlay chunks) —
especially right before treating a nonzero count in an "exotic"/alarming
bucket as evidence of a real capability (floating point, self-modifying
code, direct hardware I/O) the interpreter or emulator needs to support.

On a fixed-width ISA, a from-scratch hand-rolled decoder never "desyncs"
the way a variable-width decoder does (see
`linear-disasm-desyncs-through-inline-data.md` for that failure) — every
N-byte word always decodes to *some* instruction under a table lookup, so
a blind linear walk completes without error and looks trustworthy. But
when the blob embeds literal data inline in the code stream with no
separating marker (an internal jump/dispatch table, small constant pools,
a colour palette), those data words get decoded as if they were real
instructions too. Because rare opcode classes (COP1/FPU, `syscall`,
`break`, MIPS-II+ branch-likely, `jalr $zero,$zero`) occupy a small
fraction of the encoding space, essentially any real data blob is likely
to coincidentally trip a few of them — and because they're individually
alarming ("this uses floating point!" / "this does a hardware register
write!"), it's tempting to report them as findings rather than question
the decode.

Confirmed on Valkyrie Profile (PSX, `valkyrie`): a blind linear MIPS
decode of 655 small (~10 KB) enemy/party AI "behaviour module" blobs
found 105 COP1/FPU instructions, 112 branch-likely (MIPS II+, impossible
on the real R3000A CPU), 112 `syscall`, 470 `break`, and 4,731 "hardware
I/O" hits (`lui reg,0x1f80`). Every one of these numbers **collapsed by
95-100%** (to 4, 2, 2, 419 [now confirmed real — see below], and 0
respectively) when the exact same corpus was walked by real control flow
instead: a worklist/BFS starting from each blob's actual entry point(s)
— including any statically-resolvable internal dispatch-table handler
addresses, not just the single nominal entry offset — following every
conditional-branch target (both directions), unconditional-jump target,
delay slot, and `jal`/resolved-`jalr` self-call, while never following
into a region already known to be a literal data table. The residual
non-zero counts even after this fully explained themselves: the 4
remaining COP1 hits were 100% confined to a small (46-instruction)
literal colour-constant blob inside 4 sibling files whose *dispatch
table's own location* fell just outside this pass's search window (a
separate, narrow methodology gap, not a code anomaly); the 419 remaining
`break` instances were then independently confirmed to be the standard
GCC/SN-Systems compiler `div`-by-zero/overflow safety-check idiom, not
exotic trap usage.

**Fix:** for any instruction-class or call-target census over a
compiled-code-blob corpus with no symbol table, default to control-flow-
verified (reachability) disassembly, not a blind/linear decode of every
byte offset:

1. Seed a worklist with the blob's real entry point(s). If the format has
   a known "action id → handler table" or "state → handler table"
   convention (common in per-object AI/behaviour scripts compiled to
   native code), locate that table (often a `lui`+`addiu`-formed absolute
   address near the very start, pointing to N words inside the blob's own
   bounds) and seed every non-zero handler address too — these are
   additional real entry points a pure entry-offset-0 walk will never
   discover on its own.
2. Walk both branch-taken and fallthrough successors for conditional
   branches, the target (and, for calls, the fallthrough) for
   unconditional jumps/calls, and the delay slot of every branch/jump —
   never treat inline data as an instruction to decode.
3. Mark located tables (dispatch tables, jump tables) as data ranges the
   walker must never step into directly.
4. Only classify/count instructions actually visited by this walk. Report
   the blind-linear numbers only as a documented "before" contrast if
   useful for showing the effect size — never as the final finding.

This generalizes past MIPS/PSX to any fixed-width ISA (ARM, PowerPC,
SuperH) disassembled from raw bytes with no symbol table, and is the
correct default even when nothing about the corpus looks suspicious yet —
the failure mode produces no error and no visible desync, so it will not
announce itself.
