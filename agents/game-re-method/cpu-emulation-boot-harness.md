# Emulating a real CPU/hardware pair instead of reimplementing driver behavior — when to switch, and how to build the boot harness

`Read` this when Method §5's basic "run the game's own routine under an
emulator core" call applies at **program-scale**, not just one hostile
decompressor — specifically, when a task is reverse-engineering a
proprietary runtime system (a sound driver, a scripting VM, a physics
engine) VCMD/opcode/mechanism by VCMD/opcode/mechanism, each needing its
own from-scratch disassembly trace to get right, with no natural end (every
new edge case needs a new trace; the format may have dozens more never
even inventoried yet).

## When to make the switch

The tell is architectural, not a specific bug: a from-scratch behavior
reimplementation session finds and fixes one real mechanism per pass
(pitch formula this session, ADSR gating next session, loop-nesting the
session after that...) and each fix is independently valuable but the
total scope never visibly shrinks. If the target system runs on documented,
proven-emulatable hardware (a real CPU + real fixed-function coprocessor,
not a bespoke bytecode VM with no public spec), switching from "reimplement
its behavior" to "execute its real machine code against a real CPU/hardware
emulator" converts the open-ended problem into a **bounded, one-time**
engineering task: get the CPU and hardware emulation right once, and the
*actual* program does 100% correct interpretation of everything —
sequencing, gating, looping, timing-dependent LFOs, whatever — because
it's the literal same code real hardware runs, not a model of it. Confirmed
on FFVI (SNES)'s AKAOSNES V4 sound driver (`ceres` project,
`docs/ffvi/snes/data-structure.md` §19,
`docs/spc700-emulation.md`): after 10+ dispatches individually
reverse-engineering the driver's VCMD-by-VCMD behavior (still finding new
real bugs each pass), a from-scratch SPC700 CPU interpreter + register-
driven S-DSP (ported from a proven reference implementation, not derived
from the opcode spec by hand — same "port from a real emulator core"
discipline Method §5 already establishes for decompressors) let the real
driver take over interpretation duty entirely.

**Don't switch prematurely**: this is a substantial investment (a full CPU
core, unit-tested per-instruction; the target hardware's own register-level
behavior; a boot harness, see below) — worth it only when the behavior-
reimplementation approach has already demonstrated it won't naturally
terminate (several real, distinct mechanism-level bugs found across
multiple sessions is a reasonable bar), and only when the target genuinely
runs on documented, well-understood hardware a reference emulator core
already exists for.

## Porting the CPU/hardware core itself

Same discipline as Method §5's decompressor case: port from a real, proven
reference implementation (a mature open-source emulator's own source, e.g.
blargg's `snes_spc` for SPC700 — the same lineage vendored into
`game_music_emu` and used by countless real players for ~20 years) rather
than deriving instruction/register semantics from a written spec by hand.
Re-express performance-oriented C tricks (packed flag registers, bit-level
shortcuts) as plain, individually-named state for lower transcription risk
— then verify with hand-computed instruction-execution unit tests (fetch/
decode/execute one instruction against a known state, check the exact
result), not by running the port and eyeballing output. Cross-check against
a *second* independent reference implementation (a different emulator
project, same target hardware) for any instruction/register whose behavior
reads ambiguous from the first source alone — real, cheap insurance against
a single-source transcription bug (confirmed catching a real opcode-family
mix-up this way, see `game-re-lessons/INDEX.md` for the specific case).

## The boot harness — the actually hard part

Getting the CPU/hardware core right is necessary but not sufficient — a
harness still has to get the *target program* running in a plausible
initial state without reimplementing everything the harness is trying to
avoid reimplementing. Three techniques, each sourced from a real,
confirmed bug this pattern produces (full detail in each linked pitfall
file — read the one matching your symptom before re-deriving from
scratch):

- **Finding the program's real steady-state entry point** (where it's safe
  to inject a forced call without corrupting mid-computation state): don't
  stop at the first repeated PC (a program's own one-time boot/init code
  almost always contains genuine but *finite* loops a short-lookback
  detector locks onto by mistake) — but frequency sampling alone isn't
  enough either, since a slow-but-bounded real hardware-timing spin-wait
  inside boot code can dominate a frequency histogram exactly as
  convincingly as the real idle loop and produce a *harder-to-notice*
  failure (looks like it's running fine, silently corrupts one piece of
  late-boot state). Measure a real, target-specific warmup floor first,
  then sample frequency only after it. See
  `idle-loop-detection-needs-frequency-not-first-repeat.md`.
- **Bypassing a load-time handshake your harness doesn't want to fully
  emulate** (a cross-chip protocol, a DMA transfer) by placing already-
  correct state directly into emulated memory: check whether the real code
  you're about to let run *also* performs its own address-relocation step
  using data your harness placed (a base/delta computed from a header
  field) — if so, your pre-relocation and its real relocation compose
  additively into silent corruption. Neutralize by feeding its own
  computation an input that makes its correction exactly zero, rather than
  trying to skip the real code. See
  `harness-prerelocation-collides-with-drivers-own-relocation.md`.
- **Placing a resource's real, transitively-reachable content into a
  fixed-size emulated-memory buffer**: don't trust a documented "small
  per-instance" convention to bound real reachability — measure it
  directly; a legitimate one-way jump-chain through a shared data pool can
  span far more than any single instance's own documented footprint, with
  zero decode-desync signal that anything is wrong. See
  `unbounded-transitive-jump-chain-in-fixed-buffer.md` and (if walking
  several independent parallel execution threads sharing one resource
  pool) `shared-lifo-worklist-starves-parallel-thread-priority.md`.
- **A companion coprocessor/MCU sharing the same RAM doesn't need
  emulating just because the boot sequence depends on it once.** If the
  coprocessor's only jobs the main CPU depends on are (a) a one-time
  hardware-configuration step performed *before* the main CPU is released
  from reset (a memory-mapper config, a boot handshake) and (b) writing a
  handful of status/result bytes the main CPU only ever polls, you can
  skip emulating (a) entirely (hard-wire the config you already know is
  live, exactly as if the coprocessor had already run) and skip (b) with
  small, clearly-labeled stub values instead of building a second CPU
  core. Finding which shared-RAM bytes need stubbing is cheap: when the
  harness hangs in a poll loop, an exhaustive whole-ROM/binary scan for
  that address's literal encoding, checked for "100% reads, zero writers
  in the main CPU's own code," is strong evidence the value comes from the
  unemulated coprocessor rather than a bug in your harness. See
  `coprocessor-status-byte-all-reads-no-writes.md`. This turns "build a
  second CPU emulator" into "read a handful of comparison operands out of
  the disassembly" for boards where the coprocessor's role is narrow.

## Validation without the reimplementation-era's usual oracles

A working boot harness often can't be checked against the same "does it
render/decode byte-exact" oracles the rest of this agent's verification bar
leans on — the payoff *is* runtime behavior, which needs its own bar:
bounded/finite/non-NaN output across the full corpus (construction-only
smoke test, cheap), a slower full-render spot-check across a handful of
already-characterized targets (compare peak/duration/finished-vs-not
against whatever the prior behavior-reimplementation approach already
measured — not expecting identical output, but should be reasoned-about-
able), and PC-visit/register-write histograms as a debugging tool in their
own right (a "the real dispatch address is never visited" finding is
itself strong, checkable evidence of exactly where a boot sequence still
diverges from real hardware, the same way a corpus-wide render is evidence
for a decoder).
