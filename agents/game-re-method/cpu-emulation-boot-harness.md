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

## Differential whole-frame oracle for a static recompile

Once a per-frame unit has been statically recompiled (state handler → object update → pool loops → type routines → placement walker → callbacks), verify the *frame*, not routines, against the emulator core running the original code:

- Filter dispatch/pool-type tables to the types the scenario reaches; anything else throws "no label at". Grow coverage by discovery: run the port alone and let each missing label name the next dispatch target (one at a time, or automated).
- Hook only genuinely out-of-scope services (players, camera, sprite build, HUD, `trap` calls) on **both** sides; log each hooked call with its entry registers.
- Compare after **every** frame: full RAM, registers + CCR, the ordered service log, writes outside RAM, unmapped-read count. Carry the port's RAM into the next frame. Script the services' effects (camera/player positions) into both RAMs identically between frames.
- Scripted inputs must be accepted by the oracle: an injected hit that sets fewer fields than the real player routine would can make the ROM itself loop. Discard those, count accepted/rejected, and label it.
- Null controls: perturb only the **port's** copy (RNG, player count, camera, a flag) and require a mismatch at a specific first frame.
- In walker-only sweeps, clear/refill ("consume") pools each frame so allocations keep succeeding.
- Test runner plumbing: split files so none runs ~60 s synchronously (vitest's worker RPC times out with an "Unhandled error" though every test passed), and expose the oracle session via a getter, since it is created in `beforeAll`.

Worked example: kolbold `ddsom` (CPS2, 68000 → TypeScript, Musashi oracle): 28,000 consecutive frames in ~35 s. This run found a jump-table truncation that weeks of per-routine random-state tests missed (`jump-table-end-at-lowest-target-truncates-shared-handler-tables.md`).

## Single-routine rules harness (deriving game rules, not booting the game)

The opposite grain to a boot harness: load the executable (plus any overlay hunks) into a CPU core, build synthetic memory/registers, run **one** routine (entry + sentinel return address, or a mid-function entry on a fake stack frame with stop addresses), and diff it against a hand-written port. This is how game *rules* (RNG, combat rolls, spell handlers, level-up, shops) get verified when no reference source exists.

1. **Strict read/write-footprint parity, not output equality.** Record every byte the routine reads and writes, the RNG state and draw order, and every stubbed call (arguments + return value). Run the port on *only* the recorded read bytes; an extra read, a different RNG draw order or a different write set is a failure. Output equality alone passes ports that read the wrong field and happen to agree on the vectors.
2. **Stubbed callees are part of the footprint.** Stub UI/IO/side-effect callees, but record their argument reads and the writes they stand in for, or parity is blind to them. Overlay call stubs can be patched to `JMP abs.l` into the loaded hunk.
3. **Every unit needs a null control** — a deliberately wrong port variant (drop a mode gate, `+100` instead of `+120`) that must disagree on at least one vector. A unit whose null control never fails is not verified; the vectors don't exercise it.
4. **Vectors:** random + boundary mutation of exactly the state bytes the footprint says matter. Commit a small subset (< 1 MB), keep full sets gitignored and generated by a script, and make sure the tests also pass with the full set absent.
5. **Grade every rule** `harness` / `code` (read, not run) / `hyp` / `open`, and record corrections dated in place. Harness runs repeatedly overturn earlier hand-read claims (swapped HP/SP labels, a feature written up as absent that existed).
6. **Footprints as negative evidence:** once every unit of a pipeline is harnessed, "no unit ever reads field X across all vectors" strengthens a static "feature X is absent" census — grade it `code+footprint`, never "proven absent" (`negative-from-addressing-root-not-shapes.md`).

Harness pitfalls: `unicorn-hooks-skip-already-translated-blocks.md` (Unicorn), `low-handler-coverage-suspect-harness-before-game-gates.md` (coverage censuses), `generated-artefacts-from-game-code-carry-retail-text.md` (what you commit).

Worked example: crawl (`~/Development/crawl`) rules passes for Black Crypt (musashi), Wizardry 6, MM1 (8086), MM2 and MM3 (Unicorn 68k): ~25 passes, > 1M vectors; MM2 alone ~200k vectors over all 96 spell handlers. Every pass corrected at least one earlier hand-read claim. Method docs: each title's `docs/<game>/<platform>/game-rules.md` status block; harnesses under `tools/<game>/rules_oracle/` or `tools/wizardry6/oracle/`.
