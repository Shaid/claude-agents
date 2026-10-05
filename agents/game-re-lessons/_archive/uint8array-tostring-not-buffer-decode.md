# Uint8Array.toString() isn't Buffer.toString() — a TS port reads magic bytes as "67,86,77,72"

**When it bites:** porting Python (`bytes`/`bytearray`) or C buffer code
to TypeScript, then calling `.toString('ascii')` (or any `.toString()`
with an encoding argument) on a plain `Uint8Array` — especially on bytes
just loaded from a fixture/read buffer — and using the result in an
equality check against a magic string. **Also bites at a decompressor-
output-to-container-wrapper boundary**: wiring a new codec into an
existing container-walking abstraction (e.g. a `Source`/`Buffer`-window
class used for recursive parsing) by passing a decompress function's raw
return value straight into a `fromBuffer(buf: Buffer, ...)`-style factory
— if the decompressor returns a plain `Uint8Array` (a very common return
type for a from-scratch decoder) and the factory's parameter is typed as
`Buffer`, TypeScript's structural typing frequently doesn't catch the
mismatch at the call site. The bug then doesn't surface at the
decompression step (which works fine) but several calls later, wherever
downstream leaf-consuming code calls `.toString(encoding)` on a `.slice()`/
`.subarray()` view of that wrapped source — producing the same
comma-joined numeric string, but the wrong-looking output is a container
LEAF's content, not the decompressed buffer itself, which can misdirect
debugging toward the decompressor or the container walker rather than the
`Buffer`-vs-`Uint8Array` type boundary. Confirmed on Drakengard (PS2,
`flower` project): wiring a newly-solved LZO1X-based decompressor
(`decompressV3a`, returning `Uint8Array`) into `walkCaviaContainer`'s
recursive leaf handling via `CaviaSource.fromBuffer(decompressed, ...)` —
a regression test caught it immediately (`leaf.readAll().toString('latin1')`
producing `"102,112,107,0,..."` instead of real text), fixed with
`Buffer.from(decompressV3a(...))` at the wrapping call site. Fix
generally: wrap any decompressor's return value in `Buffer.from(...)`
before handing it to a `Buffer`-typed API, or normalize inside the
receiving factory itself.

`Buffer` (Node) supports `toString('ascii')`; a plain `Uint8Array` does
not — its `toString()` is the generic Array one and returns
comma-separated byte values (`"67,86,77,72"`), silently ignoring any
encoding argument. `new Uint8Array(buffer)` copies a Buffer into a plain
Uint8Array (not a Buffer), so "load fixture → wrap in Uint8Array → check
magic" fails in a way that looks like the data is wrong, not the code:
the fixture is fine, the parse function is fine, the *string conversion*
is the bug.

CRI ROFS CVM header parse: a `parseCvmh(new Uint8Array(readFileSync(fixture)))`
checked `tag !== 'CVMH'` and threw `Not a CVM header (got "67,86,77,72")`
— the on-disk bytes were `43 56 4d 48`. The same trap sits in
`Buffer.from(x).subarray(...).toString('ascii')` paths if the source
object is a plain Uint8Array.

Fix: normalize early — `const buf = Buffer.isBuffer(x) ? x : Buffer.from(x)`
at the top of any decoder that takes raw bytes, and let Buffer's
`toString('ascii')` handle subranges; or use `TextDecoder` explicitly.
Never assume `.toString()` on a typed array produces text.
