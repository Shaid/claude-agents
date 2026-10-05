# A background Bash job killed for "low memory" may not reflect real host memory pressure — retry the identical command in the foreground

**When it bites:** a `run_in_background: true` Bash job (a full-corpus asset
pipeline run, a batch decode) is killed with a notification reading
something like *"stopped because the system is running low on memory"* —
especially on a shared/multi-tenant dev machine running several other agent
sessions, browsers, or unrelated processes — and `free -h` immediately
after shows tens of GB still reported "available."

## What happened

Metal Gear Rising: Revengeance (PC, `flower` project): a full-corpus mesh
pipeline run (`buildMetalGearRisingMeshAssets` over the whole corpus — CPK
reads, `DAT\0` bundle parsing, glTF buffer assembly, PNG writes) launched via
`run_in_background: true` was killed by this guard **twice in a row**,
including once before it had even finished its very first, comparatively
light sub-step (building a texture-identifier index). Both times, `free -h`
run immediately afterward reported ~17-20GB "available" and only ~10GB
"used" — nowhere near exhausted, though `Swap:` showed ~25/30GB in use
system-wide (heavy contention from *other* unrelated processes on the
machine: multiple separate agent/codex sessions, several Chrome renderer
processes). Retrying the **identical command** as an ordinary foreground
Bash call (well within its 10-minute timeout ceiling, since the job's real
runtime was ~5.5 minutes) succeeded cleanly on the very next attempt, with
no code change at all.

## Why this isn't the same as `session-scratchpad-tmpfs-exhaustion.md`

That file is about disk space (tmpfs `/tmp`, or the real project volume)
hitting 0 bytes free — a real, `df`-confirmed resource exhaustion that
breaks the Bash tool itself. This is different: RAM appeared genuinely
available by `free`'s own accounting, yet the *background*-job supervision
path still killed the process — consistent with a background-task memory
guard that watches something coarser or more conservative than actual host
`MemAvailable` (e.g. total system memory pressure/swap-in rate across all
processes, not this one job's own RSS), and is more trigger-happy under
transient contention from unrelated concurrent work than the real resource
ceiling would justify.

## Fix

- If a background job dies with a "low memory" kill and `free -h` doesn't
  corroborate real exhaustion, don't assume the job itself is the cause or
  that it needs to be rewritten to use less memory — retry the same command
  once, unmodified, before changing anything.
- Prefer a **plain foreground Bash call** (no `run_in_background`) for the
  retry when the job's expected runtime comfortably fits under the tool's
  timeout ceiling (up to 600,000ms/10 minutes) — foreground execution was
  not subject to the same kill in this case, and a job that already
  completed once at a known wall-clock time (e.g. from an earlier
  successful run, or the pre-fix attempt's own partial log) gives you that
  estimate for free.
- If a genuinely long job (well over 10 minutes) needs the background path
  and keeps getting killed this way, that's a real constraint worth
  reporting rather than silently working around — don't keep blindly
  re-launching the same background job hoping contention clears on its own
  more than once or twice.
- Don't conflate this with `interrupted-transcode-mistaken-for-truncation-
  bug.md` or `background-bash-job-no-push-notification.md`'s self-imposed-
  timeout scenario — here the notification correctly arrived and correctly
  reported the kill; the question is only whether the stated cause (memory)
  matches what `free`/`swap` actually show, not whether the notification
  mechanism itself is trustworthy (it is).
