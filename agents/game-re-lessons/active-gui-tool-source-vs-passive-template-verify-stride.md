# A community GUI data-editor's source can name a section a passive binary template missed — but verify its per-record stride against the container's own header before trusting its field list

**When it bites:** a passive community binary-template repo (010 Editor
`.bt` files, an 010-template-derived doc) leaves part of an already-solved
container's byte range undecoded ("N undecoded bytes, template-documented
but not independently verified" or simply absent from the template
entirely) — and separately, a *different* kind of community resource for
the same game exists: a full data-editing GUI application with source
available (C#/C++/Python, not just a struct doc), even one whose own README
doesn't claim to solve your specific unknown.

Passive templates and active editor tools are usually treated as the same
kind of source and consulted together once. They aren't interchangeable:
a GUI editor's source has to actually *read every field it lets you edit*,
so it sometimes documents a whole section/subsystem (with real field names)
that a template author never got to. Confirmed on Fire Emblem: Three
Houses (`chimera`): the already-consulted `010-binary-templates` repo's
`PersonData.bt` left a 12-byte span (and, more importantly, gave no hint
that the file's PersonData section *1* — one of 18 sections whose outer
pointer table was already fully confirmed — held anything at all) as
undecoded. A `WebSearch` for the game name plus "asset id" plus "model"
surfaced `three-houses-research-team/Progenitor`, a full C# data-editing
GUI whose own `DataFiles/PersonData/Sections/AssetIDBlock.cs` documents
section 1 as a real, named 9-field struct (`part1Body`/`part2Body`/etc.) —
exactly the section that turned out to hold the character/model-id mapping
(see `weak-single-offset-fit-signals-missing-indirection.md`). The tool
itself never resolves those ids to a mesh file (no DATA0/archive awareness
in its own code) — it names fields it never actually decodes downstream,
which is exactly the shape of prior art worth grepping for: `find . -iname
"*.cs" | xargs grep -li "asset\|model"` over a cloned editor's source is a
cheap, fast way to surface a section name/struct a passive template omitted.

**But verify the tool's own read loop against the container's real,
self-describing size field before trusting its field count/order.**
Progenitor's `AssetIDBlock.Read()` calls `ReadInt16()` nine times per
record (18 bytes) with no explicit per-record re-seek, while the real
on-disk stride — read directly from the section's own 64-byte header field
(the same self-describing mechanism the whole container family already
used) — is 16 bytes (8 fields). The tool's 9th field per record is
therefore silently the *next* record's first field re-read one position
late; confirmed via `altFaceID[i] === ngplusHair[i+1]` holding across the
whole real corpus (i.e. the "extra" field it defines is fully explained as
an off-by-one artifact, not real data). A GUI tool with source available is
still a *hypothesis generator* for field names/roles, not ground truth for
stride/count — the container's own declared record size settles that, the
same way `record-stride-guess-vs-recount-fields.md` treats a disassembly
reader's field list.
