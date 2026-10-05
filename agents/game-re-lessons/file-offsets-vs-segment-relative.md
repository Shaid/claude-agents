# File offsets vs segment-relative offsets

**When it bites:** you're citing or reusing an address from disassembly, a jump table, or IRA's `.asm` address column as a file offset, or using one as a search key. Also: a literal-address xref search against an emulator-harness decompressed dump comes back "zero hits, must be indirect". Also: MIPS `j`/`jal` targets computed by a scanner that used file offsets as PC.

Every tool and derivation path has its own address space: true file offset, hunk/segment-relative, pre-relocation runtime, the harness's relocated load base, IRA's synthetic concatenated address, or ELF vaddr. Each one is correct for how it was derived. Mixing them under one undifferentiated label (`CODE+N`) silently shifts citations by a header size. A search key from the wrong space returns a clean "0 hits" with no error, which then gets written up as a real negative.

**Check / fix:**
- Label the offset kind on every citation, per citation, not as a blanket rule for the whole doc. Sanity-check that reads land on plausible data (e.g. 12-bit palette words ≤ `0x0FFF`).
- **Amiga hunks:** a jump-table target read from DATA (A4 = DATA+`0x7FFE`) is a pre-relocation address. For hunk 0 that equals the CODE-relative offset. The file offset needs the hunk payload's file start added (e.g. `+0x28`).
- **Harness dumps:** if the musashi-style harness runs relocation to completion, stored pointers are `BASE + header + offset`. Read `BASE` from the harness source (`emu.c`) and search in that space.
- **IRA:** with multiple CODE/DATA ranges or hunks, the `;NNNNNN` column is a synthetic concatenated-payload address. Derive a per-hunk delta by raw-searching one known byte pattern and diffing its file offset against IRA's address. Confirm the delta on a second, unrelated instruction. Offsets from raw reloc arithmetic (`hunk_file_start + operand`) need no correction.
- **MIPS/fixed-width ISAs:** `j`/`jal` targets are `((PC+4)&0xF0000000)|(idx<<2)`, which lives in vaddr space. Convert file offset to vaddr (via the `PT_LOAD` `p_vaddr − p_offset` delta) before using a target or a function address as a search key. Relative branches don't need this. Re-check each negative verdict individually after fixing, because the bug causes false negatives, not a uniform shift.

**Canonical example:** Black Crypt (Amiga, `crawl`), `bcdft_decompressed.bin` (166,676 B). A linear disassembly and an independent per-2-byte capstone rescan both found **zero** references to four known renderer functions, and the write-up concluded the calls must be indirect. The harness had run relocation at `BASE = 0x80000`, so pointers needed `+0x80058`. Re-searching found 267 direct call sites, and there was no indirect dispatch.

**Variants:**
- Hunk header double-counted: a `CODE+0x2C6` note counted a 36-byte header twice and pointed 18 words past a palette into opcodes. The phantom "second palette" stayed in the docs for weeks.
- Wizardry 6 (Amiga, `sorcery`): an unadjusted jump-table column (`CODE+0x35e6`) sat beside a file-offset string table in the same doc.
- Reunion (Amiga, `methanoid`): the IRA deltas were `+0x58` (game.exe CODE), `+0x8900` (game.exe DATA), and `+0x50` (intro.exe CODE), none derivable from the `.cnf`.
- Valkyrie Profile: Lenneth (PSP, `valkyrie`): a search for callers of two `BOOT.BIN` functions using file-offset keys gave "0 callers, orphaned". With `vaddr = off − 0x60` it found a live `jal` loading `"disc0:/PSP_GAME/USRDIR/moviepac.dat"`, while the other function's "0" held.

**History:** 5 recorded manifestations (`crawl`, `sorcery`, `methanoid`, `valkyrie`). Full log in `_archive/file-offsets-vs-segment-relative.md`.
