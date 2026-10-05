# A "zero literal magic references" negative can be an artifact of searching a wider byte-width than the code actually compares

**When it bites:** an exhaustive byte-pattern search for a container/chunk
magic string (3-4 ASCII bytes) across a whole executable comes back with
zero hits, and you're about to conclude "this executable never checks that
magic at runtime" — especially when other independent evidence (a working
decompressor, a container clearly tagged with that magic on disk) says it
must.

## What went wrong

Reunion (Amiga OCS/ECS floppy, `methanoid`): Disks 1-5 carry blocks tagged
with 4-byte ASCII magics `"2AM1"`.."2AM5"`/`"1AM1"`.."1AM5"` (disk number
baked into the 4th byte). A full-binary search of `Main.exe` for any of
these exact 3-4 byte substrings returned **zero hits**, which read as
strong evidence the decompressor must live somewhere else entirely (a
runtime-loaded overlay never captured in the extracted executable) — a
plausible and worrying theory that shaped the next several probes.

It was a false negative. The dispatcher doesn't compare the magic as a
3-4 byte string at all — it loads the leading **16-bit word** of the
4-byte field and does `cmpi.w #$3141,d0` / `cmpi.w #$3241,d0` (`'1A'` /
`'2A'` as a big-endian word), branching to the matching decompressor
before ever looking at the remaining two bytes (the disk-number digit is
read separately, for a different purpose). A search anchored on the
*nominal* magic width (however many bytes look meaningful when you eyeball
the file's own header) was strictly wider than the code's real comparison,
so it could never match.

## Fix

When a magic-string search comes back with zero hits despite good reason
to expect a real runtime check, don't only widen the search (more disk
images, more file regions) — also **narrow** it: try every prefix length
of the magic (2-byte, 1-byte) in addition to the full nominal length.
Compilers and hand-written dispatchers routinely compare only as many
bytes as are needed to distinguish the cases actually present (a `cmpi.w`
is one instruction and reads two bytes; a full 4-byte compare needs two
instructions or a `cmpi.l`), so the code's real comparison width is often
shorter than the format's documented/eyeballed magic length. This is the
mirror image of `narrow-opcode-form-census-false-negative.md` (which is
about widening *addressing-mode/opcode-form* coverage to find a missed
hit) — here the fix is narrowing the *search pattern length* itself, not
the instruction forms scanned.
