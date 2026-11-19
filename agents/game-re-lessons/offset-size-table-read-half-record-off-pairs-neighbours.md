# An {offset, size} table read half a record off still mostly works — every size belongs to the neighbour

**When it bites:** a two-field directory (`{lba, size}`, `{offset, length}`) was located by a VA, a guessed header size, or a field order borrowed from a sibling. Nearly every entry decodes, but a few overrun into the next file or fail validation, and they are being filed as format anomalies.

Shift the read by half a record (4 bytes of an 8-byte record) and the two fields swap roles: what you call entry n's offset is really a size, and its "size" is entry n+1's offset — or, with the opposite shift, entry n's size is paired with entry n+1's LBA. Files on a disc are mostly allocated contiguously and similar in size, so the neighbour's values are plausible and most decodes still work. The failures cluster where neighbours differ in kind (audio followed by video).

**Check / fix:**
- Test the **whole table**, not entries: under each field order and base, count records that tile contiguously (`lba[i] + ceil(size[i]/sector) == lba[i+1]`) and records that overlap. Compare with a shuffled-size null; a wrong reading tiles at chance.
- Anchor one record on a known file (an ISO directory entry's exact LBA and size).
- If the table lives in an executable, derive the file offset from the section header — VA ≠ file offset (`file-offsets-vs-segment-relative.md`).
- Once the re-read tiles, treat "anomaly" rows built on the old reading as refuted premises.

**Canonical example:** Chaos Legion (PS2, `flower`), sound driver `CAPSDRVD.IRX`. The repo read `addr = 0xb1e4 + fno*8` as `{size, lba}` from the VA; `.data` is at VA 0xb1e0 but file offset 0xb290. Read as `{u32 lba, u32 size}` from 0xb290, 206 of 220 records tile the disc with 4 overlaps; the repo's pairing tiled 44 and overlapped 75, against 39/86 for a shuffled-size null. Record 174 became exactly `LEGION.DAT` (LBA 2,082,755, 403,369,984 B). All 40 fno then validate 100% as PS-ADPCM (previously 38; the two "anomalous" entries existed only because the borrowed size ran past audio into FMV video).

**Variants:**
- Devil May Cry's sibling driver (`TSNDDRVM.IRX`) uses the same `{lba, size}` order: 552/552 records whose LBA starts an ISO file carry its exact size.

Related: `adjacent-ramp-table-masks-off-by-one-record-start.md` (whole-record shift), `platform-port-swaps-adjacent-header-fields.md` (swap within one header), `check-that-cannot-fail-is-not-evidence.md`.

**History:** 1 instance (flower Chaos Legion, 2026-11-18 audit), sibling confirmation on DMC.
