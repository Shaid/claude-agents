# A sub-resource/chunk tag spelling a familiar format name is not proof the payload is that format

**When it bites:** you're walking an already-cracked container's own
offset/entry table and hit a sub-resource whose 4-byte (or similar) tag
reads as ASCII for a well-known standard or in-house format (`"XML\0"`,
`"BMP\0"`, `"JSON"`, ...) — before documenting or parsing that entry as the
format its tag name suggests, especially when a *separately, correctly*
named tag for the real thing (e.g. a binary-compiled variant) sits right
next to it in the same table.

Confirmed on NieR:Automata (PC)'s in-house `DAT\0` resource-bundle
container (`flower` project, `docs/nierautomata/pc/data-structure.md` §5.2):
walking a real bundle's offset table turned up an entry tagged `"XML\0"`.
The natural read is "this is literal XML text." Dumping the 900 bytes
immediately following the tag showed dense binary data — zero `<`/`>`/
tag-name ASCII anywhere — while a *different*, separately-tagged `"BXM\0"`
entry in the very same bundle's table (plausibly "Binary XML") behaved
exactly as its name suggests. The `"XML\0"` tag turned out to be a distinct,
still-undecoded binary sub-format that merely shares a readable name with
the well-known text format, not an alias or compressed form of it.

**The fix:** treat a chunk/section tag's readable name as a hypothesis, not
identification. Before writing the format into a spec doc as more than a
guess, dump real bytes immediately past the tag and check for the format's
actual expected shape (readable angle brackets and attribute syntax for
XML, a recognizable sub-header for a binary format, etc.) — the same
one-line check `familiar-extension-not-proof-of-standard-format.md`
recommends for file *extensions*, just applied to an embedded chunk/section
*magic tag* inside a container you've already cracked, rather than to a
whole file. The two lessons share a root cause (a human-readable name
substituting for verification) but differ in scope: the extension case is
about the file as a whole and is usually resolved by finding the *real*
magic once you look; this case is about a container-internal tag that *is*
the real, in-use magic for some genuine (if still-undecoded) sub-format —
the mistake is assuming that sub-format is the well-known one its name
resembles, not that the tag is fake or misapplied.
