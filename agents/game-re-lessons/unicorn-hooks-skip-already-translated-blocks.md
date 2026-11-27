# Unicorn caches translated blocks: hooks added (or code patched) after a block ran are not applied to it

**When it bites:** a Unicorn single-routine harness disagrees with a port that looks correct, or a read/write footprint is missing accesses — only for code that a setup step already executed (a setup that calls game init routines, an earlier vector run in the same `Uc` instance), or after code bytes were patched or an overlay hunk was swapped in.

Unicorn (QEMU TCG) translates each basic block once and reuses the translation. Memory/code hooks are compiled into the block when it is translated, so a hook registered *after* a block was translated does not fire for it, and the footprint silently loses those reads and writes. The result looks like a port bug or a missing field, not like a harness fault.

**Check / fix:**
1. Call `uc.ctl_flush_tb()` (Unicorn 2) after any setup that ran game code and before starting the recorded run; guard it with `try` for older bindings.
2. Register hooks before the first emulation in a fresh instance where possible.
3. Also flush after host-side writes to code memory (stub patches, overlay swaps, self-modifying setup) — cheap insurance whatever the binding version does.
4. Sanity check: the same vector must give the same footprint in a fresh `Uc` instance and in a reused one.

**Canonical example:** crawl MM2 rules pass 5e (Hall of Training eligibility via a mid-function entry on a fake frame): the setup ran game code, so the read/write hooks added afterwards were skipped for those blocks until `tools/mm2/rules_oracle/harness.py` flushed translated blocks after setup.

**History:** 1 recorded instance (crawl MM2, 2026-11).
