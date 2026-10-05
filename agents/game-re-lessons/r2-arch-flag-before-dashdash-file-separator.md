# radare2's `-a <arch>` flag must come before `-c`, and never combine with a `-- file` separator, or the file silently fails to open

**When it bites:** invoking radare2 non-interactively with a command line
shaped like `r2 -a <arch> -q -c '<cmds>' -- <file>` (`--` used as an
argument separator, the way most Unix CLIs treat it), and getting a
disassembly/hexdump that's uniformly `0xFF` (or otherwise flat/empty) —
easy to mistake for "this ROM really is blank/erased/corrupt" rather than
a CLI invocation bug. This is **not limited to unfamiliar architectures**
(an arcade protection MCU, a new console CPU) or to plausibly-blank
targets: it has now bitten a dense, fully-populated Z80 program ROM page
too, where an all-`0xFF` read is never a plausible real result, which
should be an even faster tell than the "maybe it's really just erased"
case below.

**Confirmed a third time on a mainstream, well-supported architecture**
(68000, `methanoid`/Deuteros, Amiga): `r2 -a m68k -q -c 'pd 30 @ 0x7b860'
-- data/deuteros/amiga/Disk.1` returned uniform `0xFF`/`invalid` at one
address while a *different* address had disassembled correctly moments
earlier in what looked like the same session (in this case the file
genuinely re-opened cleanly between the two calls, so this was purely the
`-a`/`--` ordering bug, not a stale/clobbered session — see
`shared-tool-session-clobbered-by-fork.md` for that separate failure
mode). This rules out "only exotic/under-supported archs are affected" —
the bug is pure CLI-argument-parsing order, independent of how well the
target architecture is supported.

Confirmed twice in the same project (`kolbold`): (1) Black Tiger's Intel
8751 (MCS-51) protection MCU dump (`r2 -a 8051 -q -c 'px 16 @ 0x100' --
bd.6k`) — every read returned `0xFF` at every offset, `i`/`o` reported "No
file selected", and disassembly showed nothing but the `0xFF` opcode
(`mov r7,a`) forever, exactly what "the whole ROM is unprogrammed" would
also look like; (2) a later session, same project, disassembling one of
Black Tiger's 16 banked Z80 program-ROM pages (`r2 -a z80 -m 0x8000 -q -c
's 0x8000; pD 0x4000' -- bank6.bin`) — again uniformly `0xFF`, but this
time on a page independently known (via a plain hexdump) to be dense with
real code, so the symptom was unambiguous rather than merely plausible.
Both times the file had NOT actually opened at all; the `--` separator
combined with `-a` positioned before `-c` in that exact order caused
radare2 to silently drop the file argument in this build, with no error
printed even without `-q`'s output suppressed for the open step.
Reordering to `r2 -q -a <arch> -c '<cmds>' <file>` (drop the `--`, put
`-a` immediately after `-q`) opened the file correctly both times and
immediately showed real, structured, non-`0xFF` bytes at the exact same
offset. (Case 2 also needed `-m 0x8000` — a *separate*, additional
requirement to map a banked/windowed file at its real target address
rather than offset 0 — layered on top of the same dashdash fix.)

**Fix:** when a fresh radare2 invocation on a new/uncommon architecture
returns suspiciously uniform or empty data, first sanity-check the file
actually opened (`r2 -q -a <arch> -c 'i' <file>` should print a nonzero
`size` and `fd` line — "No file selected" or a missing `size` line means
the open failed, not that the data is empty) before concluding anything
about the ROM's content. Prefer `r2 -q -a <arch> -c '<cmds>' <file>` (no
`--` separator) as the default invocation shape. Separately: a real,
non-`BAD_DUMP`/`NO_DUMP`-flagged ROM that genuinely is almost entirely
`0xFF` is itself plausible and not evidence of a bad dump for a
sufficiently trivial embedded program (a few dozen real bytes in an
otherwise-erased few-KB EPROM) — cross-check the file's CRC32 against the
emulator's own `ROM_START`/`ROM_LOAD` declaration before doubting the
dump either way.
