# Amiberry live-capture workflow gotchas

**When it bites:** about to drive a *running* amiberry instance over IPC to
capture data — sending keys to navigate a menu, setting a breakpoint, or
reading many memory values in sequence.

Four things cost real time (Carrier Command, hunter project):

- **`send_key` timing is bimodal, not linear.** A `press_and_release` call
  (near-zero hold) can fail to register at all with some Amiga
  frontends/menus. A `press` + explicit sleep (~0.05-0.2s) + `release` DOES
  register — but as **many rapid auto-repeats** (a 0.2s hold scrolled an
  entire 16-item menu end-to-end). There's no clean single-step tap between
  these two regimes worth hunting for. Exploit the overshoot instead of
  fighting it: a full-length repeat run reliably lands on a list boundary
  (top or bottom), so drive to a boundary on purpose, then take one more
  non-instant tap from there.
- **Never call `resume_emulation` at all while any breakpoint is armed —
  it's not an ordering issue, the combination itself is fatal.** The
  original version of this lesson framed the fix as "sequence
  `debug_activate` → `set_breakpoint` → `debug_continue`, never
  `resume_emulation` first," implying `resume_emulation` was safe *after*
  `debug_activate`/`set_breakpoint`. A later session (Wings, hunter project)
  reproduced the IPC-killing failure a second time **using exactly that
  "safe" order** (`debug_activate` → `set_breakpoint` → `resume_emulation`)
  — the socket died identically (`runtime_ping`/`get_runtime_status`/
  `runtime_debug_status` all time out, `check_process_alive` still reports
  the process running) — unrecoverable without `kill_amiberry` + a fresh
  launch. The real rule: **once a breakpoint exists, only ever use
  `debug_continue` to resume execution, never `resume_emulation`, in any
  order.** Separately, `debug_continue` itself is not a reliable "run until
  breakpoint hit" primitive: repeated calls can leave every register
  byte-for-byte unchanged (no progress at all), and the debugger's own
  `active`/`debugging` status flag was observed reverting to `0` after
  almost every call regardless of whether execution advanced, requiring a
  fresh `debug_activate` before each subsequent attempt. This was
  particularly bad when resuming a paused-and-loaded WHDLoad/OSEmu `.uss`
  savestate whose captured PC sits inside an interrupt-service wait loop
  (a real, independently-confirmed condition for interactively-triggered
  saves — see this file's `.uss`-chunk-format note and
  `game-re-tooling/amiga.md`'s savestate section): the pause flag likely
  freezes hardware-interrupt generation along with CPU scheduling, so a
  wait-for-interrupt loop cannot exit via `debug_continue` alone no matter
  how many times it's called, but the one call that *would* deliver the
  interrupt (`resume_emulation`) is exactly the one that kills the IPC
  socket once a breakpoint is set. Net effect: with the current amiberry
  MCP server, there is no known working sequence that both (a) lets
  execution progress past an interrupt-wait loop and (b) keeps a
  breakpoint live and the IPC socket intact — treat "breakpoint a
  per-frame hot routine in a freshly-loaded interactive savestate" as
  currently unsupported, verify by another technique (direct
  `runtime_read_memory` of already-confirmed globals while paused is often
  enough — see Wings' `docs/explore/Wings/data-structure.md` §"Dogfight
  screen composition" §8 for a worked example), and escalate/report the
  gap rather than burning many calls chasing it further. Even when a
  breakpoint genuinely does fire, the reported PC can land a few
  instructions past the breakpoint address rather than exactly on it;
  treat that as normal slop, not a sign the breakpoint didn't fire.
  `runtime_clear_breakpoint(address="ALL")` also silently fails in the
  current build ("Failed to clear breakpoint.") — clear by the specific
  hex address instead, which works immediately.
- **Loading a specific `.uss` moment into a live instance needs the
  display pipeline actively ticking, not just a `load_state` call.**
  Calling `runtime_load_state` while the emulator is paused (including a
  freshly-launched process that has never once been resumed) reliably
  produces a **black screenshot** — the load appears to need at least one
  real frame to tick through before newly-loaded chip RAM/copper state
  shows up on screen. Conversely, calling `runtime_load_state` while
  running and *not* pausing again quickly enough lets the loaded
  WHDLoad/OSEmu interrupt-service state that owns the captured instant
  keep running in real time — confirmed carrying a mid-dogfight capture
  all the way to a post-mission results screen before a later
  `pause_emulation` call caught up (independently corroborated by a human
  watching the actual emulator window mid-session). Working recipe:
  `resume_emulation` → brief real-time settle (~0.3-0.5s) →
  `runtime_load_state` → `pause_emulation` → `runtime_screenshot`/reads.
  Confirm the load actually landed on the intended moment via screenshot
  content before trusting any subsequent register/memory read.
- **Pause before bulk-reading.** `runtime_read_memory` only reads 1/2/4
  bytes per call, so capturing a whole buffer takes dozens of sequential
  round trips. If the target is mid-animation (e.g. a rotating title-screen
  model), reads taken over several real-time seconds will land on different
  frames and produce an internally-inconsistent composite. Call
  `pause_emulation` first, confirm it's actually frozen (two consecutive
  screenshots come out pixel-identical), then do all the reads.
- **Don't try to reverse-engineer the `.uss` savestate chunk format as a
  bulk-memory-dump shortcut.** It has an `ASF ` magic and name+length chunk
  headers, but the exact boundary formula (per-chunk compression/padding)
  doesn't fall out from a quick scan — one attempt got a length formula that
  worked for one chunk pair and broke on the very next. Cracking it is its
  own side-quest; just do the individual `runtime_read_memory` calls unless
  someone has already solved the chunk format.

Related but separate insight for interpreting what you capture: if a
pointer global resolves to an address **outside** the static file's mapped
range, that's a strong signal it's a runtime-allocated scratch buffer
(refilled every frame by animation/transform code), not the original static
data table. Decode it anyway — it's genuine verified geometry/data for that
one frame/instance — but document the distinction; don't present it as a
byte-exact copy of the static on-disk stream.
