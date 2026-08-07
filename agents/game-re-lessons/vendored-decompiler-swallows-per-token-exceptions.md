# A vendored decompiler's own internal try/catch can return "successful" output that's actually partial/garbled — a bare try/catch around the call site won't see it

**When it bites:** batch-quantifying a vendored decompiler/parser/exporter
library's success rate across a large corpus ("N/M decoded cleanly"). If
your only failure signal is "did the call throw," don't trust a 100%/0-error
result as proof of clean output without also checking for the library's
*own* internal error handling — many non-trivial decompilers catch
sub-component failures (one bad statement, one bad token, one bad nested
block) internally, log them, and return a best-effort partial string rather
than propagating, precisely so one bad function doesn't abort a whole-file
decompile.

Confirmed on Drakengard 3 (PS3, UE3, `flower` project) using
EliotVU/Unreal-Library (UELib): `ByteCodeDecompiler.cs` wraps ~9 separate
per-token/per-statement decode steps in their own `try/catch`, each calling
`LibServices.LogService.SilentException(exception)` on failure — which by
default just prints to `Console.Error` and returns, letting the enclosing
`.Decompile()` call finish normally and return a string. A bare
`try { text = obj.Decompile(); ok++; } catch { errCount++; }` loop over
~6,750 functions reported 0 errors and 100% success — genuinely true for
"did it throw," but hiding 5 functions whose *output* contained inline
`// Failed to format nests!` comments with an embedded C# stack trace
mid-body, only visible by actually reading a sample of the output text.

**Fix:** if the target library exposes a pluggable logging/error-reporting
interface (as most non-trivial decompilers do, for exactly this
internal-recovery reason), install your own implementation that *counts*
calls instead of the default print-and-continue, and treat "any internal
error fired while processing object X" as a distinct, non-overlapping
failure bucket alongside "threw" and "OK" — not folded into either. This
also turns the library's own recovery mechanism into a free, precise
locator for exactly which corpus items need manual inspection, rather than
grepping output files for a library-specific error-comment string after the
fact.
