# File offsets vs segment-relative offsets

**When it bites:** double-checking a data offset cited from disassembly, especially in executable formats (Amiga hunk, MZ, ...) that put headers before loaded segments.

Executable formats put headers before loaded segments. A stale `CODE+0x2C6`
note double-counted a 36-byte hunk header, pointing 18 words past a palette
into opcodes — a phantom "second palette" survived in the docs for weeks.
State which offset kind you mean; verify palette reads land on plausible
colour words (≤ 0x0FFF for 12-bit).
