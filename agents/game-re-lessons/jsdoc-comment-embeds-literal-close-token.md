# A literal `*/` inside prose (a glob-like path) silently closes a `/** */` doc comment early

**When it bites:** writing a JSDoc/block comment whose prose mentions a
directory glob or wildcard path containing a literal asterisk immediately
followed by a slash (`tools/*/build-x.ts`, `src/*/index.ts`, any
"one-per-thing" path pattern) — and `tsc`/a bundler then reports a large,
confusing cascade of syntax errors that don't obviously point back to the
comment at all.

Not game-RE-specific — a plain TypeScript/JavaScript authoring trap, but
one this agent will keep hitting because doc comments routinely narrate
"see `tools/<game>/build-x.ts`" via glob shorthand instead of a concrete
example path.

**What happened:** a module doc comment read `... (`tools/*/build-dungeons.ts`) ...`
inside a `/** ... */` block. The literal substring `*/` inside
`tools/*/build-dungeons.ts` closed the block comment three lines into the
file, at that exact point mid-sentence. Every token after it — the rest of
that JSDoc prose, then all the real code below — was parsed as actual
TypeScript. `npx tsc --noEmit` produced ~150 errors spanning the *entire*
file, with confusing, unrelated-looking messages (`Module declaration
names may only use ' or " quoted strings`, `Unterminated regular
expression literal`, `'const' is a reserved word that cannot be used
here`) clustered many lines *after* the real cause, because the tokenizer
was desynced from that point on and kept reinterpreting later real code in
increasingly wrong ways. Nothing in the error list mentioned line 3 or
comments at all.

**The diagnosis, once found, was fast:** `grep -n '\*/' file.ts` — any
comment line containing `*/` *before* the doc comment's real closing `*/`
is the culprit. In this case the real closer was on line 14; the false one
was on line 3, inside a code-span-quoted glob path.

**The fix:** never write a literal `*/` inside a block comment's prose.
Rephrase the glob away (`each game's own build-x.ts`, `tools/<game>/build-x.ts`
with an explicit placeholder, or drop the trailing `/x.ts` and just say
"per game") rather than literally spelling `dir/*/file.ts`.

**The generalizable habit:** when `tsc`/lint output on a file is a large,
incoherent cascade of errors that don't individually make sense — especially
one starting a few lines into the file and including "unterminated
string/template" or "unexpected keyword" errors deep in otherwise-normal
code — suspect a prematurely-closed comment or string before reading the
error list line-by-line. `grep -n '\*/'` (for `/** */` comments) or a
quick scan for stray quote/backtick characters is a five-second check that
finds the true error site directly, instead of manually reasoning through
dozens of downstream, misleading parser complaints.
