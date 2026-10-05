# A "does this function ever write byte X" census needs store-width AND caller/callee register-aliasing resolved, not just a literal-offset grep

**When it bites:** claiming a specific stack/struct byte "is always
constant" (or, the opposite error, "must hold real per-call data because no
literal store targets it") from reading one function's disassembly for
stores at that exact byte offset — especially adjacent to a byte that *is*
proven constant/proven written.

**Two compounding traps, both hit in the same real investigation:**

1. **Sub-word stores cover more than one byte silently.** A `strh wzr,
   [sp, #N]` (store halfword) zeroes **both** byte `N` and byte `N+1` — a
   census that only greps for stores whose *literal offset operand* equals
   `N+1` will miss it and wrongly conclude "nothing writes byte `N+1`,
   so if it reads as zero that must be coincidental/meaningful". This
   generalizes to any CPU with sub-word store instructions (`strh`/`strb`
   on ARM, `movw`/`mov [word ptr]` on x86, etc.) — always check for a wider
   store at `N - k` (for each sub-word width the ISA supports) that could
   explain a byte's value before trusting a byte-granular census.

2. **A callee's own register aliasing hides writes from a caller-relative
   offset scan.** When a caller passes a stack address as an argument
   (`add x2, sp, #0xC0; bl callee`), the callee typically copies that
   argument into its own register (`mov x19, x2`) and all of *its* stores
   are then expressed relative to `x19`, not `sp`. A naive "does this
   function write `sp+0x114`" search inside the callee will find nothing,
   because the callee's disassembly never mentions `sp` — the same address
   is there, just under `x19+0x54` (since `sp+0xC0+0x54 == sp+0x114`).
   Resolving this requires walking the callee's own prologue to learn which
   register aliases which caller-relative offset, then converting every
   candidate store's operand back to the caller's frame before comparing.

**Worked example.** Fire Emblem: Three Houses (`chimera` project,
2026-08-26): a `RealtimeRig` producer loop zeroes `sp+0x114`/`sp+0x115`
via one `strh wzr, [sp, #0x114]`, then calls `main+0x6DC70` with
`x2 = sp+0xC0` (aliased inside the callee as `x19`) and `x3 = sp+0x50`
(aliased as an internal `x22`). A byte-offset-literal search inside the
callee for "+0x115" or "+0x54"-relative-to-sp found nothing, tempting the
wrong conclusion that `sp+0x115` was untouched and therefore held "real,
non-constant stack data" (the actual claim made and later corrected). The
correct census: enumerate the callee's OWN stores relative to `x19`
(`+0x8`, `+0xC`, `+0xE`, `+0x54`, `+0x5C` — note `x19+0x54 == sp+0x114`,
confirming the *other* half of the halfword-zeroed pair gets legitimately
overwritten, while `x19+0x55`/`sp+0x115` is never touched by any store in
the function) — which requires first establishing `x19 = sp+0xC0` from the
callee's prologue, not scanning for `sp`-relative literals inside it at
all. Independently re-verifying an escalation's claim by recomputing the
identical offset chain from **both** the caller's sp-relative view and the
callee's register-argument-relative view, and requiring them to agree
numerically, is what caught and confirmed this correctly.

**Practical rule:** before asserting "no store touches byte X" (or its
mirror, "this store proves byte X is dynamic"), (a) check every sub-word
store at `X`, `X-1`, `X-2`, `X-3` (or further back for wider store widths)
for the specific ISA, and (b) if the byte's addressability is described
relative to a different function than the one you're reading, walk that
function's prologue to translate its incoming-argument register aliases
back to the frame you actually care about.
