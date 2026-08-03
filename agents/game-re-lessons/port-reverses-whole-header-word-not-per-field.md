# A cross-endian port can reverse a whole multi-field header word, not swap each field's own byte order

**When it bites:** the same directory/reference-list struct is shared
across a big-endian and a little-endian port of a container format, a
per-entry field (an offset, a size, an index) resolves correctly on the BE
port but only partially or implausibly on the LE port even after applying
the expected per-field endian conversion — especially when a permissive
"fallback: recompute this from context instead of trusting the stored
field" path exists elsewhere in the same parser and could be silently
absorbing most of the damage.

Don't assume porting a struct across endianness only changes each
multi-byte field's own internal byte order (`u16`/`u32` swapped in place,
field positions unchanged). A straightforward way to port C code that reads
a packed struct field-by-field is to byte-reverse the *whole* backing word
and read fields out of the reversed bytes with the same field-extraction
code — which silently changes which **byte range** each field occupies,
not just the numeric interpretation of any one field. A 4-byte
`{u8 attributes, u24 dataOffset}` word (attributes as the high byte of a
big-endian 32-bit read) becomes, under a full 4-byte reversal for
little-endian access, `{u24 dataOffset LE, u8 attributes}` — the offset
now occupies bytes 0-2 and the flag byte moves from byte 0 to byte 3, not
just "the same 3-byte field, read backwards."

**Confirmed** on three different games sharing one resource-fork container
format (Conan the Cimmerian, Warriors of Legend, War in Middle Earth — all
Melbourne House/Synergistic titles, `~/Development/middilgard`): the
BE (Amiga) reference-list entry is `[u16 id][u16 nameOffset][u8 attributes]
[u24 dataOffset BE][u32 reserved]`; the LE (DOS/IIGS) port keeps the same
12-byte entry size but is `[u16 id][u16 nameOffset][u24 dataOffset LE]
[u8 attributes][u32 reserved]` — the attributes byte and the 3-byte offset
swap which byte range they occupy, not just their own internal order.
Reading the LE file with the BE field positions (attributes at +4, a
"u24 LE" read starting at +5) produced offsets that landed tens of
thousands of bytes past the real data section on every LE file tried.

**Why it stayed hidden:** the parser had a permissive fallback for exactly
this failure mode — when a computed offset looks implausible ("stale"), it
falls back to sequentially walking the data section and assigning blobs to
records in map order, which needs no per-entry offset field at all. That
path absorbed the bug for the *majority* of entries (every implausible
offset triggered it), so overall pipeline output looked fine. The bug only
surfaced as **wrong id-to-data pairing** for the minority of entries whose
mis-read offset happened to still look plausible (in-bounds, a sane-looking
declared length) by chance — those escaped the fallback and got silently
paired with a neighbouring record's bytes instead of their own.

**The verification that caught it, cheaply, with no ground truth needed:**
a directory's per-entry offsets should almost always be monotonically
increasing (data laid out in file/map order). Compute the candidate offset
under both field-position hypotheses across every entry in a file and check
which one is monotonic — the wrong hypothesis showed scattered,
non-monotonic offsets on every file tried; the corrected one was
monotonic on all of them (236, 161, 31, 11 entries respectively), with
per-entry lengths that resolved to sane, in-bounds values. A stronger,
independent confirmation followed once available: decoding the same
resource on two ports and comparing all fields — the fix took a
cross-platform field-agreement check from mostly-disagreeing to
6,372/6,372 exact matches.

**Fixing a shared container-parser bug like this can retroactively
overturn several already-recorded findings** that were quietly built on
mis-paired data — in this case, two "decode failure" resources turned out
to be fine once correctly paired, one "confirmed" render was reattached to
a different real resource entirely, and a set of "exception" ids all
shifted by one. Treat that as expected fallout, not a new set of separate
bugs to chase — re-verify anything whose evidence depended on this parser
before touching it further.
