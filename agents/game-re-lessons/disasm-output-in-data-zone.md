# Disassembly tool output can silently land in the read-only data zone

**When it bites:** after delegating a disassembly pass (IRA/radare2, directly
or via a sub-agent) on an executable that lives in `data/<game>/<platform>/`,
before trusting that directory's file inventory/count for anything.

IRA's `-config`/`.cnf` workflow, and some sub-agents driving it, default to
writing their `.cnf` config file (and sometimes the `.asm` output too) into
whatever directory they were invoked from or found the target binary in —
which, for a seer project, is often `data/<game>/<platform>/` itself, the
one zone the whole framework contract says is never modified by code. This
happened silently in a Wizardry 6 Amiga session: an `amiga-disasm` sub-agent
disassembling `Bane` left `Bane.cnf` sitting next to the original game files,
changing a verified "117 files" inventory to 118 with no error or warning —
only caught because a later step re-counted files by extension as a sanity
check, not because anything failed loudly.

Two habits prevent/catch this: (1) after any disassembly delegation, re-run
a file count/listing on the `data/` directory and compare against the
session's earlier known-good inventory — a diff of exactly the tool's output
files is the signature; (2) treat `docs/<game>/<platform>/disasm/` (not the
project's `docs/` root, and never `data/`) as the canonical home for
disassembly artifacts (`.asm`, `.cnf`), and relocate anything a sub-agent
left elsewhere once you notice it, updating any doc that references the old
path.

**Same failure mode, no sub-agent involved:** running IRA yourself with an
`-info`-only invocation and no explicit `TARGET` argument (e.g.
`ira -info data/<game>/<platform>/Foo`, just checking hunk sizes before the
real disassembly pass) still writes `Foo.asm` next to `SOURCE` by default —
confirmed on Embryo (Amiga): a first `-info` call with only `SOURCE` given
left `Embryo.asm` sitting in `data/explore/EmbryoHr/data/` even though the
*real* disassembly pass moments later correctly wrote to `docs/.../Embryo.asm`
because that one specified `TARGET` explicitly. Always pass an explicit
`TARGET` path (into `docs/<game>/<platform>/`) on *every* IRA invocation,
including throwaway `-info` checks — not just the final disassembly pass.
