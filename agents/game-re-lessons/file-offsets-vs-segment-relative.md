# File offsets vs segment-relative offsets

**When it bites:** double-checking a data offset cited from disassembly, especially in executable formats (Amiga hunk, MZ, ...) that put headers before loaded segments; also when reusing an address a jump table resolved for you; also before trusting a literal-address search (xref scan, pointer-table search) against the output of an emulator-harness decompressor (Method §5's musashi-harness pattern).

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
