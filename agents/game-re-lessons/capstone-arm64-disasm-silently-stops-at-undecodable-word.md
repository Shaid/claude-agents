# Capstone's `Cs.disasm()` silently stops at the first undecodable word — a whole-segment call-target census returns false negatives, not an error

**When it bites:** writing a from-scratch Capstone-based AArch64 (or any
fixed-width ISA) disassembly helper and calling `md.disasm(bytes, addr)`
over a large span (a whole `.text` segment, megabytes) to census something
like "every BL targeting address X" or "every MOVZ loading immediate Y". A
small, targeted range around a known-good hit finds it; the same search
over the full segment returns zero hits, with no exception and no warning.

Confirmed on Fire Emblem: Three Houses (Switch, `chimera`): a "find every
BL instruction targeting `0x4cd1c0`" scan over the full 11,526,944-byte
`.text` segment returned 0 hits, while the identical scan restricted to a
16 KB window around the already-known call site found it immediately.
Progressively narrowing the failing range showed the cutoff was sharp: a
64 KB window containing the real hit failed, an 4 KB window containing the
same hit succeeded.

**Root cause.** By default, Capstone's disassembly iterator **stops
entirely** the first time it encounters bytes it cannot decode as a valid
instruction for the selected mode — it does not skip forward and resume.
A large real-world code segment routinely contains non-instruction data
inline (literal pools for large ADRP+LDR-loaded constants, jump tables,
alignment padding) even on a fixed-4-byte-width ISA like AArch64, where
every one of those data words still occupies a valid 4-byte slot but does
not decode as a real opcode. The very first such word anywhere between the
start of the scanned range and the real target silently truncates the
whole iteration — everything after it, including the instruction you were
looking for, is never visited, and `disasm()` raises no error to signal
this.

**The fix:** set `md.skipdata = True` on the `Cs` instance before
disassembling any range wider than a single already-known-clean function
body. This makes Capstone skip one architecture-minimum-width unit (4
bytes for AArch64) past anything it can't decode and keep going, so a
data island no longer terminates the scan — it just contributes one
harmless `.byte`-style pseudo-entry and iteration continues correctly past
it, with instruction `.address` values still tracking real file offsets.

Treat any full-segment (not single-function) Capstone census that comes
back with suspiciously few or zero hits as suspect until re-run with
`skipdata = True` — a negative from this bug looks identical to a genuine
"no such caller exists" result, and can lead to a false "single caller"
or "dead code, unreachable" claim if the real caller happened to sit past
an inline data island the un-skipped scan never reached. This generalizes
to any fixed-width ISA disassembled with Capstone (ARM, ARM64, MIPS,
PowerPC) — not just this one project's AArch64 target.
