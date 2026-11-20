# Archive: decoder-passthrough-fallback-hides-wrapper-variants.md

## 2026-11-20 — lucina (3DS): original candidate

# A decompressor's pass-through fallback hides unhandled wrapper variants

**When it bites:** a shared decoder handles the compressed forms it knows and returns anything else untouched, so that already-uncompressed files can go through the same call. No file ever throws, so a third wrapper form nobody wrote code for goes unnoticed. Its payload comes out with the header still attached, and consumers either skip it or produce garbage quietly.

The fallback is reasonable, but it turns "unknown variant" into "success". Coverage tests stay green because they only exercise the forms the author already knew about.

**Check / fix:**
- Over the full corpus of files the decoder is applied to, histogram the leading type byte and the header-size relation (for example `u24 == fileLength - 4`), split by outcome: decoded, passed-through-raw (with the magic recognised), passed-through-unknown.
- Every file in the "unknown" bucket is either a raw format whose magic you can name, or an unhandled variant.
- Look especially for a stored/uncompressed variant (type 0x00 + size + raw bytes): toolchains emit it when compression would not shrink the file.
- Gate a stored variant on an exact size relation, so that raw data starting with 0x00 can't be misread as one.
- Add a real-data test asserting the pass-through-unknown count, so that a new variant fails the test instead of slipping through.

**Canonical example:** Fire Emblem Fates (3DS). `decompressLz13` handled LZ13/LZ11/LZ10 and passed everything else through. 31 `.lz` files (30 `field/*_t.bch.lz` terrain files plus `TextEditor.bin.lz`) are a stored wrapper (`00` + u24 = fileLength-4 + raw bytes); the size relation holds on 31/31. They came back with the 4-byte header on, and the shared decoder's own tests never noticed. After the fix, all 31 unwrap to size-4. A null control (a leading 00 with a non-matching size) still passes through untouched.
