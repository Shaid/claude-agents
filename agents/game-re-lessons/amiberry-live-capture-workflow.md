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
- **Breakpoint sequencing must be `debug_activate` → `set_breakpoint` →
  `debug_continue`, never `resume_emulation` first.** Calling
  `resume_emulation` before `runtime_debug_activate` on an already-armed
  breakpoint left the emulator running but permanently broke the IPC socket
  (`runtime_ping`/`get_runtime_status`/`runtime_get_cpu_regs` all time out
  afterward) while the underlying process stayed alive per
  `check_process_alive` — unrecoverable without a fresh launch. Even the
  correct sequence can land the reported PC a few instructions past the
  breakpoint address rather than exactly on it; treat that as normal slop,
  not a sign the breakpoint didn't fire.
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
