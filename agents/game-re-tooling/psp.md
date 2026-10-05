# PSP tooling

## radare2 auto-detects PSP ELF/PRX natively — but always confirm the file-offset delta

PSP `BOOT.BIN`/`EBOOT.BIN`/`*.prx` files are `ELF32`, `MIPS R3000` (the
Allegrex core), `Type: 0xffa0` ("SCE relocatable executable/module").
radare2 opens these with zero special loader work (`format: elf`,
`machine: MIPS R3000`), unlike several other console ELF variants this
project's `ghidra-loaders.md` needed a dedicated loader entry for.

Every PSP module observed so far has exactly **one `LOAD` program header at
file offset `0x60`, vaddr `0`** — i.e. `fileOffset = vaddr + 0x60` for
every section inside it. Don't assume this is universal without checking:
confirm it per-binary against the ELF's own `PhOff`/`Off`/`Addr` fields
(`readelf -l`/`rabin2 -l`), the same way this project already treats the
Amiga HUNK file-offset convention as "confirm per-binary, don't hardcode."
Cite PSP addresses in docs as vaddr with an explicit `+0x60` file-offset
note, not segment-relative-only (same convention as
`file-offsets-vs-segment-relative.md`'s general rule).

## No Allegrex-specific misdecodes found so far — one narrow ESIL false alarm, not a real gap

Unlike the PS2 EE's MMI extensions (a confirmed real tooling gap,
`vp2ps2-ee-mmi-disasm` in the crawl/valkyrie corpus), no Allegrex-specific
(VFPU or custom) opcode misdecode has been found in any code path traced
on this platform yet. The one anomaly seen: r2's `aaef` (emulation-based
xref) analysis pass can emit `esil_neg: unknown reg w5`/`w6` warnings —
these are r2's ESIL emulator choking on VFPU-register-name artifacts
during best-effort emulation, **not** evidence of corrupted/misdecoded
disassembly of real code. Don't treat this warning alone as grounds to
suspect the disassembly; check whether the actual instructions in the
traced function decode sensibly before escalating it as a tooling gap.

## Resolving cross-PRX shared-library calls: parse `.lib.ent`/`.lib.stub` directly from raw ELF bytes

PSP modules link to each other (and to Sony's own OS libraries) via a
**NID (numeric ID) export/import convention**, not by symbol name — a
`jal` to another module's function shows up as a call into that module's
own `.sceStub.text` jump-slot table, which by itself tells you nothing
about which library/function it reaches. r2's MCP tool wrapper had no
usable `list_imports`/`list_exports` output for this format in this
session (empty results) and its `search`/`list_strings` tools hit a
"Sandbox restricts search range" error identical to the one already
recorded for PS2 EE binaries (`vp2ps2-ee-mmi-disasm`) — **the raw
`r2`/`rabin2` CLI works fine for both** (string search, section listing),
so fall back to the CLI rather than assuming the format itself is
unsupported.

The real fix for resolving cross-module calls is a from-scratch parser
over two fixed-layout ELF sections (both trivial to read directly from
the file, no r2 needed once you have `rabin2 -S`'s section offsets):

- **`.lib.ent`** (what a module *exports*) — 16-byte records:
  `name_ptr(u32) version(u16) flags(u16) entLen(u8) vCount(u8) fCount(u16)
  entryTable_ptr(u32)`. `entryTable_ptr` points to `fCount+vCount` NIDs
  (u32 each), immediately followed by that many function-pointer vaddrs.
- **`.lib.stub`** (what a module *imports*) — 20-byte records, same
  leading fields plus `entLen=5` (words) instead of 4, then
  `nidData_ptr(u32) firstStubAddr(u32)`. `nidData_ptr` points to `fCount`
  NIDs in the **same order** as that module's own per-function stub jump
  slots, which are `8` bytes apart starting at `firstStubAddr`.

This gives a direct, mechanical resolution: for a call `jal <stub_addr>`
inside module A that imports library L, compute
`index = (stub_addr - firstStubAddr) / 8`, read `nid = nidData[index]`,
then search library L's *exporting* module's own `.lib.ent` NID→address
table for that same `nid` to get the real function body to disassemble.
No symbol names survive this process (PSP NIDs are just hashes/IDs, no
public name unless it's a well-known Sony syslib NID you can look up), but
the address resolution itself is exact and needs no guessing. Confirmed on
Valkyrie Profile: Lenneth (PSP) — resolved a shared `vpLibrary` (a
custom, game-specific 109-function API, not a Sony syslib) exported by
`BOOT.BIN` and imported identically by all 8 of the game's `*_master.prx`
per-mode modules, finding the real cross-module implementation of a
file-resource-access API this way. `BOOT.BIN` on this title also exported
a **1,971-function** `libraryXP` — PSP titles can link substantially more
of their own engine code through this NID mechanism than might be assumed
from a first glance at one module's own `.text` size.

**Tail-call trampolines are common at the resolved address.** The real
implementation is often not at the resolved NID address directly, but one
or two `j <addr>` hops away, frequently with a pointer-dereference in the
branch-delay slot (e.g. `j 0x4aa94 ; lw a0,(a0)` — jump to the real body,
having first replaced the incoming struct-pointer argument with one of
its own fields). Follow these before concluding a resolved NID's body
"does nothing" — a bare 2-instruction function that's just `j`+delay-slot
load is a trampoline, not a no-op (the general shape this project already
tracks for other platforms in
`boring-resolved-call-can-be-a-real-noop.md`, but the trampoline case
specifically needs one more hop followed, not a semantic-plausibility
judgement call).

## PSP `sceMpeg`/`MpegDemux` ATRAC3+ extraction is a confirmed cross-project mechanism — check for it before re-deriving

Any PSP title's movie/cutscene audio track that comes back as ATRAC3+
inside a PSMF/MPEG-PS-shaped container (`ffprobe` finds the H.264 video
stream fine via ffmpeg's stock `mpegps` demuxer, but reports **zero** audio
streams) needs a manual PES-walk — ffmpeg's own demuxer does not recognize
this substream on its own. `~/Development/valkyrie/tools/shared/
psp-atrac3p-audio.ts` (built for Valkyrie Profile: Lenneth's PSP remaster)
implements this: walk `0xBD` (`private_stream_1`) PES packets, strip a
4-byte PSP mux sub-header, concatenate into a "slot stream" framed by a
`0x0F 0xD0` sync word + a 2-byte size code, then wrap the resulting raw
ATRAC3+ elementary stream in a minimal hand-built Sony OMA/`"EA3"` header
so ffmpeg's stock `atrac3plus` decoder can take it from there — zero
codec reimplementation needed (per
`standard-codec-delegate-to-trusted-decoder-not-hand-reimplementation.md`).

**Confirmed to transfer byte-exact to a second, unrelated PSP title**: The
3rd Birthday (`~/Development/parasite`) ported the module verbatim and it
walked a real PSMF sample to 692 frames of a constant 744 bytes with zero
remainder, decoding to real non-degenerate PCM — the framing is PSP-SDK-
wide (`sceMpeg`), not specific to either game. Per
`game-re-tooling/seer-upstream.md`'s "one project needing it is a maybe;
two confirms it" rule, this module is now a real `@seer-project/pipeline`
promotion candidate (not yet migrated as of either project's own pass —
check both projects' `tools/shared/psp-atrac3p-audio.ts` for drift before
assuming they're still identical, and prefer extending/upstreaming over
maintaining a third divergent copy if a future project needs it too).

## Retail `~PSP`-tagged EBOOTs need KIRK/AMCTRL decryption this account has no tooling for yet

A PSP retail `eboot.bin` that starts with the literal `~PSP` tag is Sony's
scrambled/encrypted executable format (KIRK CMD1 + AMCTRL), not a plain
ELF — `readelf`/`rabin2`/radare2's native PSP ELF auto-detection (see
above) cannot touch it until it's decrypted first. Confirmed on The 3rd
Birthday (`~/Development/parasite`): `eboot.bin` opens with `~PSP`, and a
sibling `boot.bin` some retail dumps ship alongside it was **entirely
zero-filled**, not a usable pre-decrypted fallback (don't assume a
same-directory `boot.bin` is always a decrypted copy of `eboot.bin` — check
its actual bytes before relying on it). No decryption tool was available
in that project's environment: no `prxdecrypter`, no PPSSPP install (whose
`Core/ELF/ParamSFO.cpp`/`Core/HLE` machinery embeds real per-title KIRK
keys and could decrypt many commercial titles), no standalone kirk-engine
library. Building a from-scratch KIRK CMD1 decryptor plus sourcing the
correct per-title key is a real, non-trivial undertaking, not a quick
fallback — treat an encrypted `~PSP` EBOOT as **blocked** for disassembly
until one of those tools (or their embedded keys) is actually available in
the environment, rather than spending session time hand-rolling the
crypto. This is the account's first PSP title to actually hit this wall
(Valkyrie Profile: Lenneth's `BOOT.BIN`/`*_master.prx` files were
apparently unencrypted or already-decrypted dumps — no `~PSP` tag was
reported there); if a future PSP project needs real EBOOT decryption,
start by checking whether PPSSPP (source or a built copy) is available to
either decrypt via its own code path or be scripted/headless-run to dump
the decrypted image, before attempting a from-scratch KIRK implementation.
