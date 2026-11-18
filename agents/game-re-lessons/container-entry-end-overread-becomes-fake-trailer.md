# Verify a container entry's end, not just its start

**When it bites:** a container's offset rule was "confirmed" by checking where entries start. Downstream formats then show a "real 4-byte trailer", a field that equals "size − 4", a "+4 shortfall" written up as an invariant, or a "sequential id" field. Or you're about to "correct" a reference doc by shifting every field 2 bytes.

An offset rule can place every start correctly and still compute each end a few bytes too far, into the next list's header or the next entry's size prefix. Or it can start the first record one field early, so every record carries its neighbour's first field. Each consumer of the container then finds the same constant residual on its own and documents it as a property of its own format. The residual is real, consistent and zero-deviation, which is why it gets mistaken for structure.

**Check / fix:**
- For every entry, compare the **computed end** with the start of whatever follows it: the next entry, the next type list's header, the next stream's size prefix. A constant overrun (+4, +2) across thousands of boundaries is a framing bug.
- Null control for a claimed trailer: group records whose bodies are identical apart from the "trailer". Real per-record content can't differ between identical records; buffer garbage from an over-read does.
- If a residual equals the size of a header word you know (a `u32` size, `[type, count, 0, 0]`), read that word at each boundary. It is usually the next structure's header, and it often gives you the stored sizes you thought were missing.
- For record tables: if the "trailer" or "anomaly" sits only on the first or last record, try starting one field earlier or later. Check for a count word at offset 0 and an end-of-table terminator. A field that "always equals record index + 1" is the next record's id.
- When a reference doc disagrees with you by a constant field shift, check your own framing before "correcting" the reference.

**Canonical example:** FF9 (PSX) DB archives. The documented end rule `OffsetListStart + M*4 + EndOffset` overran the next type list's header by exactly +4 on 10,080 boundaries over 6,394 archives. So the last file of every list carried the next list's `[dataType, count, 0, 0]`. That one bug was documented separately as BTL_SCENE's "real, varies per record" 4-byte trailer (72 of 360 identical-body groups had different "trailers"), as AKAO `+0x06 = size − 4` (59/59), and as a sample-bank "always-present 4-byte footer". The 2026-08 correction had checked starts only.

**Variants:**
- Powermonger DOS `.HUF`: `sum(compressedSize) == blobLen + 4` was called a zero-deviation structural invariant, and only entry 0's size was "recorded". Every entry actually begins with a u32 LE original size (54/54: 64000, 32000, 768…). The +4 was that prefix, and the "partial 640/407/367-byte palettes" were full 768-byte palettes.
- EOB3 `ITEMTYPE.DAT`: read from offset 0, the fields came out 2 bytes off ThirdEye's layout, and a doc "corrected" ThirdEye. The first u16 is the record count (64, 1,026 = 2 + 64×16), and the "trailing `0x0004`" is the last record's `extraProperties`. ThirdEye and ScummVM were right; the file is EOB2's verbatim (md5).
- MH4U `.arc`: the parser read each entry's name from the following 0x50-byte window, so each entry got entry i+1's name. Texture linking only worked by luck of the tex→mrl→mod ordering.
- Warriors of Legend `restart.dat`: records started 2 bytes late, so "sequentialId at +0x1B" was the next record's id and the "final record anomaly" was the `0xFFFF` terminator.

Related: `sibling-length-field-disagreement-read-past-real-stream.md`, `redundant-offset-field-poisoned-chain-by-length.md`, `trailer-offset-locates-real-header.md`, `adjacent-ramp-table-masks-off-by-one-record-start.md`, `decoder-output-length-check-is-tautological-assert-input-consumption.md`.

**History:** 5 projects (FF9, Powermonger, EOB3, MH4U, Warriors of Legend), 2026-11 audit sweep.
