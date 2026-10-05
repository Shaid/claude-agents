# `erasableSyntaxOnly` tsconfig rejects TS constructor parameter-property shorthand (TS1294)

**When it bites:** writing a new TS class in a seer-framework project (these
all run `.ts` directly via `npx tsx`, no build step) and `npx tsc --noEmit`
fails with `error TS1294: This syntax is not allowed when
'erasableSyntaxOnly' is enabled` pointing at a constructor parameter.

Several of these projects' `tsconfig.json` sets `erasableSyntaxOnly: true`
(needed for Node's/tsx's native type-stripping to run `.ts` files without a
transpile step — the compiler option name is literal: only syntax that
type-*stripping* alone can erase is allowed). TypeScript's constructor
**parameter-property shorthand** —

```ts
class Foo {
  constructor(private buf: Uint8Array, private at: Cursor) { ... }
}
```

— is convenient sugar for declaring-and-assigning a field in one step, but
it is not erasable: a real assignment statement has to be *synthesized* at
each call, which is compilation, not stripping. It fails under this option
even though it looks like ordinary, modern TypeScript.

## The fix

Write the field declaration and the constructor assignment separately —
purely mechanical, no behavior change:

```ts
class Foo {
  private buf: Uint8Array;
  private at: Cursor;
  constructor(buf: Uint8Array, at: Cursor) {
    this.buf = buf;
    this.at = at;
  }
}
```

Confirmed on Bard's Tale's (Amiga, `crawl`) Huffman bit-reader class
(`tools/shared/bardstale-codecs.ts`). Worth checking for on any brand-new
`.ts` file in one of these projects before running the final `tsc`
check — it's an easy, purely-mechanical fix once spotted, but the error
message doesn't explain *why* the syntax is rejected, which can send you
looking in the wrong place (a `tsconfig` bug, a stale `tsc` version)
instead of at the one line it's actually pointing to.
