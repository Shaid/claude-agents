# Hand-deriving a 65816 address from a ca65 disassembly's local-label suffix, then predicting later addresses by summing assumed opcode widths, breaks silently on M/X-flag-sensitive immediates

**When it bites:** reading a committed source-level 65816 disassembly (ca65
`.asm` output, e.g. `everything8215/ff6` and its siblings) that uses
per-routine local labels like `@d064:` where the hex suffix is meant to
equal the low 16 bits of the label's real CPU address, and you're computing
a *different*, unlabeled instruction's address by summing the byte-widths
of the instructions between it and a known-good labeled anchor.

The trap: `LDA #imm`/`LDX #imm`/`LDY #imm`/`AND #imm`/`CMP #imm`/etc. are 2
bytes in 8-bit accumulator/index mode (M=1/X=1) but 3 bytes in 16-bit mode
— and which mode is live at any given point depends on the nearest
preceding `REP`/`SEP #$xx` somewhere upstream in the function, which a
linear prose read doesn't surface without tracing every mode switch back
through the routine. Confirmed on FFVI (SNES): hand-deriving addresses this
way worked perfectly for several call sites (fixed-width `JSR`/opcode
sequences aren't M/X-sensitive) but silently produced addresses off by 1-3
bytes for three sibling opcode handlers in the same file
(`AnimCmd_80_40`/`_41`/`_42`, the battle engine's Mode-7 zoom/flip/screen-
mode script commands) whose bodies do contain accumulator-width-sensitive
immediates — the error wasn't obvious until a predicted `JMP` target
operand landed on an implausible address instead of the expected label.

This is the same underlying root cause as
`r2-snes-flag-width-blind.md` (unknown M/X flag state at a given point in
the code) but a different failure mode: that lesson is about an
*automated* linear disassembler mis-decoding instruction boundaries;
this one is about a *human* trusting a source disassembly's local-label
naming convention as a stand-in for real addresses and then doing manual
arithmetic on top of it, which fails even when every individual
instruction in the source is disassembled correctly by its own author.

**Fix:** don't predict an unlabeled instruction's address by summing
assumed opcode widths at all. Instead, do an address-agnostic raw
byte-pattern scan of the containing bank (or the whole ROM, if bank
placement isn't independently known) for the instruction's actual opcode
bytes — e.g. scan for `STA.l $00211A` (`8F 1A 21 00`) rather than computing
"the STA must be at $C1D064 because the three instructions before it sum
to N bytes." This sidesteps M/X-flag tracking entirely (it doesn't need to
know instruction boundaries in advance) and comes with a free
cross-check: an exact, provable hit count across the scanned region (e.g.
"exactly 1 hit" for a register write assumed unique, or "exactly 6 hits"
matching a disassembly's declared list of call sites) that independently
validates the source disassembly's completeness, not just one instruction
in isolation.
