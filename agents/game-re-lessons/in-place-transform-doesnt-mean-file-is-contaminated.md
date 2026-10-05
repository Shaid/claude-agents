# In-place-transform-doesn't-mean-file-is-contaminated

**When it bites:** A code-verified vertex/pixel transform runs **in place** on a loaded buffer,
and a sibling doc/brief explains away weird-looking extracted data as
"already-transformed values mixed with raw data" — before you check whether
the file you're reading is actually the buffer the transform touched, and
whether the data class you're decoding is even the transform's input class.

## The trap

The ZOE2 model buffer (PS2) has a disassembly-verified in-place vertex
transform (s16 coords, stride 12/18, writes `sh v0, (a2)` back over the
buffer). A prior pass read the file's 4-byte u8 record streams as s16 pairs,
got values like `(771, 774)`, `(6167, 6168)`, and concluded the file
contained "already-transformed GS coords mixed with raw data" from a
previous game session.

Two compounding errors:

1. **The file was pristine.** `file_0005.z` is the decrypted + inflated
   payload extracted from the disc (STAGE.DAT) — the game's in-place
   transform happens in RAM at load time and never touches the file. There
   is no "previous session" contamination in disc data.
2. **Wrong data class.** The s16 readings are misalignment artifacts of u8
   4-byte records: `771 = 0x0303 = bytes 03 03`, `6168 = 0x1818 = bytes
   18 18`, `8476 = 0x211C`. The tell: long *constant* runs in the s16
   reading (`6167, 6168` × many) are the same u8 byte repeated
   (`17 18 18 18...`), which is characteristic of a byte stream, not
   coordinates — coordinates don't produce run-lengths of one value.

## The fix

Before attributing weird decoded values to an in-place transform (or any
runtime mutation): (1) confirm the file's provenance — if it's a pristine
decrypt/inflate of disc data, no runtime mutation can have touched it;
(2) verify the bytes actually belong to the transform's input class
(same record stride, same field widths) rather than a sibling stream; and
(3) when values collapse into byte-pair artifacts (`0x0A0B` from bytes
`0A 0B`), that's a u8 stream read at the wrong width — histogram the
*byte* values and look for the repeated-byte signature before believing any
coordinate interpretation. See `crawl`/ZOE2 docs `data-structure.md` §4.6
correction for the worked example (the real index layer was found only
after dropping the contamination explanation).
