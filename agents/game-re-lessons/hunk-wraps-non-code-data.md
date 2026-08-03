# AmigaOS HUNK_HEADER/HUNK_CODE can wrap non-executable resource data

**When it bites:** a decrunched or loaded file starts with `000003F3`
(HUNK_HEADER) and a `000003E9` (HUNK_CODE) tag, and you're about to assume
the payload after it is CPU-executable 68k code just because of the wrapper.

Jungle Strike AGA's `objects1`-`9`, `sprites1`-`9`, and `mission1stat`-`9stat`
(27 files, clearly sprite/data resources by name and size) all decrunch to a
byte-exact single-hunk `LoadSeg()`-format module — the same wrapper the
game's real executable (`JStrike`) uses — wrapping a `HUNK_CODE` block whose
payload is plainly graphics/table bytes, not opcodes. This is a known Amiga
convention: reuse the OS's relocating loader as a generic container even for
opaque data, since it's a ready-made "load this blob into memory and hand me
a pointer" mechanism the game's boot code already needs for its real
overlays.

Don't take `000003F3`/`000003E9` at face value as "this file is code" — check
what follows the tag+size longword: valid 68k opcode density, or graphics/
table-shaped data (many small integers, an ascending offset directory, a
tile/pixel value range)? Treat the HUNK_HEADER as a *container signal*, not
a code/data classification by itself.

**Don't assume every `HUNK_HEADER`-wrapped file in a corpus is the same
single-hunk shape, even within one game.** Desert Strike (Amiga)'s
`hunk-wrapped` chunks superficially look like the same convention as above
but are real multi-hunk relocatable modules (2-6 hunks: CODE + DATA + BSS),
not one opaque `HUNK_CODE` block — a different game/build using the
generic wrapper for a genuinely different purpose. Also: some linkers
embed `MEMF_CHIP`/`MEMF_FAST` flags directly in the in-stream hunk-type
longword itself (e.g. a raw tag `0x800003e9` = flags(CHIP) + `HUNK_CODE`
`0x3e9`), not only in the header's per-hunk size table — a parser that
masks `&0x3FFFFFFF` on the header's size longwords but not on the
in-stream type tags will misread every hunk boundary as garbage.

**Decode whatever sits between the payload and `HUNK_END` — don't just skip
to the trailer.** Two prior passes on this same Jungle Strike group read
straight past the bytes between the `HUNK_CODE` payload and `HUNK_END`
looking only for a trailer marker (a literal `TEST` string), and never
noticed a real `HUNK_RELOC32` relocation block sitting there (tag
`0x000003EC`, repeating `{count:u32, hunkNumber:u32, offset:u32 * count}`
groups terminated by `count=0`). Decoding it turned out to be a cheap,
**code-free structural oracle** for "does this blob embed real pointers":
`objects1`-`9` each carry 258-762 relocated longwords; `sprites1`-`9` and
`mission1stat`-`9stat` carry zero, `HUNK_END` immediately after the
payload. That split alone settles "entity/pointer table vs. flat pixel/
audio data" before any disassembly, byte-frequency sweep, or geometry
guess — cheaper and more conclusive than every prior structural probe
combined (divisor sweeps, trailer-shape reads, cross-format header
matches). General rule: before concluding a `HUNK_CODE`-wrapped blob's
content type from byte-pattern or geometry sweeps, check what tag
immediately follows the payload — `HUNK_END` (`0x3F2`) directly, or a
relocation/symbol/debug block you haven't parsed yet.

**A relocation block also hands you a value-based way to re-anchor a
"doesn't generalize" table, instead of a fixed-field-index byte-pattern
match.** An earlier pass found a real, self-describing header+directory
structure in exactly one file of this group (`objects1`: N leading
unrelocated longwords, each a self-relative offset from the payload
start) but concluded it didn't generalize, because the *specific field
index* holding the directory's own self-pointer (value == header's own
byte size) differs per file — sometimes field 0, sometimes field 4 or 5.
The header *field count* itself is recoverable file-by-file with zero
guessing as `firstRelocatedOffset / 4` (the relocation block's own first
entry marks exactly where the unrelocated header ends and the relocated
directory begins), and the specific field that anchors the directory is
whichever one's *value* — not position — equals that header size. Testing
by value instead of position is what generalized cleanly to all 9 files
where the original byte-pattern match on one instance couldn't.
