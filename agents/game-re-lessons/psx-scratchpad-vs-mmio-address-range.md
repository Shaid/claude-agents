# PSX addresses `0x1f800000`-`0x1f8003ff` are scratchpad RAM, not hardware I/O — only `0x1f801000`+ is real MMIO

**When it bites:** grepping/censusing PSX MIPS code for hardware register
access (a `lui reg,0x1f80` immediate, or any address literal starting
`0x1f80`) as part of deciding whether a piece of code needs real
hardware/device emulation (GPU, SPU, timers, DMA, controller, CD-ROM) —
especially when the hit rate looks implausibly high for the code being
examined (e.g. half of a large corpus of small, otherwise-unrelated
gameplay-logic blobs all "touching hardware").

The PS1's MIPS R3000A has a 1 KB on-chip data-cache-as-RAM region
("scratchpad") mapped at physical/KUSEG `0x1f800000`-`0x1f8003ff` — plain,
fast, general-purpose memory with no side effects, commonly used by game
and SDK code as a scratch buffer for staging function-call arguments,
small temporaries, or stack overflow. It is **not** memory-mapped
hardware. Real hardware registers live in the next 4 KB up:
`0x1f801000`-`0x1f802000`-ish (timers ~`0x1f801100`, DMA ~`0x1f801080`,
interrupt controller ~`0x1f801070`, GPU ~`0x1f801810`/`0x1814`, SPU
~`0x1f801c00`-`0x1f801e80`, controller/memory-card ~`0x1f801040`, CD-ROM
`0x1f801800`-`0x1f801803`). Both regions share the same `0x1f80` upper
16 bits, so a naive `lui reg,0x1f80` scan can't tell them apart without
also checking the low bits of the fully-formed address.

Confirmed on Valkyrie Profile (PSX, `valkyrie`): a scan for
`lui reg,0x1f80` across 655 small AI-behaviour-module blobs found 4,653
hits in 326/655 modules — alarming at first glance. Resolving the full
address (`lui`+immediately-following `addiu`/`ori`) showed every single
hit lands in `0x1f800000`-`0x1f8003ff` (values like `0x1f800300`), used
to stage 1-4 words of call arguments onto the scratchpad before a shared
engine call — a completely mundane, hardware-free convention. A separate
check restricted to the real MMIO range (`0x1f801000`-`0x1f802000`) found
**zero** hits anywhere in the same corpus.

**Fix:** when censusing PSX code for hardware access, always resolve the
full formed address (not just the `lui` immediate) and bucket by range:
`< 0x1f800400` = scratchpad (benign, plain RAM), `>= 0x1f801000` = real
MMIO (needs device emulation if the target is an interpreter, or names a
specific hardware subsystem if the target is understanding game logic).
A `lui reg,0x1f80` hit alone proves nothing either way.
