# Uint8Array.toString() isn't Buffer.toString() — a TS port reads magic bytes as "67,86,77,72"

**When it bites:** TypeScript code calls `.toString('ascii'/'latin1'/…)` on bytes that may be a plain `Uint8Array` — a ported Python/C parser checking a magic string, or a decompressor's `Uint8Array` return passed into a `Buffer`-typed factory (`fromBuffer(buf: Buffer)`) whose downstream leaf code stringifies slices. Symptom: comma-joined numbers instead of text.

Node's `Buffer` honours `toString(encoding)`; a plain `Uint8Array` uses the generic Array `toString()`, returning `"67,86,77,72"` and silently ignoring the encoding. `new Uint8Array(buffer)` copies into a plain Uint8Array, not a Buffer. TypeScript's structural typing often accepts a `Uint8Array` where `Buffer` is declared, so the mismatch passes the call site and surfaces several calls later — looking like bad data or a broken decompressor/container walker rather than a type boundary.

**Check / fix:** normalize at the boundary — `const buf = Buffer.isBuffer(x) ? x : Buffer.from(x)` at the top of any decoder taking raw bytes, and wrap any decompressor's return in `Buffer.from(...)` before handing it to a `Buffer`-typed API (or normalize inside the receiving factory). Alternatively decode with `TextDecoder`. Never assume `.toString()` on a typed array produces text.

**Canonical example:** CRI ROFS CVM header: `parseCvmh(new Uint8Array(readFileSync(fixture)))` threw `Not a CVM header (got "67,86,77,72")` on on-disk bytes `43 56 4d 48`.

**Variant:** Drakengard (PS2, `flower`): `decompressV3a` (LZO1X, returns `Uint8Array`) fed to `CaviaSource.fromBuffer(...)` in `walkCaviaContainer`; a regression test showed `leaf.readAll().toString('latin1')` = `"102,112,107,0,..."` — a container *leaf*, not the decompressed buffer, looked wrong. Fixed with `Buffer.from(decompressV3a(...))` at the wrapping call site.
