# A whole-multi-hunk-file forced-CODE IRA pass's address comments desync past the declared `.cnf` range

**When it bites:** a `.cnf` forces a single, large `CODE $0 - $N` range over
an IRA disassembly (the standard fix for the "large hand-optimized binary,
`-preproc` badly under-covers it" failure mode), but the file actually fed
to IRA is the **whole multi-hunk executable** (not just that one hunk's
extracted CODE payload) and `N` equals only the first hunk's size — i.e. the
`.asm` output runs to many more lines than `N` bytes would explain. Before
citing any address past that boundary as a real file offset (or converting
it with the same `ORG + header_size` formula that works fine for addresses
inside the declared range), verify it independently.

Confirmed on Midwinter 2 (Amiga, `hunter` project): `mwII.cnf` declared
`CODE $00000000 - $000353B8` (exactly hunk0's real CODE size, 217,912
bytes), fed the *entire* 505,488-byte `mwII` executable (all 4 hunks). A
25-point spot-check pairing each `.asm` line's own printed opcode-byte
comment against the real file confirmed `real_file_offset = ORG_address +
0x2C` (the hunk0 header size) held for **every** sample inside the declared
range (13/13 unambiguous long-needle matches, ORG `$0`-`$34AE8`) — but a
label the project's own doc cited at ORG `$443AC` (well past `$353B8`,
already inside hunk1/DATA territory) was **completely wrong**: a direct
string search for the real content ("Africa\0Agora\0Lobos\0...") found it
at raw file offset `0x53030`, not `0x443ac+0x2c=0x443d8` — a ~60 KB
discrepancy, not a small header-constant miss. IRA continues disassembling
past the declared `CODE` range's end (rather than stopping or refusing),
and once it starts decoding hunk1's own header fields and DATA bytes as if
they were more hunk0 CODE, its own running address counter stops
corresponding 1:1 to real file bytes — plausibly because structural fields
it still recognizes (hunk tags, size longwords) don't count instruction
bytes the same way plain opcode decoding does.

**Fix:** treat a forced-whole-range `.cnf`'s address-to-file-offset formula
as validated **only inside the declared `CODE` range**. For anything the
`.asm` places past that boundary, don't trust the comment address at all —
locate the real content by direct byte/string search against the raw file
instead (fast, and self-verifying). If the region past the boundary matters
for real work, the fix is a proper `.cnf` per hunk (separate `CODE`/`DATA`
ranges honoring the real hunk table), not extending trust in the single
forced range. A cheap way to catch this before it produces a wrong citation
in the first place: spot-check a handful of addresses spanning the *whole*
`.asm` (not just near the start) against the raw file's real bytes,
specifically including points past wherever the `.cnf`'s declared range
ends.
