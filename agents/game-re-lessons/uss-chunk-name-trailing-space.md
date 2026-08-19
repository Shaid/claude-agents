# A UAE-family `.uss` savestate chunk's 4-byte tag can carry a trailing space that `findChunk` won't forgive

**When it bites:** looking up a specific chunk (especially `"CPU"`) from a
UAE-family (WinUAE/FS-UAE/Amiberry) `.uss` savestate via `findChunk(chunks,
name)` (`@seer-project/amiga`'s `uss.ts` or an equivalent hand-rolled
walker), and getting `undefined`/a thrown error from the next call (e.g.
`inflateChunk`) with no indication why — especially when a raw chunk-name
dump (e.g. from `scanChunks`) shows the chunk clearly exists.

Chunk names in this format are a fixed 4 ASCII bytes, and several of the
common ones are shorter than 4 characters and get right-padded with a
literal space, not a null or left-padding: the CPU-state chunk's real tag
is `"CPU "` (space at the end), not `"CPU"`. A lookup for the 3-character
string silently fails — `Array.prototype.find` just returns `undefined`,
there's no exception at the lookup site itself, so the failure surfaces
one level down (a `chunkPayload`/`inflateChunk` call throwing on `undefined
.payloadOffset`) in a way that can look like a savestate-parsing bug rather
than a wrong search key. Confirmed on Wings (Amiga): `findChunk(chunks,
'CPU')` returned `undefined` for all 3 supplied savestates even though
`scanChunks` had already listed a `"CPU "` entry (22,764-byte payload) in
each one; switching the lookup to `'CPU '` (with the trailing space)
immediately worked.

**Fix:** always read the exact 4 raw bytes of a chunk's name from a
`scanChunks`-style listing (or a hex dump of the chunk stream) before
searching for it by string literal — never assume a 3-letter chunk
abbreviation is stored as a 3-character string. This generalizes past
`.uss`: any fixed-width tag/magic field that's shorter than its declared
width is a candidate for silent right-padding (space, in this format) that
breaks a naive string-equality lookup without ever raising an error at the
lookup itself.
