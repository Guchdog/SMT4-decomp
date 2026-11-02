# `0x00254CA8` offline integration — run005

## Result

The C++ service was patched in place at `0x00254CA8`. The relocated candidate is 640 bytes in the original 840-byte slot, with 18 `R_ARM_CALL` relocations to even pinned ARM helper addresses. The runner verifies the slot suffix and IPS roundtrip. The transitive logical-query helpers, axis reader, and angle helper are controlled identically in direct differentials; they remain original dependencies in the executable image.

Run005 passed all 76 comparable direct fixtures across modes 0/1/2, unsupported modes, ordinary and boundary IDs, H2 pairs `(6,15)` and `(5,14)`, ID precedence, mode-1 short-circuit/suppression, both special-query rounds, all four calibration sectors, finite angle boundaries, signed calibration halfwords, written zero/nonzero samples, and result/trace/global-state/stack/callee-saved comparisons. A deliberately wrong helper target was detected. The direct comparison treats FPSCR condition codes as diagnostic: 36 of 76 comparable cases differed only in the N/Z condition bits (`0xA0000000`); the [AAPCS32](https://github.com/ARM-software/abi-aa/blob/main/aapcs32/aapcs32.rst) says FPSCR condition-code bits are not preserved across a public interface. Return values, helper traces, memory/global state, SP and saved registers matched. The axis reader's two output pointers can occupy the two local stack slots in opposite physical order; the harness compares output roles/values and records the raw offsets.

The explicit `special-no-write-reader-excluded` fixture is not counted as a pass or failure. `0x0027FBC8` returned without writing its outputs; the original reads prior stack values and the C++ locals are indeterminate. H2 has not been shown to exclude this path. No semantic claim covers it, and the candidate does not initialize those outputs.

Three compositions passed through the pinned original `0x001FF3C4` axis mover with the candidate query service: initialized idle, initialized primary ID 6 with the special ID 15 path, and initialized primary ID 6 with special ID 14. The harness supplies deterministic logical-query and float-helper outcomes and writes both axis sample outputs. It does not establish that live H2 always writes those outputs.

The full ARMv6K build passed 204/204 translation units after the ABI declaration change.

| Evidence | Result |
|---|---:|
| Original image SHA-256 | `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558` |
| Source / object SHA-256 | `b24453a8c20c4d6d306acb226d96fbcde90d92cfe3dd20378ee4fc00b11d15b5` / `2c5715a9d64e39b48f22a4c1d61fc1dc7c454ac170534a357d7c84a8fb49145f` |
| Relocated body SHA-256 / size | `9a77100a0cf3cd188c4bfe9a356895cd90a50f700cbe3e7e449433a895997786` / 640 bytes |
| Direct comparable cases | 76/76 passed; one no-write case excluded |
| FPSCR diagnostic differences | 36/76; caller-saved and not used for the pass decision |
| Original mover compositions | 3/3 passed |
| Wrong-helper-target control | detected |
| Slot IPS SHA-256 | `db23257413866439b86d9ce784da6804b5153106b7386a26356f1751443400ae` |
| Full ARMv6K build | 204/204 |
| Runtime | not run |

Independent review regenerated run007 with a distinct seed and sample count: 89 comparable direct cases passed, the one no-write case remained excluded, all three H2 compositions passed, and the wrong-target control was detected. The reviewer independently checked the H2 IDs, selector precedence, calibration sectors, and that FPSCR differences were only caller-saved N/Z bits under a zero-initialized test state. Review accepts only the written-output domain; it does not approve promotion for unrestricted H2 use. See the [review report](h2-00254ca8-independent-review.md).

Reproduce with:

```powershell
python tools/h2_254ca8_experiment.py --output build/agent-work/H2-semantic/h2-titleconfig-00254ca8-offline-integration/<fresh-run> --seed 20261112 --samples 40
python tools/build_check.py --out-dir build/h2-254ca8-full --jobs 4
```

## Limits

The supported differential domain requires both axis output floats to be written. No proof establishes that the initialized H2 path always satisfies that condition. NaN/Inf, unusual FPSCR/VFP unordered behavior, physical control mapping, natural event timing, no-write stack contents, exact fault/read ordering, MMIO/concurrent mutation, runtime audio and whole-game equivalence remain unverified. The implementation is non-identical and the ledger classification is `non_matching`; independent review accepted only the bounded written-output domain. The no-write path still lacks a proven semantic contract.
