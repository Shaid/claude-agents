# The reference tool's bundled data may be a different revision than yours

**When it bites:** you found a fan/RE tool with source that reads the exact
game's files — perfect oracle — and you're about to trust its versioned
tables (bank pointers, palette addresses, file↔role mappings) against your
own flat data files without checking which *revision* of the game the tool
was built against.

A reference tool's source documents its *own* data: the disks/saves it
ships, the build it was written against. The files in your hands may be a
different release revision with identical formats but different *content
tables*. Same containers, same codec, same sprite layout — and yet the
pointer table has one extra entry, the bank numbering is shifted by one,
and the "sprite palette" the tool used isn't in your data at all.

Confirmed on Drakkhen (Amiga/ST, `drakkhen`): the Drakkhen Viewer v1.00
ships **v1.1 disks** whose files are renamed (`jdr.app`, `garde.tc1`,
`res.tc0`, `resid.ech`) and whose `res.tc0` bank table has 6 entries,
while the original-release `res.mc0` in the data dir has 7 (an extra bank;
the 68-sprite item bank sits at ptr[2] not ptr[1], and the "not gfx" bank
lands at ptr[4] not ptr[3]). The tool's sprite palette came from a v1.1
RAM dump; the palette embedded in the original `res.mc0` colours the
sprites **wrong** (0/3 reference colours present) — the original's own
palette location is a separate open question.

**Cheapest first move — read the tool's own input files, not just its
code.** The tool's code documents the format; its *shipped disks* pin down
the revision. Extract the same-named file from the tool's disk image (via
its own FAT parser) and diff the two revisions' structures. Here that
instantly showed the extra bank and the renamed files, and made the
original-release bank numbering decipherable.

**When your data and the tool's differ, the tool is still the oracle for
the format, only not for the versioned tables.** Decode-chain verification
still works: decode the tool's own file with your pipeline and diff
pixel/byte-exact against its rendered output (0/128 mask, 27/27 colour
pixels on Drakkhen's dagger), then apply the same decoder to your
revision's data with the corrected table semantics.

Related: `decoder-address-reuse-across-rom-release.md` (decoder constants
vs ROM releases), `same-name-cross-port-colour-mismatch.md` (cross-port
colour truth), `embedded-palette-not-the-installed-palette.md` (a parsed
embedded palette isn't the installed one — here the *reference tool's*
palette was installed and the embedded one was dead).

**Same trap, fork-shaped: two forks of one community tool can document
DIFFERENT format revisions.** Fire Emblem: Three Houses (Switch,
`chimera`): `imouto1994/fe3h-editor` (README: "v1.0.2") only describes the
older 152,588-byte save layout (`Character` stride `0x230`) and throws on
anything else, while its same-lineage sibling `Xzonn/Fe3hSaveEditor` gates
on the header's version word (`V1000` = 12/13 vs `V1001` = 23) and carries
the current 154,412-byte layout (stride `0x24C`, `MAX_CLASS 100`). A pass
that read only the first fork verified it byte-exact against the project's
two old-revision saves and then concluded the current revision was
"unlocated" — the second fork already had it. **Before trusting any
community tool's struct, read its version/size gate (`switch (SaveVersion)`,
`if (SizeOfFile != ...)`, a `V1000`/`V1001` enum) and check which revision
your files actually are; if the tool rejects your file's size or version,
look for a sibling fork that accepts it before deriving anything.**
