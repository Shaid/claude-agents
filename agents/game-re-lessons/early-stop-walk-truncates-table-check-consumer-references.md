# A walk that stops at the first terminator, empty entry or unknown opcode truncates the table

**When it bites:** an extractor sizes a table, an action list, a command stream or a text record by stopping at the first `0`/terminator-looking value, the first 0×0 entry, the first unknown opcode, or a fixed-size read window. The output looks complete because the walk ended cleanly.

Games rarely scan for an end. They index directly (`base + id*stride`), read a fixed allocation, or walk a stream whose every opcode they know. Placeholder entries sit mid-table. A fill byte can also appear inside the addressable region. An opcode your walker doesn't know ends your walk, but not the game's. Everything past that point is dropped, and the counts derived from it ("N images", "zones with empty tables", "63 distinct items") inherit the truncation.

**Check / fix:**
- **Consumer-reference census.** Collect every index or offset that something else uses: script draw calls, map cells, star/trigger action indices, text pointers. Check that each one resolves inside the decoded extent. Any reference past your end is proof of truncation. A null control is a file whose references all fall inside.
- Size the extent from the game: the read length or allocation (`Read(name, buf, 0x9C4)`), the index width (an 8-bit index means up to 256 slots), the next structure's start, or the lowest data offset.
- Make the walker **fail loudly** on an unknown opcode or type, rather than returning as if at the end. Then learn that opcode's length (try each candidate and require every stream to end cleanly).
- Bound variable-length records by their own terminator or the next pointer, never by a fixed window, and assert each record ends on its terminator.

**Canonical example:** Phantasie I/II dungeon files. The action table was read up to the first `0x0D 0x0D`. But stars reference action slots past it in 6 files, 62 well-formed records in total (P2 `DNG6` alone has 33, including +Item and surprise-encounter records). The other 12 files reference nothing past their terminator, which is the null control. The game never scans: it reads a fixed 2,500-byte `DNG` buffer, and star indices are one byte, so the table is 256 fixed slots. The terminator test pinned the wrong model, and the item censuses undercounted.

**Variants:**
- AGOS (Elvira 1/II, Waxworks): the image walk stopped at the first 0×0 entry, but the placeholders sit mid-table. The full tables hold 1,654/3,273/4,381 images against 1,124/2,303/2,318, and every "empty zone" claim was false.
- Alien Breed 3D: the zone graphics walker returned on the first type-4 command. That command follows every floor, so water (type 7, which comes after it) was never exported. With type 4 = 4 bytes, 2,395/2,395 and 2,567/2,567 streams end cleanly.
- FFIV (SNES): dialogue was read through `rom.subarray(off, off+512)`. Only the records of 512 bytes or more were cut, mid-word. The "no garbage escapes" check could not see truncation.

Related: `terminator-scan-must-be-record-aligned.md`, `list-final-byte-is-a-data-value-not-a-terminator.md`, `jump-table-end-at-lowest-target-truncates-shared-handler-tables.md`, `fixed-stride-record-count-unverified.md`, `reference-debug-dumper-or-tool-helper-is-not-runtime-path.md`.

**History:** 4 projects (Phantasie, AGOS, AB3D, FFIV), 2026-11 audit sweep.
