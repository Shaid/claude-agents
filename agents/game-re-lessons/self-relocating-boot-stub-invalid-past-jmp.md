# Self-relocating boot/loader stub: linear disasm past its JMP looks invalid, not because it's wrong

**When it bites:** a small (bootstrap-sized, tens-to-low-hundreds of bytes)
piece of code contains an explicit byte-copy loop (`move.b (aX)+,(aY)+` /
`dbra`) writing to a fixed absolute destination address computed from
literal immediates, followed by a `jmp`/`jsr` to an absolute address that
falls *inside* that destination range — and a plain linear disassembly
(radare2/IRA) of the bytes immediately following that jump renders as
garbage/`invalid` opcodes even though the jump target address is nominally
valid and in-range.

This is a **self-relocating stub**, not a bug in the disassembly or a sign
the jump target is wrong. The stub copies a second code blob — stored later
in the *same file*, right after the copy-loop code itself — to a fixed
absolute memory address at runtime, then transfers control into the
*relocated* copy. The original file bytes right after the `jmp` are not
"the next instructions" at all; they're the **source** of the copy, still
sitting at their original file position, which a naive continued sweep
mis-reads as more code. This is distinct from (though related in spirit to)
the already-documented HUNK-relocation and overlay-linking traps — this one
needs no `HUNK_RELOC32` table or executable container at all, since it's a
small, headerless, hand-written copy loop, most often seen in Amiga
boot-block bootstraps (1024-byte payload, no room for a real loader, so the
first stage's whole job is "copy stage two somewhere bigger and jump to it").

**Confirmed on Millennium 2.2 (Amiga)'s `Disk.1` boot block**:
`movea.l #$66032,a3` / `move.l #$66400,d1` / `subi.l #$66032,d1` (computing a
974-byte length) / a `move.b (a5)+,(a3)+` + `dbra` loop copying
`file[0x32, 0x400)` to absolute `$66032`–`$66400`, then `jmp $662EC.L`.
`$662EC` is inside the just-relocated range. Disassembling straight through
from the file's own byte 0x42 onward (i.e., ignoring the relocation) renders
mostly `ori.b`/`invalid` garbage; the *same bytes*, extracted standalone and
disassembled from their own start (or seeked at `jmp_target − dest_base`
within the extracted blob), decode as a long, coherent, semantically sound
routine (device I/O init, LVO calls, structured reads).

**Fix:** when a small binary's copy-loop immediates give you
`(sourceStart, destBase, length)`, extract `file[sourceStart, sourceStart +
length)` as a standalone blob and disassemble *that* from its own offset 0 —
don't keep sweeping the original file past the jump. To resolve any absolute
address `A` inside the relocated range from there: blob-relative offset =
`A − destBase`; and conversely, original file offset for any blob-relative
position `p` is `sourceStart + p`. Every absolute call/jump target the
relocated code itself references (further LVO calls, other fixed
"$6xxxx"-style addresses it sets up as a small resident service API) uses
the same `file_offset = mem_addr − (destBase − sourceStart)` formula, valid
only within that relocated blob's own memory range.
