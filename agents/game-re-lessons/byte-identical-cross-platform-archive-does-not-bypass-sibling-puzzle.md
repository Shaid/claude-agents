# A byte-identical archive across a platform port inherits the sibling platform's open puzzle unchanged

**When it bites:** starting a "companion" investigation of a new platform
port/re-release, especially when hoping it might be *less* obfuscated than
an already-partially-solved sibling platform and could shortcut a stalled
sub-problem (an unsolved codec, an unlocated pixel region, an unresolved
vertex format).

Before assuming a new platform's version of a resource is worth
re-investigating from scratch, MD5/byte-compare it against the sibling
platform's already-extracted copy. If it's identical, **every already-open
problem about that resource is still open** — a same-named archive shipped
verbatim across a port carries its unsolved puzzle over intact, because the
bytes literally didn't change. Don't spend a session re-deriving container
structure, testing decode hypotheses, or hunting for pixel/vertex data in a
resource that's already been shown byte-for-byte identical to a sibling
platform's copy — any progress made there is progress that *directly
transfers back* to the original platform's docs (and vice versa), so check
identity first, before investing decode effort.

This cuts both ways usefully: **finding non-identical byte-for-byte** is
itself a strong, cheap, early signal that the new platform's copy *was*
touched (re-encoded, rebuilt, or replaced) and is worth investigating on
its own merits — while finding identity is a strong signal to redirect
effort toward genuinely different resources instead.

Confirmed on Zone of the Enders: The 2nd Runner. The PS3 "HD Collection"
build's `ZoE2/ZOE2/STAGE.DAT` (417,091,584 bytes) is MD5-identical to the
PS2 disc's `STAGE.DAT` — same Konami MGS-family cipher, same still-open
mesh-vertex-encoding and texture-pixel-location puzzles the PS2 investigation
had already spent multiple `re-codebreaker` passes on. The PS3 build's
per-stage `.bin` overlay files turned out to be a completely unrelated,
genuinely new resource (compiled PS2 EE machine code — see
`script-files-may-be-native-code-bound-to-fixed-memory-map.md`), while three
*other* same-named archives on the same PS3 disc (`MOVIE.DAT`, `DEMO.DAT`,
`VOX.DAT`) were confirmed **not** byte-identical (different sizes, and
`VOX.DAT`'s shared 16-byte "FS stream" header shape flipped from
little-endian on PS2 to big-endian on PS3) — correctly flagging those as
platform-specific rebuilds worth their own investigation, unlike
`STAGE.DAT`.
