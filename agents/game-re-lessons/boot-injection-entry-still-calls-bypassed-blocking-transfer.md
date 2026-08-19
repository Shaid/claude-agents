# A boot harness's chosen injection point may itself call the same blocking port-protocol routine the harness exists to bypass

**When it bites:** building a CPU-emulation boot harness that force-calls a
real driver's "load resource" entry point (found via disassembly or a sibling
game's already-confirmed equivalent address) to avoid reimplementing a
cross-chip/main-CPU handshake — especially when porting the *technique* from
one game to a sibling game in the same driver family, where the sibling's own
entry point happened not to need this.

A driver's real "load song"/"load resource" routine is not guaranteed to have
the same internal shape across sibling games in the same engine family, even
when the overall boot-injection *technique* transfers cleanly. One game's
entry point may do its own byte-transfer work internally (call the same
generic port-protocol/DMA-wait routine the bypassed main-CPU handshake uses)
before reaching the part that actually matters to a single-song renderer —
while a sibling game's equivalent entry point does no such thing, because that
work happens entirely *before* it's reached. Confirmed on FFV (SNES)'s
AKAOSNES V3 `PlaySong` routine: unlike FFVI's own `$0A92` (no port-protocol
work of its own — safe to force-call directly), FFV's `PlaySong` releases all
voices, waits ~8ms, then calls the *same* generic `TfrData` byte-transfer
routine the bypassed handshake itself uses — force-calling `PlaySong`'s own
stated entry hangs forever inside `TfrData`'s own blocking wait loop (`CMP
X,hPort0; BEQ`), since no real main CPU is emulated to drive the other end of
the protocol.

**Don't assume the entry-point-finding result generalizes just because the
overall harness architecture does.** Trace forward a short way from any
candidate injection point (live single-step, or read the target's own
disassembly if available) specifically looking for a call into the same
generic transfer/wait primitive the bypassed handshake used elsewhere — if
found, the real injection point is **after that call returns**, not at the
routine's own stated start. Reproduce everything the bypassed call would have
transferred by placing it directly into emulated memory yourself (the
harness's own precomputed-placement pass standing in for the real transfer,
same principle as `harness-prerelocation-collides-with-drivers-own-relocation.md`),
then resume force-calling from the instruction immediately following the
skipped call. A related, cheaper symptom to watch for once this is fixed: a
resource-load entry point may also re-run a large buffer-clear/init routine
(not just per-track setup) as part of its own real work — size any
force-call settle-cycle budget generously enough to include it, don't just
carry over a sibling game's own smaller budget unchanged.
