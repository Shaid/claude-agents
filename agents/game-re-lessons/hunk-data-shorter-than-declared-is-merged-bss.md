# A `HUNK_DATA` block smaller than its `HUNK_HEADER`-declared size is a merged data+bss hunk, not a parse error

**When it bites:** you're hunting for the file location of a table/variable
whose `LEA`/`JSR`-absolute-long reference resolves (via `HUNK_RELOC32`) to
a target hunk, but the resolved offset never lands on plausible content no
matter what base you add — especially if that hunk's `HUNK_HEADER`-declared
size doesn't match the size longword embedded in its own `HUNK_DATA` block.

AmigaOS `HUNK_HEADER` declares each hunk's *allocation* size (how much
memory the loader reserves); the hunk's own body (`HUNK_DATA`'s marker+size
longwords) declares only how many bytes are actually *stored in the file*
for it. For a plain `HUNK_CODE` or `HUNK_BSS` hunk these normally agree (or
`HUNK_BSS` has no stored bytes at all, by definition). But SAS/C's linker
routinely emits a **merged `data+bss` hunk**: the `HUNK_DATA` block stores
only the initialized prefix, and the difference between the header's
declared size and the block's stored size is the zero-filled BSS tail —
present in memory at load time, **with zero corresponding bytes in the
file**. Any reference that reloc-resolves to an offset at or past the
`HUNK_DATA` block's own *stored* length (not the header's *declared*
length) is targeting a runtime variable, not stored table content. There is
no file offset to resolve it to; searching harder for one is chasing
something that structurally cannot exist — the specific failure shape
`negative-from-addressing-root-not-shapes.md` already names for consumer
searches applies just as directly here to *content* searches.

Confirmed on Phantasie III (Amiga, `nicodemus` project): `PhantasieIII`'s
hunk 1 declares `0x1AC3` longwords (27,404 B) in the header but its
`HUNK_DATA` block's own size field says `0x9DF` longwords (10,108 B) —
a `re-codebreaker` escalation root-caused this as the answer to "what's
the right file-offset base for these `LEA`-referenced tables," not a
distraction from it, after two independent local attempts (a literal
`+dataHunkFileBase` guess, and a brute-force monotonic-value scan) both
failed by chasing bytes that don't exist in the file at all. Four
independent checks confirmed the `0x277C`-byte boundary (the stored
block's real length) as the true data/BSS split, with zero deviations:
a physical-impossibility check (the header's declared size would run the
hunk past EOF); a sharp reference-count split (all 4,676 code→hunk-1
relocation operand values partition cleanly at exactly that boundary, none
straddling); no initialized hunk-internal pointer aiming past it; and the
textbook SAS/C `LEA $7FFE.L,A4` / `RTS` `__LinkerDB`/A4-base-setup
signature landing on the one reloc entry whose value exceeded even the
*declared allocation* size.

**Fix:** before hunting for any hunk-relative base to resolve a reloc'd
reference, check the target hunk's own **stored** payload length (parse
`HUNK_DATA`'s own size longword, not the `HUNK_HEADER`'s per-hunk size
table) and compare it against the raw operand. If the operand is `>=` the
stored length, stop searching the file for content — it's a BSS variable —
and instead trace *what writes to it at runtime* (setup/init loops in the
code). A save file that round-trips the runtime BSS region (a
`gamesave.dat`-style raw dump) is a strong, cheap byte-exact oracle for
these addresses once you know that's what they are, with no live-emulator
access needed — confirmed here via an exact file-size match (11,812 bytes
= four block lengths summing exactly) and printable character names
decoding cleanly at the claimed struct stride.
