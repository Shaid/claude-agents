# A decoder's "pass unrecognised input through untouched" fallback hides unhandled wrapper variants

**When it bites:** a shared decompressor/unwrapper handles the compressed forms it knows and returns anything else unchanged, so already-raw files can go through the same call. Nothing ever throws, so a wrapper form nobody wrote code for goes unnoticed: its payload comes out with the header still attached, and consumers either skip it or quietly produce garbage. The decoder's own tests stay green because they only exercise the forms the author already knew.

The fallback itself is reasonable. The trap is that it turns "unknown variant" into "success", so coverage numbers built on "decoded without error" count the misses as hits.

**Check / fix:**
- Over the **whole** population the decoder is applied to, histogram the leading type byte (and any header-size relation such as `u24 == fileLength - 4`), split by outcome: *decoded*, *passed through — raw magic recognised*, *passed through — unknown*.
- Every file in the *unknown* bucket is either a raw format whose magic you can name, or an unhandled variant. Name them all.
- Look first for a **stored / uncompressed** variant (type `0x00` + size + raw bytes): toolchains emit it when compression would not shrink the file.
- Gate a newly recognised variant on an exact size relation, so raw data that happens to start with the same byte can't be misread. Keep a null control (same leading byte, non-matching size) that still passes through.
- Add a real-data test that asserts the *unknown* count, so a new variant fails a test instead of slipping through.

**Canonical example:** Fire Emblem Fates (3DS, `lucina`). The shared `decompressLz13` (`@seer-project/3ds` `lz.ts`) handled LZ13/LZ11/LZ10 and passed everything else through. 31 `.lz` files (30 `field/*_t.bch.lz` terrain files plus `TextEditor.bin.lz`) were a stored wrapper: `00` + u24 (= fileLength − 4) + raw bytes, with the size relation holding on 31/31. They came back with the 4-byte header still on, and no test noticed. After the fix all 31 unwrap to fileLength − 4, and a leading-`00` file with a non-matching size still passes through.

Related: `decompress-then-inspect-scan-must-bound-entry-size.md` (cost of scanning compressed archives), `crunched-size-mistaken-for-decrunched-size-invariant-mismatch.md` (which size a wrapper field records).

**History:** 1 recorded instance (`lucina`, 2026-11-20).
