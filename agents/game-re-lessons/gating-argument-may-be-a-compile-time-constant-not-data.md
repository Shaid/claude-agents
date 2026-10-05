# A repeatedly-reverified "real, live" mechanism can still be dead code if its own gating argument is never traced back to its origin

**When it bites:** a per-frame/per-object mechanism (a factory, a subsystem
init, a solver) has already been independently re-verified 2+ times —
disassembly citations checked, caller chain confirmed, a live dispatch loop
proven `dt`-gated or otherwise data-driven — and the only remaining open
question treated as "well-posed" is naming its internal fields. Before
trusting "reachable and live" as settled, check whether the function's own
**gating condition** (an `if (argN)`/`cbz`/`cbnz` on one of its call
arguments, not a field read from a resource) has ever been traced back to
where that argument's *value* comes from. A mechanism can pass every
disassembly-level check — real callers, real vtables, real per-frame
dispatch — and still never execute, if the argument feeding its own gate is
a hardcoded literal at every call site.

This is a sharper, cheaper-to-refute case than
`guarded-call-confirmed-called-but-precondition-unreachable.md` (which is
about a *data-dependent* guard that real game data never happens to
satisfy, requiring an exhaustive writer/caller enumeration to prove
unreachability). Here there is no data dependency to enumerate at all: the
guarding register is set by a bare `mov xN, xzr` (or equivalent immediate
load) with no computation behind it, so the branch it feeds is
unconditionally taken or not taken for *every* invocation, full stop.

Confirmed on Fire Emblem: Three Houses (`chimera` project): a native
per-frame NUN-cloth "solver factory" (`main+0x46cc90`) had already survived
three independent re-verification passes (a `re-codebreaker` escalation, a
fresh re-derivation by the dispatching session, and a third from-scratch
script by the orchestrating session) — all confirming the six model-NUN-
pointer checks, the `0x2910`-byte allocation, and the call into the
instance-array builder were real, correctly-disassembled code. A fourth
pass went one level further and found the allocation branch is *also*
gated on a 4th call argument (`x27`), which is set by a literal
`mov x4, xzr` at the factory's one and only call site — confirmed via
`xrefs_to` on the instruction immediately after the `mov` (zero incoming
branches could land there and see a different value) and an exhaustive
4-byte-aligned scan of the whole relocated image for the factory's own
address as a stored pointer (zero hits — no vtable/jump-table entry could
call it any other way either). The identical constant was independently
reproduced in a later game-update build of the same binary. Net effect: the
"real, dt-driven, per-frame solver" from the prior passes turns out to be
compiled-in dead code — every model routes to a small stub object instead,
and the whole multi-thousand-instruction subsystem downstream never runs.
The prior passes' own disassembly citations were all still byte-exact
correct; what they hadn't done was trace the *gating argument itself* back
to its source.

**The generalizable technique**, reusable whenever a subsystem's liveness
matters and its entry point has a call-argument gate:
1. Find every direct caller with `xrefs_to` on the gated function.
2. For each caller, find where the specific argument register is set, and
   confirm with `xrefs_to` that no incoming branch can land between that
   `mov`/load and the call (i.e. the value really is unconditional, not
   just "usually" that way in the one path you disassembled first).
3. If the caller itself is a `bl` target (not a jump table), also check
   whether the *callee's own address* appears anywhere in the binary's data
   segments as a stored pointer (a vtable slot, a function-pointer table) —
   a plain `xrefs_to` only reports direct `bl`/`b` instructions and will
   silently miss an indirect caller that could supply a different,
   non-constant value.
4. Only once all of that comes back "single caller, argument provably
   constant, zero indirect references" is "unreachable" a safe conclusion —
   otherwise you've only shown one path is dead, not the whole mechanism.
