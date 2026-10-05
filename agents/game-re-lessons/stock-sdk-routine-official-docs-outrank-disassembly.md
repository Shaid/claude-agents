# A statically-linked stock SDK routine's official docs outrank re-deriving it from disassembly

**When it bites:** A math/formula question (rotation-matrix construction,
a transform, a checksum, a compression codec) sits inside a function that
turns out to be a **stock, unmodified library routine** from the platform's
official SDK — not project-specific game code — and there's no reference
decompilation project's C source to lean on for that specific routine, or
the reference project's own C source is itself an inference rather than a
byte-exact-matched translation.

## The situation

Parasite Eve II (PSX)'s animation blend path calls a function at a fixed VA
that a community "matching decompilation" project's own build config
(`configs/USA/main.yaml`) resolves to object `libgte/rmat_01` — i.e. it's
linked straight out of Sony's official `LIBGTE.LIB`, the same
`RotMatrix_gte()` every PSX game that uses the GTE coprocessor's rotation
helper links in unmodified. The community project's own `.c` source for
this routine (if it has one at all) is necessarily a *reconstruction*
compiled to match the object file bit-for-bit — useful, but not the
authoritative source for "what does this formula actually compute,
mathematically."

Sony shipped `Libref.pdf`, the official PsyQ library function reference,
publicly archived (e.g. `psx.arthus.net/sdk/Psy-Q/DOCS/Devrefs/Libref.pdf`).
It documents `RotMatrix`/`RotMatrix_gte`'s exact `M = mX × mY × mZ` formula
with the three per-axis matrices spelled out. For a stock SDK function,
this document is a **primary source** for the algorithm — stronger than
independently re-deriving the same formula from a disassembly trace, and
categorically different in kind from a community project's transcription.

## The technique

1. **Before disassembling a suspicious function's body, check whether it's
   project-specific code or a linked library routine.** A decomp project's
   own build manifest (`configs/*/main.yaml`, a `.map` file, a symbol
   table with a `.lib`/library-object annotation) usually says so directly.
   A function called from many unrelated places with no project-specific
   naming, sitting at a fixed low-churn address across game revisions, is
   also a tell.
2. **If it's stock SDK code, go find the SDK's own official docs first.**
   Search for the exact function name plus the platform's SDK name (e.g.
   `"RotMatrix_gte" PsyQ`, `"aski_gte" filetype:pdf`). Archived scanned SDK
   manuals for PSX/Saturn/N64/PSP-era platforms exist in more places than
   expected (`psx.arthus.net`, PDF archives of `Libref`/hardware manuals).
   `WebFetch` a raw PDF URL and convert locally (`pdftotext`) if needed.
3. **Still independently confirm the bit-level plumbing feeding the
   routine** (how the caller unpacks its input arguments) via your own
   disassembly — the SDK doc tells you what the *library function* computes
   from its arguments, not how *this specific caller* packs those
   arguments into a bitfield. Both pieces of evidence are needed and they
   come from different sources: primary-source docs for the stock
   algorithm, your own from-scratch disassembly for the project-specific
   packing/calling convention around it.
4. **A minimal from-scratch disassembler is often cheaper than getting a
   real toolchain working in a sandboxed environment with no root/pip/
   docker.** Writing a decoder for exactly the dozen-or-so opcodes a single
   function actually uses (shift/sign-extend/branch/load-immediate) is a
   short, bounded task, and produces ground truth you don't have to trust
   any third party for.

## Why this matters

Treating a decomp project's C source for a stock library call as equally
authoritative to the actual SDK spec risks silently inheriting that
project's own reconstruction quirks (variable naming that obscures the
real per-axis convention, a plausible-looking but not-provably-exact
re-derivation) as if it were verified ground truth. Going to the vendor's
own docs for vendor code, and your own disassembly for project code, keeps
each half of the evidence chain honest about what it can and can't prove.

Confirmed on Parasite Eve II (PSX, `parasite`): this combination (own
disassembly of `Gp_AnimBlendPacked`'s bitfield unpack + Sony's own
`Libref.pdf` for `RotMatrix_gte`'s formula) was the load-bearing evidence
that let a previously-unverified `GpPackedSvec` rotation decode ship as
real, skinned, animated glTF output — confirmed further by a real
multi-frame Playwright visual check across 3 clips.
