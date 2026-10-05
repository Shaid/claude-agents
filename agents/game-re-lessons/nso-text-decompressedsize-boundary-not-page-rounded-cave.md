# An NSO segment's page-rounded, mapped-and-executable padding is not the same memory the loader actually copies patch content into

**When it bites:** placing an exefs/IPS32 code-cave patch's new instruction
bytes in the gap between an NSO segment's declared `DecompressedSize` (e.g.
`.text`'s) and the next segment's page-aligned `MemoryOffset` (e.g.
`.rodata`'s) — confirmed empty (all-zero), confirmed page-mapped with the
right permission (R-X for a `.text` gap), and confirmed applied by the
mod-loader's own log line with no warning — yet the game crashes with an
"undefined instruction (opcode 0x00000000)" fault landing exactly at the
cave's own address, as if the patch bytes were never written at all.

Confirmed on Fire Emblem: Three Houses (Switch, `chimera`, Ryujinx/Ryubing
1.3.3): a bounds-check patch placed 60 bytes of new AArch64 code at
`0xafe320`–`0xafe35c`, in the 3,296-byte gap between `.text`'s NSO-header
`DecompressedSize` (`0xafe320`) and `.rodata`'s page-aligned `MemoryOffset`
(`0xaff000`). Two other records in the same IPS32 file — branch redirects
well inside `0xafe320` — worked exactly as intended (confirmed executing,
by the crash itself reaching the cave). The cave content did not: a live
test crashed instantly with `UndefinedInstructionException` at the cave's
exact address, and the Ryujinx log showed the patch WAS applied ("Patching
address offset afe320 <= ... len=60", no warning) with zero complaint from
`MemPatch.Patch()`.

**Root cause, confirmed from Ryubing's actual source**
(`src/Ryujinx.HLE/Loaders/Executables/NsoExecutable.cs` and
`src/Ryujinx.HLE/Loaders/Processes/ProcessLoaderHelper.cs`, cloned from
`https://git.ryujinx.app/projects/Ryubing.git`): there are **two separate
buffers with two separate, non-matching bounds**, and the patcher writes to
one while the CPU reads from the other.

1. `NsoExecutable.Program` is a **flat, unpadded byte array**, exactly
   `DataOffset + DataSize` bytes — `.text` + `.rodata` + `.data` back to
   back, with `Text`/`Ro`/`Data` each just a `Span` slice of it at their
   exact declared offset/size, **no page rounding at all**. This is the
   array `MemPatch.Patch(programs[i].Program, protectedOffset)` writes into,
   and its own bounds check (`patchOffset > memory.Length`) is against this
   array's real length — tens of megabytes for a real game binary — so an
   offset like `0xafe320` (deep inside a ~28 MB array) is nowhere near out
   of bounds. The write always "succeeds" and logs success.
2. `ProcessLoaderHelper.LoadIntoMemory()` copies each segment into actual
   guest CPU memory with `process.CpuMemory.Write(textStart, image.Text)` —
   and `image.Text` is `Program.AsSpan(TextOffset, TextSize)`, a span
   **truncated to exactly the declared `TextSize`**, not the page-rounded
   size. Only the permission grant (`SetProcessMemoryPermission`) rounds up
   to the next page; the byte *content* copy does not. Bytes at index
   `>= TextSize` inside `Program` are real array elements MemPatch can
   happily overwrite, but `LoadIntoMemory` never transfers them anywhere the
   CPU can see — the guest page there keeps whatever the fresh backing
   allocation defaulted to (zero), regardless of `Program`'s contents.

So the "cave" is real, mapped, executable memory that is **structurally
unreachable by any patch**, permanently, no matter how the IPS file is
rebuilt — the loader's per-segment copy, not the patcher, draws the real
line, and it draws it at the segment's own declared size, not the page
boundary. This is different from (and stacks with) the simpler premise-trap
of assuming "page-rounded and marked executable" implies "the loader will
put my bytes there" — it's specifically the split between a *host-side flat
patch-target buffer* (unbounded past the segment) and a *guest-memory
content pipeline* (bounded exactly at the segment) that makes the mistake
undetectable by inspecting either side alone.

**The fix:** any code-cave address used in an exefs/IPS32 NSO patch must
satisfy `address < Segments[N].DecompressedSize` for whichever segment it
nominally belongs to (re-derive this directly from the raw NSO0 header —
3×`{FileOffset:u32, MemoryOffset:u32, DecompressedSize:u32}` at file offsets
`0x10`/`0x20`/`0x30` — don't trust a stale prior derivation). Add this as an
explicit, automated self-check in the patch build script (`assert
recordEnd <= segmentDecompressedSize` for every record) — it would have
caught this bug before the patch was ever built, and costs nothing to keep
running on every future patch for the same binary. If no such space exists
below the boundary (verify by an actual byte scan, not assumption — a
heavily optimized release binary may have essentially zero linker/alignment
slack: one real case found only 15 NOP runs, max 12 bytes, across 11.5 MB of
`.text`), look for genuinely dead-but-copied bytes instead: a NOP run
immediately preceded by an unconditional return/branch (so fall-through can
never reach it) with a whole-corpus direct/relative branch-family census
(B/BL/B.cond/CBZ/CBNZ/TBZ/TBNZ) confirming nothing targets it. Multiple
small dead-after-`ret` gaps can be chained with unconditional branches to
assemble enough space for a check too large for any single gap — a
single-unsigned-compare range check (`cmp`+`csel`, catching both
out-of-range-low and out-of-range-high in one comparison since a negative
value reinterpreted as unsigned wraps huge) needs far fewer instructions
than two signed comparisons and two conditional branches, which can be the
difference between fitting and not fitting in the real space available.

This generalizes to any Nintendo Switch NSO exefs-patch target on Ryujinx/
Ryubing (and plausibly Atmosphere's own IPS32 patcher, which uses the same
segment-copy convention this project's `NSO_HEADER_ADJUST = 0x100` offset
convention was already sourced from) — not just this one game.
