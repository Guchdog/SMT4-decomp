# Independent integration review: `0x00286928`

## Recommendation

**Proceed to the project’s autonomous runtime comparison.** The offline-first gates and integration artifacts are in place: the exact production slot passes the staged differential and callback composition, all six negative controls are reported detected, the full 204-object build cache is present, and the IPS is replayable with only the 820-byte function slot changed. I found no source, ABI declaration, ledger, relocation, or patch-artifact defect.

Before commit/push, fix one concrete documentation issue: `README.md` contains two identical consecutive `0x00286928` rows (lines 52 and 53 in this checkout). After the dedicated runtime run, update the record/README with its exact scope and outcome. The earlier H2 comparison is not a substitute: it did not instrument this helper. The new runtime should set a breakpoint at `0x00286928` and capture entry args/return on both original and patched sides; do not claim the helper was reached without that probe.

## Frozen input and production identity

All 24 run-001 packet hashes match. The pinned original image hash is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. The ledger row is `0x00286928,820,non_matching,engine,engine_func_00286928,src/engine/leaf_batch45_a.cpp`, truthful for this changed C++ body.

The production function is a six-word raw ABI: four 32-bit register arguments plus two 32-bit stack arguments. The production definition and both inline-assembly consumer declarations in `leaf_batch18_b.cpp` and `leaf_batch24_c.cpp` use matching six-`uint32_t` signatures with C linkage. The inline assembly stages the trailing stack words before `BL`; no float type is inferred for arg6. The production function retains 17 original helpers in 22 direct call sites.

The staged manifest records a 812-byte function body in the 820-byte slot. I inspected the existing production object without rebuilding: its object SHA-256 is `2f79d91314429f6f341237b474cf8416bf8a08f1f47d9ee675eb5cce6f7ce4cb`; extracted raw symbol size is 812 bytes and there are 22 relocations. The patcher accepts only 22 unique aligned `R_ARM_CALL` relocations, resolves each by ledger symbol, rejects odd/Thumb targets and non-unconditional ARM BL opcodes, and checks alignment/range. The manifest lists all 22 as ARM and even. The staged slot ends with two ARM NOP words (`00f020e3 00f020e3`).

## Staged image and offline/build evidence

I independently recomputed hashes from the artifacts: staged image `32c7469f5cb8a6c8654d94f7fdc25e8c17733061081e92f585c819d109f05159`; original-based IPS `ace8db842a40af07e563c58b54d2fa71a057ad4d84c0190403107e58cef30862` (833 bytes); production object as above. The staged slot's first 812 bytes hash to the manifest’s relocated function body hash `cf49833b73ea58eeff3986af47a8c86d05c848123248a255f168bdb58e99c62c`. Read-only IPS replay against the pinned base exactly reproduces the staged image, and byte comparisons confirm everything outside the declared slot is unchanged. The manifest’s `non_matching`, `ips_roundtrip`, and `only_function_slot_changed` claims agree with these checks.

The candidate offline report pins the original, candidate source, runner, and object identities; it records 296 direct comparisons, four compositions through the original pinned `0x00221168` callback, and six detected controls. The staged production validation report independently identifies production source/object/image hashes and reports the same 296 direct and four callback cases passed. The callback body itself is original pinned ARM, and the staged run replaces only `0x00286928`; the upstream getters return synthetic fixture values. Six mutation controls are candidate/offline evidence, not rerun on the final staged binary.

The composition is useful real callback-to-helper code execution in the offline harness, but all helper direct callees and callback getter callees are intercepted. In particular `0x002B8D24` does not execute its original body. It does not cover the handler `0x001A07CC` continuation, the other 21 direct caller domains, invalid-pointer/MMIO/concurrency cases, or whole-game equivalence. These limits are disclosed in the function record and offline reports.

The full-build output contains 204 object files, including `leaf_batch45_a.o`, `leaf_batch18_b.o`, and `leaf_batch24_c.o`. The cached dependency manifests for all three affected TUs pin their source hashes to the current packet inputs. This agrees with the implementation report’s `build_check.py --repo-root`/four-job, 204-TU closure claim; I did not run or rebuild anything.

## Runtime and commit scope

No dedicated runtime comparison for this exact staged image has run. The previous paired H2 runtime report tested another cumulative image and did not install a breakpoint/counter at `0x00286928`. Given the passed offline production image comparison, ABI/interworking checks, caller composition and controls, it is appropriate to proceed with the project’s loopback-bound autonomous Azahar/GDB procedure. Compare pinned original against this exact staged replacement (or a manifest-pinned cumulative image containing the identical slot), record the helper entry and return on both sides, and keep the result scoped to the exercised titleConfig scenario. Readiness/re-entry and complete H2 acceptance remain separate gates.

**Commit recommendation:** source and patch are ready for runtime review; no code blocker to the runtime step. Hold commit/push until (1) the duplicate README row is removed and (2) the dedicated runtime result and helper-hit status are recorded accurately. This is not a request for manual playtesting and is not a claim of H2 closure.

Review was read-only: no build, candidate runner, or emulator was run. The only authored repository file is this assigned review.
