# H2 callback 0x00221168 — integrated replacement

The C++ candidate replaces the 148-byte original wrapper with 140 bytes at the
original ARM entry. It retains the original 0x00286928 helper, selector and
other callees. The bounded source domain requires ordinary valid RAM and a valid
object at slot +8 when the first getter is zero. Null fault equivalence, general
aliasing, concurrent mutation and indirect interior entries are not established.

`python tools/h2_callback_00221168_package.py` compiled and relocated the candidate,
compared it against original ARM and the H2 base in 64 direct, 64 caller and 64
original-helper caller cases for each image, detected branch (64/64), write
(32/64), stack-argument (64/64), and return (32/64) mutants, checked ARM state and stack alignment at instrumented calls,
scanned aligned words and ARM branches for interior references, and verified IPS
roundtrip. The selector and one helper dependency remain simulated in these
fixtures; these tests do not establish all behavior of those dependencies.

The integrated code image SHA-256 is
`061058c4c7e3ddc548c0166b41d837ab1ee88293c5500853faf79e6737b4e757`.
`python tools/h2_callback_00221168_runtime.py` reran the offline gate and drove
the original and patched images through the same private Azahar scenario: 19/19
state checkpoints and 20/20 observed nested callback events matched. The callback
target was 0x00221168 and raw callback return 0 in those events. Both sides
remained not ready and did not reenter in the same session; physical input and
the complete H2 lifecycle are not proven. See the runtime report and comparison
under `build/h2-callback-00221168/runtime-observed-001/`.

Independent reviews are `h2-callback-candidate-review.md` (run-002),
`h2-callback-package-review.md` and `h2-callback-production-review.md`. The
production TU is `src/engine/leaf_batch30_c.cpp`, ledger classification is
`non_matching`. Its compiled function bytes match the experimental candidate;
all 204 TUs compiled successfully before a subsequent comment-only marker move;
the final production TU was recompiled and its 140-byte body still matches.
Typed aliases use the observed target ABI against legacy untyped assembly
definitions; complete cross-TU C++ type compatibility and LTO are unproven.
The four-control test expansion was run after the runtime trace, but regenerated
the identical image hash above; the trace used the previous runner revision.
