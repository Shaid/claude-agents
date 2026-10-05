# File offsets vs segment-relative offsets

**When it bites:** double-checking a data offset cited from disassembly, especially in executable formats (Amiga hunk, MZ, ...) that put headers before loaded segments; also when reusing an address a jump table resolved for you; also before trusting a literal-address search (xref scan, pointer-table search) against the output of an emulator-harness decompressor (Method §5's musashi-harness pattern); also when citing IRA's own `.asm` listing address column directly as a file offset — especially on a target whose `.cnf` declares more than one CODE/DATA range across more than one hunk, or a hunk whose real file-data start isn't 0 — or when a delegated/prior session's IRA-derived offset citation looks subtly inconsistent with an offset independently derived by raw reloc/byte arithmetic in the same doc.

Executable formats put headers before loaded segments. A stale `CODE+0x2C6`
note double-counted a 36-byte hunk header, pointing 18 words past a palette
into opcodes — a phantom "second palette" survived in the docs for weeks.
State which offset kind you mean; verify palette reads land on plausible
colour words (≤ 0x0FFF for 12-bit).

A second, easy-to-miss manifestation: an Amiga small-data jump-table target
(the `A4 = DATA_start + 0x7FFE` technique — read a `JMP.L` absolute target
straight out of the DATA hunk) yields a **pre-relocation runtime address**,
which for the first hunk (loaded at runtime address 0) is numerically
identical to that function's **CODE-hunk-relative offset** — not the true
file offset, which needs `+ (CODE hunk payload's file offset, e.g. 0x28)`
on top. A from-scratch string search or manual disassembly of an extracted
CODE-hunk binary, by contrast, naturally yields true file offsets once you
add that same header size back in. Both conventions are individually
correct for how they were derived, but citing them side-by-side under one
undifferentiated `CODE+N` label — which is exactly what happened when a
doc's own jump-table table (unadjusted, e.g. `CODE+0x35e6`) sat next to a
separately-derived filename-string-offset table (adjusted, true file
offset) in the same document — silently produces two address spaces
differing by the header size throughout the same write-up. Before reusing
*any* address a jump-table resolution handed you, check which of the two
bases the surrounding document already established for it, and say so
explicitly per-citation rather than asserting one blanket rule for the
whole document (Wizardry 6 Amiga, `sorcery`).

A third manifestation, distinct from both above: when an **emulator-harness
decompressor** (Method §5 — running the game's own routine under musashi or
similar to defeat a hostile codec) also runs the game's own **relocation-fixup
pass** to completion before dumping its output buffer, every stored code
pointer in that output is `harness_load_base + original_offset`, an address
space defined by the harness's own arbitrary load address (its `BASE`
constant), not the file offset, and not any hunk-relative offset either. Two
exhaustive xref searches on Black Crypt Amiga's `bcdft_decompressed.bin`
(166,676 B) — a linear disassembly, then an independent per-2-byte-offset
capstone re-scan — both found **zero** direct or literal-address references
to four known renderer functions across the whole decompressed image plus
its data segment, and concluded the call must go through an indirect/
computed dispatch table. A `re-codebreaker` premise audit found the real
cause in minutes: the harness's `emu.c` runs relocation to completion at
`BASE = 0x80000`, so every stored pointer needed `+0x80058` added first (the
harness's base plus its own small fixed header). Re-running the identical
search at the corrected address found 267 direct call sites immediately —
there was no indirect dispatch to find. **Fix:** before any literal-address
search against a harness-decompressed artifact, check the harness source for
whether it runs a relocation pass to completion, and if so, derive its load
base from the harness's own code (a `BASE`/similar constant) and search in
that address space, not the raw offset — a "zero hits, must be indirect"
conclusion from an unrelocated-address search is itself a common false
negative, not evidence of anything.

A fourth manifestation, distinct from all three above and specific to the
**IRA** disassembler: when a `.cnf`/`-config` run declares more than one
CODE/DATA range spanning more than one hunk (or a hunk whose real file data
doesn't start at file offset 0), the `;NNNNNN` address column IRA prints in
the `.asm` listing is a **synthetic "IRA virtual address,"** not the file
offset — IRA numbers addresses by concatenating each declared hunk's own
data *payload* back-to-back starting at 0, independent of where those bytes
actually sit in the file. Every `LAB_xxxx (0xADDR)`-style citation
transcribed straight from that column therefore needs a **per-hunk constant
delta** applied: `real_file_offset = ira_address + delta`, where `delta` is
constant within one hunk but different for every other hunk (and every
other executable). Confirmed on Reunion (Amiga, `methanoid`) across two
executables sharing one engine: `game.exe`'s CODE hunk1 delta was `+0x58`,
its DATA hunk2 delta was `+0x8900`, and a *different* executable
(`intro.exe`) built from the same toolchain had its own CODE hunk1 delta of
`+0x50` — three different constants on two files, none of them derivable
from the `.cnf` values alone. This does **not** mean IRA's disassembly is
wrong or untrustworthy — only its printed address column needs translating;
an offset independently derived via raw reloc-hunk-relative arithmetic
(`hunk_file_start + reloc_patched_operand`) is unaffected and needs no
correction, since that computation is inherently file-relative to begin
with. **Fix, and a general verification technique in its own right:** find
one already-identified byte pattern (a known immediate operand, a
recognizable instruction sequence) via a raw file byte search, then diff
its real file offset against IRA's address-column value for the same
instruction — the difference is the hunk's delta, and it's cheap to
re-confirm on a second, unrelated instruction in the same hunk before
trusting it (two independent hits landing on the identical delta is strong
enough to stop there; a mismatch means more than one hunk/range is in play
and each needs its own delta derived the same way).

A fifth manifestation, on a non-Amiga, non-hunk platform: **MIPS `j`/`jal`
absolute jump targets computed from a file-offset-indexed pseudo-PC.** The
`j`/`jal` encoding's target formula is `((PC+4) & 0xF0000000) |
(instr_index << 2)` — purely a function of "PC," so if a hand-rolled
disassembler or scanner is fed raw file bytes and uses each instruction's
*file offset* as "PC" (rather than converting to the real vaddr first via
the ELF's own `PT_LOAD` `p_vaddr`/`p_offset` delta), it computes a "target"
number that is a plausible-looking file offset — not the real vaddr the
CPU would actually jump to. For a small binary (upper 4 bits of every real
address are 0 either way) this number "works" when reinterpreted directly
as a file position to read bytes from, so eyeballing the disassembly at
that position looks totally normal — but it is silently the **wrong
32-bit value** when used as a search key against vaddr-space data: a
direct `j`/`jal`-target scan for "who calls function X" (where X's own
address was derived the same file-offset-as-PC way) or a `lui`+`addiu`/
`ori` materialization scan both return a clean "0 hits" with no error,
because the real callers encode the real vaddr, not the file offset.
Confirmed on Valkyrie Profile: Lenneth (PSP, `valkyrie`): an initial
caller search for two `BOOT.BIN` table-consumer functions (both addresses
obtained by scanning raw file bytes, so both were file offsets, not
vaddrs) came back "0 static callers for either" and got written up as a
negative — "this whole 4-function cluster appears genuinely orphaned."
Re-running the identical search after converting each address with the
project's own already-established `vaddr = fileOffset - 0x60` (`PT_LOAD`)
delta immediately found a real, live `jal` caller for one of the two
functions, whose own argument setup materialized the literal string
`"disc0:/PSP_GAME/USRDIR/moviepac.dat"` — decisive proof the first pass's
negative was a search-key bug, not a real absence (the *other* function's
"0 callers" verdict held up even after the fix — the bug produces false
negatives, not a uniform offset error that cancels out, so each verdict
needs independently re-checking, not just re-labeling). **Fix:** before
using a MIPS (or any fixed-width-ISA) computed jump/branch target as a
search key against anything else in vaddr space — not just before citing
it in a document — convert through the binary's real vaddr delta first;
relative branches (`beq`/`bne`-family) don't need this (both ends shift by
the same constant), but absolute `j`/`jal` targets are computed purely in
vaddr space and this conversion is not optional for them.
