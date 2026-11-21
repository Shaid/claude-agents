# WHDLoad slave sources contain patching info only — but that patching info is a free address-mapping oracle

**When it bites:** tempted to read a `.slave` source for hints about a game's data format; listing which disk files a game reads from the slave's strings; or stuck converting between a raw disk image's file offsets and the game's own runtime addresses with no other oracle available.

WHDLoad slave sources contain patching info only — version offsets,
protection removal, self-modifying-code fixes. No format information (record
layouts, compression schemes, table shapes) lives there. Don't mine them
looking for format clues.

They ARE, however, a free and verifiable **runtime-address <-> file-offset
mapping oracle**, worth checking before building one any other way. A slave's
hardcoded patch-target addresses are real absolute addresses inside the
original, unpacked game image, and its final `jmp $<addr>.w`-style entry
point tells you exactly where execution resumes after the loader hands off —
both are directly checkable against your own raw file dump. Confirmed on
Midwinter (Amiga, `hunter` project): the installed WHDLoad slave's boot stub
jumps to `load_address + 0x20`, and cross-referencing 5 of its patch-target
addresses against known strings/opcodes in the raw disk image derived
`runtime_address = file_offset - 0x331B6` (equivalently `file_offset =
runtime_address + 0x331B6`) with 5/5 addresses confirming the same constant
— turning "everything else static is blocked on having a runtime<->file-offset
mapping" into a one-session solve, no disassembly of the loader itself
required.

The slave is also the authoritative **list of disk files the game reads** —
but `strings` under-counts it. `resload_DiskLoad` (`jsr $28(A6)`) takes the
disk number in D2 and opens `Disk.<n>` with no file name in the slave; only
`resload_LoadFile`-style loads leave strings. Decode the `resload_*` calls
and their register setup instead. Armour-Geddon (hunter): strings named 3
files, the DiskLoad calls showed all 7 disks are read — the doc's open
question "how are Disk.1-4/7 loaded?" was an artefact of the string search.
