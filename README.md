# Shin Megami Tensei IV (`CTR-P-AMXE`) Decompilation

Decompilation and reverse-engineering project for **Shin Megami Tensei IV** (Nintendo 3DS, US v0.1.0, Title ID `00040000000E5C00`, internal codename `sdds4`), aimed at recovering modifiable C++20 source code. The current build targets 3DS ARMv6K objects and a static library; linking a runnable game and PC / Android ports are future work.

> **Legal Notice:** This repository contains **no copyrighted ROM data, binaries, encryption keys, or extracted assets**. You must supply your own legally dumped `.cia` copy of *Shin Megami Tensei IV* (`CTR-P-AMXE`) and `aes_keys.txt` locally to extract `code.bin` and `RomFS`.

---

## Primary goal: editable C++ semantics

Find and reconstruct readable C++ with supported behavior. Byte-for-byte identity is not an acceptance requirement. Prioritize coherent milestone behavior, differential/caller evidence, and integration; do not optimize the project around matching opcodes.

Follow the [functional status](docs/functional-status.md), [milestone plan](docs/reconstruction-milestones.md), and [per-function workflow](docs/function-reconstruction-workflow.md). The [generated candidate inventory](docs/semantic-inventory.md) measures experimental definitions and static evidence links, not equivalence or integration. Milestone status lives in the functional and reconstruction plans. H2 (title audio settings) remains open: earlier paired runtime evidence stopped before readiness and re-entry, and the per-function conversions below do not close that milestone.

Use the [agent workflow](docs/agent-workflow.md) for bounded parallel contracts, implementation and independent review; the coordinator owns shared files, integration and the CPU budget.

Find new semantic work or review existing C++ for validation/integration:

```powershell
python tools/find_candidates.py --limit 20
python tools/find_candidates.py --include-existing-candidates --limit 20
```

## Full C++ reconstruction and native port progress

The [full reconstruction and native port plan](docs/native-port-plan.md) tracks every inventoried function and raw span through classification, readable C++ or a documented portable replacement, and contract-specific validation. Native gameplay scenarios are tracked separately from per-function coverage.

| Progress dimension | Current baseline |
| --- | --- |
| Original inventory | 10,959 functions and 8 raw spans; boundaries require audit |
| Readable byte-identical C++ | 60 functions reported by the historical exact ledger; this is not a complete semantic count |
| Experimental candidate inventory | 188 address-named definitions and 21 prefix/control/helper definitions in the [generated snapshot](docs/semantic-inventory.md); static presence is not validation or integration |
| Classified, integrated and contract-validated across the full inventory | Baseline audit pending; these dimensions must be counted separately |
| Native game scenarios without original ARM code | Not established; H20 tests isolated host HAL components |

The historical 100% exact-byte baseline is retained as a recoverable reference, not a claim about the current semantic ledger. H19's composite ARM image retains original code; H20's host tests do not establish a native game build. The next step is the reproducible P0 inventory audit described in the plan.

## Recent H2 C++ semantic progress

The following H2 functions have typed C++ definitions, with ledger classifications and per-function evidence recorded below. Several are bounded helpers that retain original ARM services. The paired runtime comparison establishes parity only for its defined scripted scenario on the recorded cumulative image; it does not establish whole-game or full H2 equivalence.

| Address | Reconstructed behavior | Recorded evidence |
| --- | --- | --- |
| `0x00221168` | `titleConfig` nested callback slice | 20 paired callback returns and 19 checkpoints; readiness and re-entry remain incomplete. [Function record](docs/function-records/0x00221168.md) |
| `0x0028DF54` | H2 state-field writes and raw return | 64 direct cases, 64 compositions through original `0x00286928`, one negative control; RAM/ordering limits documented. [Function record](docs/function-records/0x0028df54.md) |
| `0x00289640` | H2 nested callback raw state-word getter | 40 direct cases and five compositions through original `0x00221168`, reaching the actual getter twice in each case; wrong-offset mutation detected. The 20-byte typed C++ body is `non_matching`; it preserves ordered reads, the raw return and no-write behavior. [Function record](docs/function-records/0x00289640.md) |
| `0x0028686C` | H2 callback context getter | 38 direct cases and 50 compositions through original `0x00221168`; wrong-offset mutation detected. The typed 20-byte C++ body is `non_matching`; independent review passed, and the full ARMv6K build passed 204/204 TUs. [Function record](docs/function-records/0x0028686c.md) |
| `0x00296F60` | H2 callback value getter | 109 direct cases, including 48 Cartesian float-boundary cases, and 24 compositions through original `0x00221168`; two mutation controls detected. The 156-byte body is `non_matching`; independent review passed and the full ARMv6K build passed 204/204 TUs. [Function record](docs/function-records/0x00296f60.md) |
| `0x002C1F28` | Signed global predicate and byte return | 153 direct cases, 32 zero-result caller compositions, three negative controls; six named callsites audited. [Function record](docs/function-records/0x002c1f28.md) |
| `0x002B89A0` | Null or manager-mode predicate | 139 direct cases, 32 nonzero caller continuations, three negative controls; caller entry is asserted. [Function record](docs/function-records/0x002b89a0.md) |
| `0x002AF854` | Indexed field selection with ordered alias-safe accesses | 503 direct cases, 32 disjoint and 32 cross-alias compositions through original `0x002B8D24`, five controls; selector-12 cross-call aliasing is covered by two five-call chains for one documented topology. [Function record](docs/function-records/0x002af854.md) |
| `0x002CAB70`, `0x0021F39C`, `0x002E0AF4` | `titleConfig` config-byte-to-index mappers | Two 512-case runs per mapper, each covering all 256 byte values, plus production-image checks and initializer caller compositions. [Mapper records](docs/function-records/0x002cab70.md), [0x0021F39C](docs/function-records/0x0021f39c.md), [0x002E0AF4](docs/function-records/0x002e0af4.md) |
| `0x002BF030` | Sentinel-counted table selector, retaining original service `0x00138934` | 128 direct cases, 24 compositions through original `0x002B8D24`, six negative controls; full service branches and cumulative H2 runtime remain open. [Function record](docs/function-records/0x002bf030.md) |
| `0x002B8D24` | Typed selector dispatcher, retaining original helpers `0x002AF854`, `0x002BF030` and `0x001384F0` | 116 direct cases, two selector-11 caller compositions, two five-call selector-12 cross-alias chains and seven controls; 356/360 bytes. Paired cumulative-image H2 runtime matched 19/19 checkpoints across 51 scripted actions; a hit at this helper is unverified, and readiness/re-entry still prevent H2 closure. [Function record](docs/function-records/0x002b8d24.md) |
| `0x00286928` | Typed titleConfig state dispatcher, retaining its original callees | 296 direct cases, four compositions through original callback `0x00221168`, six negative controls; 812/820 bytes and 22 ARM call relocations. Cumulative paired runtime captured 129/129 helper hits with arguments/returns matched and 19/19 checkpoints across 51 actions; readiness/re-entry are incomplete, so H2 remains open. [Function record](docs/function-records/0x00286928.md) |
| `0x002B0188` | Group manager-table resolver with preserved `node_index` tail-call ABI | 261 direct cases, signed quotient boundaries, null entries and two detected mutations. The final-address body matches the 24-byte original; full build 204/204. [Function record](docs/function-records/0x002b0188.md) |
| `0x002B787C` | `AsdText_GetLineCount`, retaining original text-code helpers | 515 direct cases, selector 11/19 caller compositions, six controls; 176/176 bytes and two ARM call relocations. Final-address staged differential passed. Paired Azahar scenario matched 19/19 H2 checkpoints; a GDB-controlled direct invocation returned/consumed `1` in both profiles. The normal H2 selector-6 route does not reach this helper, and the probe does not establish natural runtime caller reachability. [Function record](docs/function-records/0x002b787c.md) |
| `0x002AE6B0` | `AsdText_IsControlCode`, unsigned predicate for `[0xF801, 0xF88F]` | Exhaustive 65,536 halfword values, 18 directed and 512 seeded 32-bit cases, two boundary mutation controls, and selector 11/19 partial compositions through original callers (other services stubbed; imported harness hashes not pinned); 24/24 bytes with no relocations, but bytes differ. Runtime not run for this helper. [Function record](docs/function-records/0x002ae6b0.md) |
| `0x002AE664` | ASD control-code mapping helper used by `AsdText_GetLineCount` | 65,798 direct values, three table layouts, two detected mutations; 515 line-count cases plus selector 11/19 compositions through original callers. Candidate 56/76 bytes, zero relocations; bytes differ. Stack spill and runtime limits are documented. [Function record](docs/function-records/0x002ae664.md) |
| `0x002BF41C` | Task-registration lookup for `TitleConfig_IsReady` | All 4,096 bucket indices, empty/boundary handles, 5 chain probes, 64 seeded chains, two mutations; five compositions through the original ready gate. 68/68 bytes, no relocations, but bytes differ. Runtime/scheduler lifecycle not run. [Function record](docs/function-records/0x002bf41c.md) |
| `0x002B88C4` | Touch-region registration used by titleConfig and UI callers | Staged together with typed `0x002BF6D0` into H2 run-013; the two-slot image passed 58/58 original-caller comparisons and an independent fresh-seed review. Body 156/220 bytes. Runtime and scheduler lifecycle remain unverified. [Function record](docs/function-records/0x002b88c4.md) |
| `0x002BF6D0` | H2 indexed manager-node resolver used by `0x002B88C4` | 2,269 direct signed-index cases, 42 original caller compositions, three detected controls; body is 60/64 bytes with even ARM calls to `0x002B0188` and `0x002C615C`. Independent review passed; stack spill residue/runtime remain unverified. [Function record](docs/function-records/0x002bf6d0.md) |
| `0x002A63F8` | `AsdRes_IsLoaded`, testing bit 2 of the resolved resource record | 8 direct fixtures plus the original null-result fault, three compositions through the actual `TitleConfig_Calc` call slice, and two negative controls. Staged as a 24-byte one-slot IPS overlay; independent review confirmed the staged null fault at offset 8 and the `non_matching` ledger label. Runtime is not run. [Function record](docs/function-records/0x002a63f8.md) |
| `0x002B96F0` | Typed 24-byte group-table resolver and subindex tail call | 103 direct fixtures, paired `TitleConfig_Calc` caller compositions, group-stride mutation detected, and second-index mutation rejected for exceeding the slot. Final-VMA relocation produces the original bytes, so ledger stays `matching`; runtime is not run. [Function record](docs/function-records/0x002b96f0.md) |
| `0x002C1830` | Logical query dispatcher used by TitleConfig_Calc | 114 direct cases, three controls and 43 scenarios cover all six original Calc call PCs and seven ID/mode combinations; 264/504-byte body and six ARM calls. Slot-only IPS, independent review accepted and full ARMv6K build passed 204/204; runtime not run. [Function record](docs/function-records/0x002c1830.md) |
| `0x0029EDFC` | Cursor range update called by TitleConfig_Calc | 14 direct cases, three controls and four actual touch-path compositions cover handled indices 0–2 and selected-row skip. 44/80-byte body with one ARM tail relocation; slot-only IPS, independent review and build passed 204/204. Runtime not run. [Function record](docs/function-records/0x0029edfc.md) |
| `0x00297674` | Full-width global state word getter used in TitleConfig_Calc state 2 | Seven direct values, null fault, three controls and 28 original-caller cases; 20-byte body differs in two bytes. Slot-only IPS, independent review and full ARMv6K build passed 204/204. Runtime not run. [Function record](docs/function-records/0x00297674.md) |
| `0x002C17D4` | Logical input bit query used by the cursor and mode-2 dispatcher | 134 direct cases, four detected controls and 17 original-dispatcher compositions; 92/92-byte body with no relocations. Slot-only IPS, independent review and full ARMv6K build passed 204/204. Runtime and full cursor paths not run. [Function record](docs/function-records/0x002c17d4.md) |
| `0x002892C0` | H2 cursor axis clamp and position update helper | 1,220 direct and 360 original-wrapper compositions; 136-byte production body at `0x003FEE64` in a Calc-only base. Combined IPS roundtrip and wrong-entry control pass; independent review and the full ARMv6K build (204/204) pass. It is not merged into the accumulated five-callback image; runtime not run. [Function record](docs/function-records/0x002892c0.md) |
| `0x0027FBC8` | Calibrated axis sample reader used by the H2 query service | Production C++ body is 300/320 bytes with two calls to original `0x0019FE4C`; 146 direct and final-VMA cases, six original camera call-slice cases, mutation controls detected, affected TU builds and independent review accepted. `0x00254CA8` no-write stack reads remain unresolved. [Function record](docs/function-records/0x0027fbc8.md) |
| `0x002BDAC0` | Table-selected position setup used by TitleConfig_Calc | 72 direct cases, three null-table cases, an alias/order case, three negative controls, and both actual TitleConfig_Calc call slices; 80/108-byte body and slot-only cumulative IPS. Independent review accepted and full ARMv6K build passed 204/204; runtime not run. [Function record](docs/function-records/0x002bdac0.md) |
| `0x0029F260`, `0x0029F248` | Guarded ASD slot getters for fields `+0x24` and `+0x20` | 76 direct cases per getter, four actual `TitleConfig_Calc` caller-slice cases, two mutation controls, and a cumulative three-slot H2 IPS overlay. Each body is 20/24 bytes and differs from the original; independent review confirmed relocation targets, ledger status and slot scope. Runtime is not run. [0x0029F260](docs/function-records/0x0029f260.md), [0x0029F248](docs/function-records/0x0029f248.md) |
| `0x001078D8` | H2 logical input counter refresh, composed with converted state reader `0x0011C5EC` | 140 direct cases, four original-caller compositions, and 144 full-chain original-versus-two-slot-production compositions across two fresh seeds; row-31 sentinel, 31-to-30 mutation, slot-only IPS, and independent review pass. Body is 160/164 bytes. Runtime and input cadence remain unresolved. [Function record](docs/function-records/0x001078d8.md) |
| `0x0011C5EC` | H2 input-state reader with seven original callees | 288 direct cases, 32 compositions through original `0x001078D8`, three mutation controls, and 144 full-chain compositions; body is 304/304 bytes. Independent review supports valid, disjoint synthetic ordinary memory; physical input and runtime behavior remain open. [Function record](docs/function-records/0x0011c5ec.md) |
| `0x001285C4` | H2 input calibration clamp called by `0x0011C5EC` | 334 direct cases, 16 compositions through the original reader and `0x001078D8`, three detected mutations; body is 76/76 bytes with no relocations. Independent review passed; runtime/input provenance remain unverified. [Function record](docs/function-records/0x001285c4.md) |
| `0x00128610` | H2 sample-normalizer selector dispatcher called by `0x0011C5EC` | 254 direct cases against the three original normalizers, 12 original-reader/caller compositions, four detected mutations; body is 144/148 bytes with three even ARM relocations. Independent review passed; input provenance/runtime remain unverified. [Function record](docs/function-records/0x00128610.md) |
| `0x0013B8F8` | H2 selector-1 signed deadzone normalizer | 176 direct cases, 16 original reader/caller compositions, 31 zero-denominator fixtures and three detected mutations; body is 252/260 bytes with three even ARM calls to original divider `0x002C615C`. Independent review passed; runtime/input provenance remain unverified. [Function record](docs/function-records/0x0013b8f8.md) |
| `0x0013B9FC` | H2 selector-0 radial input normalizer | 107 direct cases and 16 original reader/caller compositions; 14 zero-divisor fixtures (28 final quotient calls), three detected mutations; body is 208/228 bytes with three even ARM calls to original divider `0x002C615C`. Two independent fresh seeds passed; runtime/input provenance remain unverified. [Function record](docs/function-records/0x0013b9fc.md) |
| `0x0013BAE0` | H2 selector-2 VFP axis normalizer | 352 direct cases and 18 reader/dispatcher compositions; three detected mutations; body is 368/460 bytes with no relocations. Independent review passed. FPSCR flag parity and exceptional domains remain unverified. [Function record](docs/function-records/0x0013bae0.md) |
| `0x0013B9FC`, `0x0013B8F8`, `0x0013BAE0` | Integrated H2 selector-0/1/2 normalizers | Three production slots staged together passed 402/402 original-reader/dispatcher compositions (132 per selector) across two seeds; independent review, even ARM targets, IPS slot audit, and all four affected TU compiles passed. Reader/dispatcher remain original; runtime/input provenance are unverified. [Integration report](docs/agent-work/h2-input-normalizers-batch-integration.md) |
| `0x0013BCAC` | H2 input record postprocessor called by `0x0011C5EC` | Coordinator and independent runs passed 192 direct transition-bit/full-word cases and 32 compositions through the original reader; the optional helper ran in 16 cases and a bit-condition mutation was detected. The 148/212-byte body has no relocations and passes slot-only IPS replay. Independent review and full build (204/204 TUs) passed. Physical input and runtime behavior remain open. [Function record](docs/function-records/0x0013bcac.md) |
| `0x002B9008` | Shared H2 secondary-callback manager counter helper | 32 signed-boundary/caller-register cases, exact 36/36-byte slot, threshold and offset mutation controls, slot-only IPS replay, and affected-TU build. Shared scheduler/manager lifecycle remains open. [Function record](docs/function-records/0x002b9008.md) |
| `0x002F5B2C`, `0x002D65B4` | Indexed byte/halfword getters used by the six-entry H2 configuration loop | 44 direct final-VMA cases plus two compositions through original `0x00286928` (six calls per getter); four offset/bound mutation controls detected. Both bodies fit their slots, have no relocations, and are staged by a two-slot IPS. [0x002F5B2C](docs/function-records/0x002f5b2c.md), [0x002D65B4](docs/function-records/0x002d65b4.md) |
| `0x002B8B78` | Six-slot profile transition used by TitleConfig and a conditional callback path | Independently reviewed; 23 direct final-VMA cases, two original caller call-slice compositions, and four mutation controls. The 332/340-byte body has six branch instructions to five unique ARM targets and one verified ROM table relocation. Dependencies remain original; runtime/audio output is unverified. [Function record](docs/function-records/0x002b8b78.md) |
| `0x002AEA28` | Indexed TBB profile payload selector used twice by `0x002B8B78` | Independently reviewed; 16 direct final-VMA cases, two original caller slices and three mutation controls; 56/56-byte body with three ARM relocations. TBB services are controlled hooks in these tests. [Function record](docs/function-records/0x002aea28.md) |
| `0x002C0E4C` | TBB row-count query used by the H2 profile selector | Independently reviewed typed C++; its 56-byte final-VMA body remains byte-identical after relocation. Passed 13 direct cases, five compositions through `0x002AEA28`, and three mutation controls; retains the original ARM unsigned divider. [Function record](docs/function-records/0x002c0e4c.md) |
| `0x002B8794` | Profile-slot registry and manager updater called six times by `0x002B8B78` | Independently reviewed typed C++; 12 direct fixtures, two original caller slices with six real calls each, and three mutation controls. Body is 272/304 bytes with no relocations. [Function record](docs/function-records/0x002b8794.md) |
| `0x00296F18` | Typed H2 cursor-axis record initializer used by `0x0029FAE8` | 61 direct cases, matching boundary fault, three detected mutations, and exact two-call TitleConfig setup composition; 68/72 bytes, no relocations, independent review. Both final axes have start 1 after wrapper finalization; runtime and broader H2 remain open. [Function record](docs/function-records/0x00296f18.md) |
| `0x0029FAE8` | Typed cursor setup orchestration retaining the original divider and axis-record helpers | 60 direct original-versus-C++ cases in coordinator and independent runs; both wrap routes and repeat modes, exact H2 helper trace/final records, and a detected wrong-target control. The 392-byte body fits the 452-byte slot; seven ARM `BL` relocations resolve to even aligned original entries. Runtime and full TitleConfig behavior remain open. [Function record](docs/function-records/0x0029fae8.md) |
| `0x002BDB2C` | TitleConfig sprite-node setup retaining original `AsdMem_Zero` | 36 direct cases, the exact original TitleConfig caller slice, final node/group bytes, raw return and tested callee-saved state, plus a detected wrong-zero-target control. The 148-byte body fits the 152-byte slot; independent 52-case review and full build (204/204 TUs) passed. Resource lookup/rendering and full H2 behavior remain unverified; write-width/order parity is limited to ordinary RAM without concurrent observers. [Function record](docs/function-records/0x002bdb2c.md) |
| `0x002C32F8` | TitleConfig sprite-group descriptor binder | 51 direct cases, exact group-init/bind caller slice, raw return, full descriptor bytes and detected missing-count-store control. The body is 76/76 bytes with no relocations; independent 67-case review and full build (204/204 TUs) passed. Table rendering and store-order observability remain unverified. [Function record](docs/function-records/0x002c32f8.md) |
| `0x00297704` | TitleConfig asynchronous table-load wrapper | Coordinator 34 and independent 66 direct cases, plus both calls through the exact TitleConfig slice; loader register/stack arguments, raw return and preserved state checked. The 24/32-byte body has one even ARM call to original `0x002AE6C8`; independent review and full build (204/204 TUs) passed. Async completion and loaded assets are unverified. [Function record](docs/function-records/0x00297704.md) |
| `0x0012A758` | H2 input ring reader used by `0x0011C5EC` | 1,225 directed + 128 seeded direct cases, five one-field retry mutations plus a repeated retry, and eight real-reader compositions with the actual helper body. The 404/424-byte body has no relocations; four signedness/cap/modulus/store-order mutations were detected. It is `non_matching`; producer lifecycle and physical input remain unknown. [Function record](docs/function-records/0x0012a758.md), [conversion evidence](docs/agent-work/h2-input-ring-reader-conversion.md) |
| `0x00128C2C` | H2 input mode-four predicate called by original `0x0011C5EC` | 256 direct byte cases and 14 original-reader compositions; mode 4 alone takes the early return. The typed wrapper uses 24 bytes inside its 84-byte span, while the separately callable SVC interior and literals remain unchanged. Wrong-constant mutation detected; this row is `non_matching`. [Function record](docs/function-records/0x00128c2c.md), [conversion evidence](docs/agent-work/h2-input-mode-wrapper-conversion.md) |
| `0x00138F34` | H2 input mode unsigned byte getter used by original `0x00128C2C` wrapper | 256 direct byte cases and 14 compositions through original `0x0011C5EC`; the wrapper and reader return early only for mode 4. A signed-load mutation was detected; the 16/16-byte body has no relocations and is `non_matching`. Independent review and full build (204/204 TUs) passed. Physical mode source and runtime remain unknown. [Function record](docs/function-records/0x00138f34.md), [conversion evidence](docs/agent-work/h2-input-mode-getter-conversion.md) |
| `0x002BB978`, `0x002BC9C8` | H2 signed-byte input flag getters | 512 direct cases cover every byte value for both getters; 25 compositions through original `0x0011C5EC` verify return/state/write parity and the second getter short-circuit, plus an unsigned-load mutation. Both 16-byte bodies have no relocations and are `non_matching`; physical input provenance and runtime remain unproven. [Getter records](docs/function-records/0x002bb978.md), [conversion evidence](docs/agent-work/h2-input-flag-getters-conversion.md) |

The recent helper batch compiled all 204 translation units. Runtime and integration limits remain explicit in the per-function reviews and the [H2 milestone record](docs/milestones/H2-audio-settings.md).

---

## Reference byte coverage

- **Current ledger exact matches:** `3,117,288 / 3,139,108 bytes` (**99.3049%**) across `10,883` matching functions and `8` matching raw spans, according to the current `config/functions.csv` classifications.
- **Current non-matching reconstructions:** `21,820 bytes` across `76` functions; semantic evidence is recorded per function. `0x002B0188` and `0x002B96F0` have typed C++, but their relocated final bodies are byte-identical and remain `matching`. `0x00207D84`, `0x0027FBC8`, `0x002C17D4`, `0x002892C0`, `0x00297674`, `0x0029EDFC`, `0x0029F248`, `0x0029F260`, `0x002A63F8`, `0x002B787C`, `0x002AE6B0`, `0x002AE664`, `0x002BF41C`, `0x002B88C4`, `0x002BF6D0`, `0x002BDAC0`, `0x002C1830`, `0x002C32F8`, `0x002C615C`, `0x00297704`, `0x0029F278`, `0x001FF3C4`, `0x00254CA8`, `0x001078D8`, `0x0011C5EC`, `0x001285C4`, `0x00128610`, `0x0013B8F8`, `0x0013B9FC`, `0x0013BAE0`, `0x0013BCAC`, `0x002B9008`, `0x002F5B2C`, `0x002D65B4`, `0x002B8B78`, `0x002AEA28`, `0x002B8794`, `0x002B85BC`, `0x002AA268`, `0x002A8A8C`, `0x002BDB2C`, `0x002BB978`, `0x002BC9C8`, `0x00138F34`, `0x00128C2C`, `0x0012A758`, `0x00289640`, `0x0028686C`, and `0x00296F60` have typed C++ with bounded offline evidence; caller and runtime scope is documented per function.
- **Cumulative-image placement limit:** generic UI transform `0x00207D84` passes bounded VFP and caller differentials, but its 156-byte body exceeds the 128-byte slot. Its standalone cave at `0x003FEE54` overlaps Draw/Secondary code in the current cumulative H2 image, so it is not integrated there. No direct TitleConfig/Audio Settings reachability is established. See the [function record](docs/function-records/0x00207d84.md) and [placement review](docs/agent-work/ui-transform-independent-review-00207d84.md).
- **Readable byte-identical C++ reconstructions:** `60` functions from the historical exact-conversion count. Non-identical semantic reconstructions, including `0x002B787C`, are counted separately in the ledger.
- **Total Codebase Explored:** `3,139,108 / 3,139,108 bytes` (**100.0000%**) across `10,959` functions and `8` raw spans; this measures mapped inventory, not byte matching or behavioral equivalence.
- See [`PROGRESS.md`](PROGRESS.md) for the full subsystem breakdown (`ui`, `camp`, `battle`, `script_vm`, `shop`, `unite`, `engine`, `nn_sdk`, `crt`) and explored function ledger. Coverage totals use original function sizes and do not measure behavioral equivalence.

---

## Quick Start

Install Python dependencies with `python -m pip install -r requirements.txt`. Clang is required for ARM compilation; CMake and Ninja are required for the CMake build. See [development setup](docs/development.md) for compiler configuration, build commands, and tests. Run `python -m unittest discover -s tests -v` for tests; tests requiring private game files skip when those files are absent.

### 1. Extract `code.bin` and UI/HUD Assets from Your Local CIA
Place your `.cia` and `aes_keys.txt` in the repository root (both are automatically ignored by `.gitignore`) and run:
```powershell
python tools/extract.py
```
This auto-selects a CIA only when exactly one is present; otherwise pass `--cia path/to/game.cia`. It decrypts the CIA, decompresses the BLZ-compressed `ExeFS/.code` into `extracted/exefs/code.bin` (`0x377000` bytes), verifies its size and SHA-256 against the configured revision by default, indexes all 20,126 RomFS files in `extracted/romfs_index.json`, and extracts UI/HUD folders.

### 2. Analyze Functions & Subsystem Xrefs
```powershell
python tools/analyze_code.py
```
Scans all `3,139,108` bytes of `.text` (`0x00100000`–`0x003FE624`), resolves literal pools and inline `ADR` strings (including original Atlus `c:\SMT4\XRD686\...` source file paths), and writes review proposals to `build/analysis/functions.csv`, `symbols.csv`, and `ledger_diff.json`. The curated files in `config/` are never overwritten; review boundary changes before manually accepting individual discoveries.

### 3. Disassemble Any Function or HUD Subsystem
```powershell
# Disassemble a specific function by address or original Atlus source name:
python tools/split_asm.py --addr 0x002ac2f4
python tools/split_asm.py --name StatusDown --limit 3
python tools/split_asm.py --category ui --limit 10
```

### 4. Inspect `.tbb` (`TBCR`/`TBL1`) UI Tables and `.bf` (`FLW0`) FlowScripts
```powershell
python tools/inspect_assets.py extracted/romfs/saveLoadUI/SaveLoadUITable.tbb extracted/romfs/saveLoadUI/saveloadUI.bf
```

### 5. Verify Progress & Update `PROGRESS.md`
```powershell
python tools/progress.py --write
```

---

## Project Structure

- [`config/game_info.json`](config/game_info.json) — Memory map and binary metadata for `CTR-P-AMXE`.
- [`config/functions.csv`](config/functions.csv) — Master ledger of 10,959 callable functions and 8 explicitly labeled non-function spans covering 100% of `.text` (`3,139,108` bytes).
- [`config/symbols.csv`](config/symbols.csv) — String and data symbols recovered from `.rodata`, `.data`, and `.text` literal pools.
- [`include/`](include/) & [`src/`](src/) — Decompiled C++20 source code and engine/UI headers.
- [`docs/architecture.md`](docs/architecture.md) — Documentation of the `XRD686` / `AsdSDK` engine, dual-screen LCD pipelines, and `TBCR`/`TBL1` UI table formats.
- [`tools/`](tools/) — Extraction, static analysis, annotated disassembly, asset inspection, and progress verification scripts.
