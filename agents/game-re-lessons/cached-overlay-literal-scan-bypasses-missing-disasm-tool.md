# A missing interactive disassembler doesn't block a literal-immediate census over already-cached overlay/code blobs

**When it bites:** radare2 (or another interactive disassembly MCP server)
is unavailable this session, a TODO/doc item is framed as "blocked on
radare2" for a specific "does code reference constant N" question, and
earlier sessions already extracted/decompressed the relevant code overlays
to `build/cache/<game>/*.bin` (or an equivalent scratch/cache directory).

An interactive disassembler is the right tool for open-ended exploration
(finding functions, tracing control flow, naming call graphs), but a single
targeted question — "does any code load constant N as an immediate?" — only
needs a few dozen lines of hand-rolled opcode decoding, not a full tool.
Confirmed on Valkyrie Profile (PSX, `valkyrie`): with radare2 still
unavailable and several TODO rows explicitly marked "blocked on radare2,"
a ~20-line Python MIPS immediate scanner (`addiu`/`ori reg, zero, N` for a
target constant set) run directly against the project's own already-cached
`codeoverlay_slot*.bin` files (extracted by a prior session, sitting unused
in `build/cache/`) found real, confirmed call sites for three previously-
untraced TOC-slot values in minutes — no tool, no project setup, no
permission gate. A ~90-line purpose-built instruction printer (not a
general disassembler — just enough opcodes to read `addiu`/`ori`/`lui`/
`jal`/`jr`/`lw`/`sw`/branches around a hit) was then enough to confirm each
hit was a real resource-load argument, not a coincidental bit pattern.

Rule: before writing "blocked on [disassembler]" or reaching for a fresh
Ghidra project / escalation, check whether the target binaries are already
sitting decompressed in the project's build cache from earlier sessions,
and whether the actual question is narrow enough (a literal-constant
census, not open-ended exploration) for a small hand-rolled scanner. This is
the same "literal `addiu`/`ori` immediate scan" technique this agent already
uses constantly *with* an interactive tool — it doesn't stop working without
one, it's just slower to write by hand. Escalate to `ghidra-disasm` (fresh
project setup) or wait for the interactive tool only once the question needs
real control-flow tracing, not a value census.
