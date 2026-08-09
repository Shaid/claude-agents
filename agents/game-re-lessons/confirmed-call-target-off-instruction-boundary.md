# A confirmed JSR/BSR target that doesn't land on an instruction boundary is real evidence — but check the load base with a random-baseline test before chasing a per-routine explanation

**When it bites:** you've byte-exact-verified a call site's target address
(hexdumped the actual opcode bytes, not trusted a disassembler's rendering),
but linear disassembly of the target function — walked forward from the
nearest independently-confirmed neighboring code — places that address
partway through a multi-byte instruction rather than on a clean boundary.
Also fires *before* you conclude a load base / relocation offset is correct
because a handful of hand-picked call targets disassembled as clean,
sensible code.

The natural instinct is to assume the disassembler mis-synced and either
(a) silently start decoding a few bytes early/late to "make it work," or
(b) distrust the call-site verification instead, or (c) chase a per-routine
explanation (self-modifying code, an alternate entry point, decompressor
corruption). All three are legitimate checks — but if 2+ distinct targets
in the *same file* show the same symptom, stop chasing individual routines
and check the load base itself first, using the random-baseline test below.
It's cheaper and it's the more common root cause.

**Corrected history (2026-08-07).** This lesson originally documented two
JSR targets in Hunter (Atari ST) file `100`'s decompressed executable
(`$DC3E`, `$E81A`) that were byte-exact confirmed at their call sites but
landed mid-instruction under linear disassembly, cross-checked with two
independent disassemblers and a from-scratch decompressor re-run — and left
open as "a genuine anomaly." A later `re-codebreaker` escalation found the
real cause: **the assumed load base (`file_offset == memory_address`, i.e.
base 0) was wrong by exactly `$100`.** Worse, file `100` turned out not to
be Hunter's executable at all — it's a *different game* (Cybercon III)
copied onto the same cracked multi-game compilation disk, confirmed by
credits-block strings (`C Y B E R C O N   I I I`, developer/publisher
names, copyright line) sitting in the decompressed payload. Hunter's real
Atari ST executable was a separate file (`800`) the whole time.

**Why "5-6 known-good targets all disassemble cleanly" was worthless
evidence for the base.** On 68000, an arbitrary even address lands on an
instruction boundary roughly **two-thirds of the time by chance** (mean
instruction length ≈ 3 bytes). Measured directly on the file in question:
400 random even addresses → 62.7% "clean"; the same 58 real JSR/JMP targets
deliberately displaced by ±4-8 bytes → 65.2%; the 58 real targets at the
(wrong) base-0 model → 67.2%. All three numbers are statistically the same.
"I picked several call targets and they all disassembled as sensible code"
is the *expected* outcome of a wrong base, not evidence for a right one —
it only becomes evidence once measured as a **ratio against this same
file's own random baseline**, over the **whole** target set, not a
hand-picked handful. This generalizes past 68k/Atari ST to any CISC ISA
with variable-length instructions and dense opcode space (x86, 68k) — a
fixed-width ISA (MIPS, SH-2, ARM in one mode) doesn't have this failure
mode at all, since every address is trivially "on a boundary."

**The decisive test.** Two independent measurements, both required:
1. **PC-relative branch targets are base-independent.** If these decode
   coherently across thousands of instances (98.7% in this case, over
   3,528 branches), the *decompressed bytes themselves* are correct —
   this rules out decompressor corruption as the explanation, separately
   from the base question.
2. **Absolute `JSR`/`JMP .L` targets depend on the base.** Scan a wide
   range of candidate bases (here ±`$8000`...`$14000` was enough) and, at
   each candidate, compute what fraction of *every* distinct absolute
   target lands on an instruction boundary — restricted, if possible, to
   targets whose call sites are unambiguously code (e.g. reached only via
   a `beq`/`bne` guard from already-confirmed code, not a raw byte-pattern
   scan that could hit data). Compare against the random baseline for that
   *same file*. The correct base is the one that jumps to ~100% while every
   other candidate — including the "obviously right" one built from a
   handful of clean-looking targets — sits within noise of the baseline.
   An independent structural check (a stack-pointer `lea` at the entry
   point landing on exactly the image's own last byte, zero deviation) is
   a strong secondary confirmation when available.

**Fix — the full verification sequence, base check first:**
1. Before trusting *any* individual "this call target looks clean at this
   base" observation, run the random-baseline ratio test above across the
   whole target set. If it's inconclusive or the file has stopped making
   sense structurally (subsystems that don't fit the target game, strings
   that don't match), also grep decompressed/decrypted payloads for
   credits-block strings (company name, "programmed by", copyright line) —
   on a multi-game compilation disk, a file catalogued as "the target
   game's executable" can belong to a different game entirely.
2. Only once the base is confirmed by the ratio test, treat a remaining
   individual alignment anomaly as a real per-routine question: hexdump the
   call site's raw opcode bytes yourself, disassemble the target with a
   **second, independent** tool/library, and if the payload came from a
   decompressed/decrypted intermediate, re-derive it from scratch and diff
   against what you were using (rules out a stale/corrupt cache).
3. If the anomaly survives all of the above at the *confirmed* base, it's
   a genuine open question — self-modifying/runtime-patched code, or an
   alternate entry point valid only under a specific register-state
   precondition. For the latter: two independent linear disassemblies that
   disagree on how to parse an overlapping byte range but **reconverge
   byte-exactly on the same later instruction address** is real positive
   evidence for a genuine hand-optimized "alternate entry point sharing a
   tail" idiom, not proof that one decode is simply wrong — confirmed on
   this same file's `$DC3E` (before the base-0 finding voided the specific
   routine analysis): a fresh disassembly starting exactly at the
   anomalous target decoded as different-length instructions than the
   "main" entry path, but both converged on the identical next instruction
   a few bytes later.
