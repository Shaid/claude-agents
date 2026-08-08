# One in-house format using hardware-packet encoding doesn't mean a sibling format in the same engine does too

**When it bites:** you've just cracked one proprietary format in an engine
by discovering it embeds literal platform hardware packets/microcode
(GS register writes, VIF/VU upload tags, GPU command-buffer fragments...)
instead of a clean struct, and you're about to carry that same paradigm
into a *sibling* format from the same engine/game as your leading
hypothesis for a still-unsolved binary layout.

It's a reasonable hypothesis to test first — engines are internally
consistent more often than not, and hardware-packet embedding is exactly
the kind of low-level convention a single in-house toolchain would reuse
across asset types. But it is a hypothesis, not a transfer of confirmed
fact, and it can be cleanly wrong even within the same game's own asset
pipeline: Cavia Inc.'s `wZIM` texture format (Drakengard/Drakengard 2)
embeds literal PS2 GS register-write packets (see
`ps2-inhouse-texture-embeds-gs-register-packets.md`), and the sibling mesh
format `CSFg` — same engine, same two games, same era — was a strong
candidate to follow suit. It doesn't: `CSFg` is a plain little-endian
struct/array format with zero VIFcode, GIFtag, or GS register address
anywhere in it. Different asset types apparently went through different
authoring/export tools even within one in-house pipeline (textures likely
captured straight off a real hardware DMA trace or debug-capture tool;
meshes exported from a modeling tool's own serializer).

**Test it fast and be willing to fully discard it.** The refutation itself
was cheap here — a scan for the sibling format's own register-address byte
patterns (see the wZIM lesson) coming back with zero hits across the
corpus was decisive and took minutes, not hours. The expensive mistake
would have been spending a long stretch trying to reinterpret ordinary
struct fields as fragments of a hardware packet stream because "the other
format in this engine does that."

**Second confirmed instance — and it runs the other direction, which is the
sharper trap.** A later session on the same two games found a genuinely new
DG2-only *sub-format* of `CSFg` itself (identified by a header sentinel,
tag names all beginning `VU1`) that turned out to embed literal PS2 VIF1
DMA source chains (`STCYCL`/`UNPACK`/`FLUSH`/`MSCAL` sequences, real
GIFtags forwarded to the GS) — i.e. the *exact* hardware-packet paradigm
this lesson's own headline finding had just ruled out for `CSFg`. Both
conclusions are correct simultaneously: ordinary `CSFg` (97.6% of the
corpus) is still a plain struct with zero hardware packets, and this
narrower `VU1` sub-format (2.4% of the corpus, a distinct on-disk shape
sharing only the outer magic) genuinely does use the paradigm. The
takeaway isn't "the first refutation was wrong" — it's that **ruling the
paradigm out for a format's dominant/first-discovered shape doesn't rule
it out for every variant sharing that format's magic.** When a sizeable
minority of a format's corpus fails a "confirmed" decoder (here, 231-304
of ~2,700-12,900 depending on how the population was counted — see
`shallow-magic-scan-undercounts-sibling-magic-corpus.md` for why that
count itself needed correcting), don't assume the failures are more of the
same struct with a bug; check whether they're structurally distinguishable
(a header sentinel, here) and re-open the hardware-packet hypothesis for
*that specific subset*, independent of what was already concluded about
the format's main shape.

**A related trap surfaced while re-deriving the correct struct reading for
`CSFg` after the packet hypothesis was dropped:** a fixed-size buffer
holding a NUL-terminated tag string followed by a NUL-terminated name
string was originally documented as "tag, then name, then sometimes a
*second* name" — because a few samples showed a plausible-looking third
string fragment after the second NUL. It wasn't a field at all: the buffer
is a fixed 32-byte allocation, and anything past the second real string's
NUL terminator is just **stale, never-cleared memory content left over
from a previous use of that buffer slot** by the original authoring tool —
unrelated to the record it appears attached to. The tell was semantic
mismatch (the trailing fragment named an anatomically unrelated body part)
combined with it not affecting any downstream field's fixed offset either
way (the *next* real field always sits at the same absolute offset
regardless of how much of the 32-byte buffer the real strings used) —
a genuine field would have shifted subsequent offsets; stale buffer
content doesn't, because nothing downstream ever reads it.
