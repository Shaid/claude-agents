# A from-scratch glTF exporter's `UNSIGNED_SHORT` index buffers silently cap out at 65,535 vertices per primitive

**When it bites:** writing a hand-rolled GLB writer for a from-scratch
decoded 3D format (the `tools/epic/build.mjs` pattern — positions/normals/
indices as raw typed-array bufferViews, no external glTF library), then
reusing that same writer's index-buffer logic for a *larger* object in the
same or a sibling game's corpus than whatever it was first written
against.

## What went wrong

Frontier: Elite II (Amiga)'s glTF exporter (`tools/frontier/
build-gltf.mjs`) was templated closely on `tools/epic/build.mjs`, whose
`writeGLB()` always uses a `Uint16Array` (glTF componentType `5123`,
`UNSIGNED_SHORT`) for index buffers — correct for Epic's objects, all
small. Frontier's submodel-assembly pipeline can flatten a deeply
recursive object (station model 54: 12,587 resolved submodel instances)
into a single per-colour face group with 91,724+ vertices — past the
65,535-vertex ceiling a `Uint16Array` index can address. The first attempt
threw a hard `RangeError`-style overflow (values silently wrapping/
truncating would have been worse — a thrown error at least surfaced
immediately rather than producing a corrupt-looking GLB).

## The fix

glTF 2.0's accessor `componentType` permits `5125` (`UNSIGNED_INT`, 4-byte
indices) for exactly this case, and three.js's `GLTFLoader` (the consuming
engine in this family of projects) handles it transparently with no extra
configuration. Pick the index array type and `componentType` per primitive
based on that primitive's own vertex count (`> 0xFFFF` → `Uint32Array` +
`5125`; otherwise `Uint16Array` + `5123`) rather than hardcoding one
choice — a smaller reference implementation (Epic here) that never needed
the wide-index path is not proof a sibling game's own largest objects won't.
Verify with the official validator across the *whole* corpus (see
`external-validator-sample-insufficient-cli-spawn-slow.md`), not just a
sample, since only whichever corpus member happens to be the outlier
surfaces this.
