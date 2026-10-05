# A serialized record's float/element payload need not be aligned — pin its start by arithmetic across every observed record size

**When it bites:** a variable-length record's header is decoded (magic,
size, a type byte) but the payload immediately after it decodes to garbage,
and every candidate start offset you're trying is a multiple of 4 because
"floats are 4-byte aligned." Also bites the other way: a payload *does*
decode to plausible values at an odd offset and you distrust it for being
unaligned.

Serialized (as opposed to memory-mapped) record formats routinely pack
records back to back with no inter-record padding, so a payload that starts
at an odd offset within a record sits at a *different* absolute alignment in
every record of the file. That is legal and common — the reader streams
fields rather than casting a struct pointer — and `DataView.getFloat32` /
`memcpy`-style reads handle it fine.

**The arithmetic pin, which needs no plausible-value eyeballing:** if the
payload is `N` elements of width `w`, then `(recordSize - payloadStart) % w
=== 0` must hold for *every* record. Sweep `payloadStart` across the small
window just past the known header fields and keep only the values that
satisfy it at **all** observed record sizes simultaneously. With two or more
distinct record sizes in the corpus this usually leaves exactly one
candidate.

Confirmed on Fire Emblem Warriors (Switch, `chimera`), the `"OC1G"`
collision-primitive record: three record sizes exist (37 / 57 / 97 bytes),
and `+0x11` — an odd offset, one byte past a `shapeType` discriminator — is
the **only** start in `+0x10..+0x14` for which `(recordSize - start) % 4 ===
0` at all three sizes at once (`+0x10` leaves remainder 1, `+0x14` leaves
17/37/77). All 271 records in the corpus satisfied it with zero exceptions,
and the resulting floats were immediately sane (round world coordinates,
exact `0.0` pads, an exact identity matrix). Records land at arbitrary
absolute alignments as a result — record 0 at file+0x10, record 1 at
file+0x71, record 2 at file+0xd2 — which is exactly what the format
intends.

Corollary worth remembering: a record size that is *odd* (37, 57, 97) is
itself the tell that the format is a serialized stream with no alignment
discipline, so stop requiring aligned offsets the moment you see one.
