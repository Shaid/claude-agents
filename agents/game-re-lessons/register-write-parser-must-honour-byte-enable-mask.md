# GPU command-stream parsers must replace only the byte-enabled lanes of a register write — OR-merging fakes "power-of-256" constants

**When it bites:** you parse a GPU command list / register-write stream (PICA200 on 3DS, or any stream whose write header carries a per-byte enable mask) to recover shader uniforms or vertex attribute setup, and a decoded constant (position scale, UV scale, bias) is right on most meshes but off by an exact power of 256 (or 2^8k) on a minority — tempting a "quantisation mode" or a per-mesh fix-up heuristic.

**The trap:** a parser that accumulates repeated writes to the same register by OR (or by plain overwrite of the whole word) instead of replacing just the masked bytes. Streams routinely write a register more than once and with partial masks; merged wrongly, the float bits of a uniform get mixed and the value moves by byte-sized exponents. A heuristic that "snaps" the result to a box-fit power of two then hides the bug and appears to work.

**Check / fix:**
- Read the command header's byte-enable field (PICA200: header bits 16–19, one bit per byte lane) and apply `reg = (reg & ~laneMask) | (value & laneMask)` per write, in stream order.
- When any constant needs snapping to a power of two to fit, suspect the register-write parser first; re-decode with mask-honouring writes before inventing a mode.
- Confirm a uniform's role from the shader itself (disassemble the shader binary, e.g. 3DS `shbin`) rather than from which register a heuristic likes.
- Score over the whole mesh population: agreement of the decoded constant with an independent fit (bounding box), before and after.

**Canonical example:** Fire Emblem Fates (3DS BCH, `lucina`). The shared seer PICA command reader OR-merged writes; position scale looked like box-fit × 256^k on ~30% of meshes. Honouring the byte-enable mask made scale = VS uniform `c7.x` exactly, agreeing with the box on 97% of 728 int16 meshes.

**History:** 1 instance (lucina, 2026-11).
