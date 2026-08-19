# Adjacent same-shaped register-cache slots let you ID an unlabeled one by elimination

**When it bites:** an unlabeled per-voice-group bitmask VCMD/opcode pair's
real hardware-register role is unclear, and a cold-boot init routine (or any
single shared setup block) copies that pair's own bitmask cell into ONE byte
alongside one or more sibling bytes you've already independently confirmed
are specific hardware registers.

## What happened

Tracing FFVI's (SNES) AKAOSNES V4 sound driver, three VCMD pairs
(`ECHO_ON`/`OFF`, `NOISE_ON`/`OFF`, `PITCHMOD_ON`/`OFF`) each independently
`OR`/`TCLR1` a bit into their own per-voice-group cell (`$53`/`$54`,
`$55`/`$56`, `$57`/`$58` respectively). A single cold-boot init block then
copies each cell into one of three adjacent bytes in a fixed, identical
pattern: `mov $87,$53 / mov $88,$55 / mov $89,$57`. `ECHO_ON` and `NOISE_ON`
had already been independently traced/confirmed elsewhere to feed the S-DSP's
real `EON`/`NON` registers. Rather than separately tracing where `$89`
eventually gets flushed to the DSP write port, its role was resolved purely
by **elimination**: the SNES S-DSP's own well-documented register map has
`PMON`/`NON`/`EON` at three fixed, adjacent addresses (`$2D`/`$3D`/`$4D`), in
that same order — since `$87`=EON and `$88`=NON were already confirmed, and
the cache-copy block visits the three cells in the identical order the real
registers are numbered, `$89` (the remaining slot) had to be `PMON`. This
was correct, and cheaper than tracing `$89`'s own downstream flush site.

## The technique, generalized

When N structurally-parallel bitmask-cache slots are set up in the same
init block in the same relative order, and you've confirmed M<N of them
against a platform's own known, ordered, small register set (any sound/
graphics coprocessor with a handful of adjacent per-channel enable-bit
registers — S-DSP, PSG channel-enable registers, GPU layer-enable bits,
etc.), the remaining N-M slots can often be assigned by matching the
init block's *visitation order* against the register map's *address
order*, without independently tracing each one's own consumer. This is not
proof on its own for N-M>1 (order alone doesn't disambiguate more than one
unknown against more than one candidate) — but for the common N-M=1 case
it's a clean, decisive shortcut. Still worth a final sanity check: does the
identified register's real documented *behavior* (e.g. "modulates pitch
from the preceding voice," not just "some bitmask") match what the VCMD
pair's *name* suggests? (Confirmed here: `PITCHMOD_ON`/`OFF` naming exactly
matches PMON's real function.)
