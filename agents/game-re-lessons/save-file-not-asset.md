# A file never opened by literal name may be a save file, not an asset

**When it bites:** string-searching the executable for a data filename comes up completely empty, even though the file clearly exists and is loaded somehow.

Check whether the load path instead **enumerates a directory**
(`Lock`+`Examine`+`ExNext` or equivalent) via a file requester —
user-chosen filenames are never compile-time string literals, so a filename
search will never find them. This reframing cracked Frontier: Elite II's 5
"unknown compressed assets" as shipped savegames, ahead of any deeper
disassembly work.
