# A confirmed field width — or hardcoded constant-selection branch — can be unfalsified, not verified, if the first corpus never exercises its full range

**When it bites:** you're reusing a decoder "confirmed" byte-exact on one game against a sibling on the same engine, platform format or container, especially when the sibling's files are larger or it carries a header/version value never seen before. Also: a vendored reference tool (vgmstream, a 010 template) refuses or garbles a structurally valid file outside its authors' test set.

A narrow read and the correct wide read are bit-identical whenever the high bits are zero. A hardcoded constant and the correct selector agree whenever the selector only ever took one value. "Zero errors across the whole corpus" therefore means "correct for every value this corpus happened to contain", not "verified field-width fact". The failure on the sibling is usually silent: well-formed garbage values, uniform-entropy output, or fields that echo each other, rather than a crash. Upstream tools are overfit to *their* corpus in the same way, through equality gates or templates scoped to "the common case".

**Check / fix:**
- Before reuse, mark as **unfalsified** any field whose observed values never approached the narrow type's max, and any hardcoded constant or branch whose selector field took only one value. Corroborate it independently: the reference implementation's source, a second oracle, or a structural invariant that only holds at the right width or constant.
- After widening or fixing, run the old corpus again. A byte-exact no-op there proves the bug was being masked, not introduced.
- **Detect silent garbage** by cross-checking already-parsed fields against each other (one field byte-identical to another, `packetCount=1` for 3.5 M samples), and with a magic-byte oracle inside decrypted or decoded content (e.g. an embedded PNG signature).
- **Third-party gate refusals:** patch only the gated field in a scratch copy. A clean decode proves the rest of your structure is right and only the gate is overfit. Check whether a template's header comment scopes it to one codec or variant.
- **When you find a sibling's changed constant, run both values over 100% of the new corpus.** The new one should succeed N/N and the old one fail N/N. "Same engine, byte-identical reader code" licenses reusing the *structure*, never the *offsets*.
- **A field constant across the whole corpus** pins the layout but not the semantics. Prefer the candidate reading that turns the constant into a *neutral* value (identity matrix rather than a 180° quaternion), and document that the corpus never exercises it.

**Canonical example:** Dungeon Hack (`crawl`, AESOP/16, shared with Eye of the Beholder III). `eotb3lib/bitmap.py` read the old-format sub-image offset table as `u16` per 4-byte slot, byte-exact and zero-error across EOB3's whole `EYE.RES` corpus, because no EOB3 resource in that format exceeds 64 KB. Dungeon Hack's `"Drawbridge"` (130,544 B, 6 frames) needs offsets past 65,535. The `u16` read produced dimensions like `1544×1285` and `56025×1499` with no error. Widening to `u32` fixed it and was pixel-identical across all prior EOB3 output.

**Variants:**
- `flower`, PS3 `.EDAT`/`.SDAT` (`tools/shared/ps3-edat.ts`): the decoder hardcoded `EDAT_KEY_1` (all Drakengard 3 files are `NPD.version 4`). NieR's version 2/3 files decrypted to uniform garbage. The fix was RPCS3's `version == 4 ? EDAT_KEY_1 : EDAT_KEY_0`, validated by an inner `ICON0.PNG` signature.
- `flower`, NieR X360 AIX: vgmstream `meta/aix.c` hard-rejects when `u32be@0x0c != 0x800` (a field it labels "header size?"). NieR's per-file values differ. Patching that one field produced a correct 6-channel/48 kHz decode.
- `chimera`, Fire Emblem Warriors KTSS: the community `KTSS.bt` covers Opus (`codecID=9`) only. FE Warriors is entirely `codecID=2` (DSP-ADPCM, per vgmstream `ktss.c`). `audioOffset` read back identical to `sampleCount`.
- `chimera`, FE Warriors `G1CO`: all 211 boxes carry an exact identity 3x4 matrix, so the layout is pinned and "orientation" stays a hypothesis.
- `nicodemus`, Phantasie I (Amiga) vs II (Atari ST): instruction-identical readers, but the icon list sits at offset 1000 vs 1500 (record grew 2500 → 3000). 1500 parses 17/17 and 1000 fails 17/17.

Siblings: `fixed-stride-record-count-unverified.md`, `record-stride-guess-vs-recount-fields.md` (the same range-limited-first-corpus root cause).

**History:** 6 recorded instances (crawl, flower, chimera, nicodemus): full log in `_archive/format-field-width-unexercised-by-first-corpus.md`.
