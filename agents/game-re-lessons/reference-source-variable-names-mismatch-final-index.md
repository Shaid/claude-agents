# A confirmed C reference's own local variable names can mismatch the array slots they're finally written to — transcribe by destination index, not by variable name

**When it bites:** porting a math formula (matrix rotation, vector
transform, any multi-component calculation) from a game's own confirmed,
already-cross-validated C source, where the source computes several
scalars into intermediate variables (`dx`, `dy`, `dz` or similar) and then
assigns them into an array/struct a few lines later.

## What went wrong

Frontier: Elite II's `Matrix3x3i16RotateAxis` (from `watsonmw/fe2-intro`,
already confirmed as a byte-exact ground-truth source for this game's
whole 3D format) computes a rotated matrix row like this:

```c
dx = (((z2 * cosine) - (z1 * sine)) >> 15);
dy = (((y2 * cosine) - (y1 * sine)) >> 15);
dz = (((x2 * cosine) - (x1 * sine)) >> 15);

matrix[row2][2] = (i16)dx;
matrix[row2][1] = (i16)dy;
matrix[row2][0] = (i16)dz;
```

A direct transcription that assumes `dx`/`dy`/`dz` land in slots
`[0]`/`[1]`/`[2]` respectively (matching every OTHER formula in the same
file, and matching the variable names' own obvious x/y/z suggestion)
produces `out[row2] = [dx, dy, dz]` — i.e. `[z2·c−z1·s, y2·c−y1·s,
z2·c−z1·s]` written into `[x, y, z]` slots. This is wrong: the C source's
own assignment reverses x and z (`dx`→slot 2, `dz`→slot 0), a
naming/assignment mismatch baked into the *original game's own source*
(not a typo in it — the sibling `row1` block a few lines earlier assigns
`matrix[row1][0..2] = dx,dy,dz` in the "obvious" order, making the row2
block's reversal easy to miss on a skim). The bug silently corrupted every
rotation with a static angle, and none of the pipeline's own numeric
checks caught it — they verified instruction-level field *decode*
(byte-exact vs. an oracle) and gross output scale (bounding boxes), but
nothing independently checked rotation *direction/axis assignment*. It was
only caught by a dedicated code-review pass reading the transcription
against the source line-by-line.

## The fix / general principle

When porting a formula from reference C source, **trace each output
variable to its literal destination index in the following
assignment statements — never assume slot order matches variable-name
order, even when every sibling formula in the same file follows the
"obvious" naming convention.** This is the sibling lesson to
`packed-bitfield-prose-order-vs-real-lsb-first-packing.md` and
`self-relative-offset-needs-cpp-arithmetic-not-prose.md` (both about not
trusting an author's prose/comment ordering over real bit/byte
arithmetic) — here the trap is trusting an author's *variable naming*
ordering over the real, explicit index assignment a few lines below it.
A numeric oracle that only checks decode correctness and gross scale will
not catch an axis-swap bug; if a live/rendered ground truth is available,
specifically check rotation direction and axis, not just magnitude.
