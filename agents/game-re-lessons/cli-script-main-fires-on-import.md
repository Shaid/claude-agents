# A decode-script's unconditional `main()` fires as an import side effect

**When it bites:** importing a constant or helper function from another
`decode-*.ts`-style CLI script (to share a palette, a parsed-format
struct, or similar), and seeing confusing double output, a wrong
`Usage: ...` error, or `process.exit()` unexpectedly killing a test run.

Seer-framework pipeline scripts commonly follow a "library logic + CLI
`main()` in one file, called unconditionally at module scope" pattern —
convenient for a single throwaway extractor, but it means the file has an
**import side effect**: pulling in one of its exports (a constant, a
parser function) for reuse in a sibling script or a test also executes
its `main()`, which reads `process.argv` meant for the *importing*
script's own invocation (or the test runner's), and can call
`process.exit()` mid-test-run. This is easy to trip when consolidating
several platform-variant decode scripts that need to share one constant
(e.g. a palette) defined alongside another script's CLI entry point — the
natural refactor ("just import it from there") silently breaks both
sides.

Two-part fix: (1) if a value genuinely belongs to a decode format rather
than to one script's CLI, give it its own small module with no `main()`
at all (cheapest, and the more idiomatic seer split — see how `pic-
format.ts`/`decode-pic.ts` already separate format logic from the CLI
elsewhere in this same corpus); (2) for a script whose *exported
functions* (not just constants) genuinely need to be both CLI-runnable
and importable (e.g. by its own test file), guard the trailing call:

```ts
if (process.argv[1] && import.meta.url === `file://${process.argv[1]}`) {
  main();
}
```

instead of a bare `main();`. Verified this doesn't change CLI behavior
(still runs identically via `npx tsx script.ts ...`) while eliminating
the import-time side effect, confirmed via a full regression pass
(MD5-identical output before/after across every existing generated
asset).
