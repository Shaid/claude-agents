---
name: ira-disasm
description: Use when IRA (Interactive ReAssembler) is the right tool for the job — static 68k disassembly, label-based code search, cross-referencing annotated `.asm` files in `docs/`, or reassembling for binary-identical output. Covers IRA CLI usage and output interpretation. Use ONLY when reading, searching, or producing annotated IRA assembly — NOT for interactive analysis (use radare2 for that).
---

# IRA Disassembly for Amiga Binaries

## What is IRA

IRA (Interactive ReAssembler / Aira Force) is a portable MC68000/010/020/030/040/060
reassembler. Located at `~/Downloads/AiraForce-Linux/ira`.

**Key properties:**
- Produces **annotated, re-assemblable** assembly output
- Output can be reassembled with `vasm` to produce identical binaries
- Labels use `LAB_NNNN` format (e.g., `LAB_0A11`)
- Supports 68000/020/030/040/060/851/881/882
- No longer shareware — freeware (contact Frank Wille for bugs)

## Running IRA

```bash
# Basic disassembly
~/Downloads/AiraForce-Linux/ira SOURCE [TARGET]

# Example for WIME
~/Downloads/AiraForce-Linux/ira \
  ~/Development/middilgard/data/wime/amiga/WarInMiddleEarth \
  ~/Development/middilgard/data/wime/amiga/WarInMiddleEarth.asm
```

### Key Options

| Option          | Description                                              |
| --------------- | -------------------------------------------------------- |
| `-a`            | Append address and data to every line                    |
| `-compat=bi`    | Compatibility: BTST bit 8-15 in memory (`b`) + immediate byte MSB 0xFF (`i`) |
| `-config`       | Read an existing `.cnf` (typically hand-edited after a `-preproc` pass) and re-disassemble using it — the refinement-loop flag, see below |
| `-preproc`      | Auto-detect code vs. data on a first pass over an unfamiliar binary; emits a `.cnf` alongside the `.asm` to hand-edit and feed back in via `-config` |
| `-text=<n>`     | Identify ASCII text strings as `DC.B` string literals instead of raw hex bytes (`-text=1`) |
| `-keepzh`       | Keep empty sections in output                            |
| `-binary`       | Treat source as raw binary rather than hunk executable   |
| `-info`         | Print hunk structure information                         |
| `-label=<n>`    | Label style: `0`=LAB_index, `1`=LAB_addr                 |
| `-radix=<n>`    | Number base: `10`=decimal (default), `0`=hex for pos     |
| `-M68000`       | Target CPU (optional — IRA detects from hunk header)     |
| `-oldstyle`     | 68000-style addressing modes                             |
| `-newstyle`     | 68020+ addressing modes                                  |
| `-fixlabels`    | Prepend `L` to labels that would start with a digit      |

### Recommended invocation for WIME

```bash
~/Downloads/AiraForce-Linux/ira -a -compat=bi \
  ~/Development/middilgard/data/wime/amiga/WarInMiddleEarth \
  ~/Development/middilgard/data/wime/amiga/WarInMiddleEarth.asm
```

The `-compat=bi` flag enables:
- `b`: Recognize BTST #n accessing bits 8-15 in memory
- `i`: Recognize immediate byte addressing with MSB 0xFF

## First pass on an unfamiliar binary: the refine-and-repeat loop

IRA can't perfectly separate code from data on a raw binary — it guesses, and
the recommended workflow is an iterative loop, not a single invocation:

1. **Auto-detect pass.** Run with `-preproc` (plus your usual `-a -compat=bi`):
   ```bash
   ~/Downloads/AiraForce-Linux/ira -a -compat=bi -preproc -keepzh Target Target.asm
   ```
   This emits both `Target.asm` and a `Target.cnf` config file.
2. **Spot misclassifications** by reading the `.asm` output:
   - **Code misread as data** shows up as `DC.L`/`DC.W` directives whose hex
     values are recognizable 68k opcodes (e.g. `DC.W $4e75` is a disguised
     `RTS`).
   - **Data misread as code** shows up as implausible instruction sequences —
     runs of `EXT_`-prefixed pseudo-ops, or repeated `ORI #0,...` ($0000)
     decoded from what's actually a run of zero bytes.
   - **Unidentified ASCII text** appears as raw hex byte sequences in the
     printable range ($41–$7A) instead of `DC.B` string literals — rerun with
     `-text=1` to have IRA find these automatically instead of eyeballing.
3. **Fix boundaries and add knowledge in the `.cnf` file, not the `.asm`.**
   The `.asm` gets regenerated every pass, so hand edits there are thrown
   away — the config file is the durable record. Useful directives:
   - `LABEL` — mark a fresh code/data boundary or name a location you've
     identified.
   - `SYMBOL` — rename an existing `LAB_NNNN` to something meaningful once
     you know what it does.
   - `COMMENT` / `BANNER` — annotate a line/region without touching the
     `.asm` source.
4. **Re-run with `-config`** (not `-preproc` — that would throw away your
   edits and re-guess):
   ```bash
   ~/Downloads/AiraForce-Linux/ira -a -compat=bi -config -keepzh Target Target.asm
   ```
5. **Repeat 2–4** as you understand more of the binary — each pass should
   produce cleaner output with fewer misclassified regions. This is why the
   project's committed `.asm` files (see Cross-Referencing below) are worth
   treating as a durable, growing asset: once a binary's `.cnf` is
   well-refined, regenerating the `.asm` from it is a single fast command,
   not a from-scratch effort.

## IRA Output Format

```asm
; Label definitions
LAB_0A11:
    LINK.W  A5,#-8
    CLR.B   -5(A5)
    MOVE.L  SECSTRT_0-12258(A4),-4(A5)
    MOVEQ   #0,D0
    MOVE.B  11(A5),D0
    MOVEQ   #0,D1
    MOVE.B  SECSTRT_0-10909(A4),D1
    JSR     SECSTRT_0-32172(A4)
    ADD.L   #$00000010,D0
    MOVE.B  D0,-6(A5)
```

### Key conventions:

| Pattern | Meaning |
|---------|---------|
| `LAB_NNNN:` | Function/data label (hex address) |
| `SECSTRT_0-N(A4)` | SAS/C small-data relative access |
| `DC.W $XXXX` | Data word (not instruction) |
| `BRA.S`, `BEQ.S` | Short branch (byte displacement) |
| `BRA.W`, `BEQ.W` | Long branch (word displacement) |
| `#nnn` or `#$XXXX` | Immediate value |
| `(A0)`, `0(A0)` | Register indirect / displacement |

## Cross-Referencing

Check the current project's `docs/` for existing annotated IRA output before
disassembling from scratch — the whole point of committing `.asm` files is
to make them a durable, greppable asset (see the refine-and-repeat loop
above). Example from middilgard (your project's filenames will differ):

| File | Game | Lines |
|------|------|-------|
| `WarInMiddleEarth.asm` | WIME | 47K |
| `disassembly.asm` | WIME (capstone) | 40K |
| `vengeance.asm` | Vengeance | 75K |
| `conan-game.asm` | Conan | 23K |

### Finding functions

Substitute your project's actual `.asm` path for `TARGET.asm` below:

```bash
# By label name
grep -n 'LAB_0A11:' docs/TARGET.asm

# By caller
grep -n 'JSR.*LAB_0A11\|BSR.*LAB_0A11' docs/TARGET.asm

# By instruction pattern
grep -n 'LINK.*A5.*-8' docs/TARGET.asm | head -10

# By data reference (example displacement — use your own)
grep -n 'SECSTRT_0-25110.*A0' docs/TARGET.asm
```

## IRA vs Radare2

| Aspect          | IRA                            | Radare2                     |
| --------------- | ------------------------------ | --------------------------- |
| Output          | Annotated assembly             | Disassembly + analysis      |
| Labels          | `LAB_NNNN` (hex)               | Auto-generated              |
| Cross-refs      | grep/ripgrep                   | `axt`/`axf`                 |
| Data detection  | `-preproc` auto-detect + manual `.cnf` refine | Auto-detection (heuristic)  |
| Speed           | Fast (single pass)             | Slower (multi-pass)         |
| Reassembly      | vasm supported                 | Not supported               |
| Binary format   | Amiga hunk native              | Multiple formats            |

**Use IRA when** you have existing annotated output to search or need clean,
re-assemblable assembly. **Use Radare2 when** you need interactive analysis
(stepping, breakpoints), unknown binary format detection, or data
cross-references (`axt`).

## Reassembly with vasm

```bash
# Disassemble
~/Downloads/AiraForce-Linux/ira -a -compat=bi -config -keepzh SOURCE

# Reassemble (requires config file from -config)
vasmm68k_mot -no-opt -Fhunkexe -nosym -o NewBinary SOURCE.asm

# Verify
~/Downloads/AiraForce-Linux/ira -a -compat=bi -config -keepzh NewBinary
diff -s SOURCE.asm NewBinary.asm
```
