# Per-channel/per-voice driver state that's intentionally never reset across resource loads has no real value for a from-scratch cold-boot harness

**When it bites:** a real-hardware CPU/DSP boot-injection renderer correctly
keys voices on (envelope engages, `SRCN`/`PITCH` populate once a
program-change/note establishes them) but produces exactly zero volume —
looks identical to a dispatch/relocation bug, but isn't one.

Some per-channel driver state (channel volume, pan, and similar "current
value" cells a mixdown formula reads as one multiplicand) is deliberately
**not** reset by a "load song"/"load resource" routine, because on real
hardware it's expected to carry over from whatever played immediately
before — composers rely on the *previous* session leaving it in a reasonable
state, and only write it explicitly when they want to change it partway
through a track. A cold-boot-from-nothing harness (the only scenario a
from-scratch renderer can offer) has no "previous resource" to inherit from,
and if the driver's own boot/reset routine only zero-fills a *bounded*
low-memory scratch region (not full RAM), this per-channel state sits outside
that cleared range and silently reads zero — multiplying every other
correctly-computed factor (global/master volume, envelope, etc.) down to
exactly zero output. Confirmed on FFV (SNES)'s AKAOSNES V3 driver: `wChVol`/
`wChPan` are written only by their own explicit VCMD handlers and by a
*different* code path's own explicit default for a sibling resource type
(sound effects got `0x60`, songs got nothing) — never by the per-track
init routine a "load song" call always runs. Voices keyed on and enveloped
correctly for many real ticks with `VOL(L)/VOL(R)` permanently `0x00`.

**Diagnosis technique that found it**: instrument the DSP's own register-write
call to log every write (address + value) across construction and a long
render window, not just watch for `KON`. A register that's *supposed* to
receive a value from a note-on but never does (stays at its harness's own
zero-init default for the whole render) is the tell — cross-reference against
the real disassembly for *every* write site touching that register/cell to
confirm none of them fire under a fresh-boot scenario.

**Fix is inherently an approximation, not a discoverable fact** — there is no
"real" value to find for a from-scratch renderer, only a defensible
substitute (e.g. full volume / center pan, the state a player would expect
after picking any song from a menu). Seed it explicitly as one-time harness
state before the forced call (same category as any other bypassed-handshake
substitute — see the "harness-supplied one-time state" pattern in
`~/.claude/agents/game-re.md`'s method for prior art on citing exactly which
real mechanism is being substituted for), verify the fix empirically (peak
amplitude goes from flat zero to real audio for multiple spot-checked
resources), and document it explicitly as an unconfirmed-value approximation
rather than folding it in silently as if it were traced.
