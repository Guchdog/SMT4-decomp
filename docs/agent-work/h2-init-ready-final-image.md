# H2 production callbacks and initializer final image — run-013

## Result

The final offline production-derived patch combines the reviewed Calc, Draw, Secondary, initializer, and ready-gate bodies in one image. It keeps the original entry addresses for all five functions, with a single cave branch for Calc and one for Secondary. The initializer is replaced in its original 572-byte span and its four strings are copied to the zero-filled `.rodata` page tail. The 48-byte ready body fits in its original 52-byte span and its one reviewed `R_ARM_CALL` resolves to `0x002BF41C`.

The serialized IPS re-applies to the recorded image, and its changed bytes stay within the seven declared records. All five callbacks pass final-address differential checks with their targeted negative controls. The State-9/10 title caller passes with the production initializer and ready gate executing from this exact patched image. The caller composition still models multiple subsystem services as HLEs and does not schedule Calc, Draw, or Secondary.

This closes the offline source, patch, callback, and caller work for H2. It does not establish visible UI behavior, physical input, edit/cancel/confirm semantics in the real menu, save persistence, restart behavior, or Azahar runtime equivalence.

## Artifact identity and placement

- Pinned original `code.bin`: 3,633,152 bytes, SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
- Final patched image: `build/agent-work/H2-semantic/h2-init-ready-final-image/run-013/combined-build-final/code.combined.bin`, SHA-256 `7b2bc2983a890e1c4cf1ae71beca9f574260d98d6cfcdffb3bbb34bd3eb2b291`.
- IPS: `build/agent-work/H2-semantic/h2-init-ready-final-image/run-013/combined-build-final/code.combined.ips`, SHA-256 `3901823e725afb914a9bc49c5f86038f8c285c107eedaa3a4337a64bc5b062d3`.
- Manifest: `build/agent-work/H2-semantic/h2-init-ready-final-image/run-013/combined-build-final/manifest.json`, SHA-256 `e866f14b9c5bcf0936afa67aadabfcf58fff47e20e37ae51802dfd75745fc298`.
- Patched image SHA-256 in manifest matches the supplied image. The builder independently reapplies serialized IPS and rejects any changed byte outside authorized records. It reports 4,006 changed bytes.

Placement map:

| Component | Guest VMA | Bytes | Placement/evidence |
|---|---:|---:|---|
| Calc entry | `0x001EA928` | 4 | Branch to `0x003FE624` |
| Calc body | `0x003FE624` | 2,096 | Four reviewed local `R_ARM_ABS32` targets rebased |
| Secondary entry | `0x002CAEF0` | 4 | Branch to `0x003FEED4` |
| Draw main | `0x002CAFD0` | 1,464 | Returns before retained original suffix |
| Draw helper | `0x003FEE54` | 124 | Seven Draw BL calls resolve here |
| Draw format string | `0x003FEED0` | 3 | `%s\0`, followed by one alignment byte |
| Secondary body | `0x003FEED4` | 292 | Zero ELF relocations; 8 bytes remain at cave end |
| Initializer | `0x002F4CA0` | 572 | Exact original span, no ELF relocations |
| Initializer string pool | `0x0042AB78` | 68 | Four strings in the audited `.rodata` tail |
| Ready gate | `0x002FC0EC` | 48 | One resolved `R_ARM_CALL` at `0x002FC108` to `0x002BF41C`; four original tail bytes remain untouched |

The string pool slots are 20, 16, 16, and 16 bytes for `TITLE_CONFIG_MAIN\0`, `TITLE_CONFIG D\0`, `camp/config.bf\0`, and `camp/config.mbm\0`. The exact copy and each zero-padded slot are in the manifest. The string addresses were independently reviewed against the image's ExHeader-sized `.rodata` page tail. Actual installed Azahar mapping and access protection still require runtime verification.

Production source/object/symbol identities are pinned in the manifest and the task-local reports:

- Calc source `c76ab50c12589404ca81e35373c8b136c50c91eb63c5af805bf05cc44c6081c7`; object `94197ad141393099a25e679b73457f127c54c7155fa4d8c2ff25270f8ca620fd`; symbol `script_vm_func_001ea928`, 2,096 bytes.
- Draw source `e5c6414cd37d2d6fc9928ca85eb5466a8c07bcec224a887616cb383ac408d64c`; object `0513196e3d93398036feba0177fc92cadadba87589068dc0605da64b0658ede2`; main symbol `ui_func_002cafd0`, 1,464 bytes.
- Secondary source `3ca4676613634ae91fe980e5e6e3c79fa74aff355e0facc50149749ba10b9c37`; object `e04b6dcb9ae560efa2e39202b04763263b03f1f61455efe5b54756ffda81d53e`; symbol `engine_func_002caef0`, 292 bytes, zero relocations.
- Initializer source `11b5360c77aecb4ab0e510774fd42a1cb479e8343aff4bb1a30d4cadeccc1b5e`; object `432664ba70073ff98c2fed19559d4f663f0e4dd9732c519e1bf66eda4dcfe82d`; symbol `_ZN4smt44camp25titleConfig_func_002f4ca0EPv`, 572 bytes, zero relocations.
- Ready source `609aaf963db8129a560293c8d1e65b3c6df8fa016673d28b0143535dadb4e4ee`; object `2c0ca7a51729389cce55cf31476f9a3075b50b3b4ef3cabebba9cffe0382b37`; symbol `ui_func_002fc0ec`, 48 bytes, with the one reviewed helper-call relocation.

## Final-address differential

Command:

```powershell
python tools/h2_combined_offline_validation.py --original extracted/exefs/code.bin --patched build/agent-work/H2-semantic/h2-init-ready-final-image/run-013/combined-build-final/code.combined.bin --manifest build/agent-work/H2-semantic/h2-init-ready-final-image/run-013/combined-build-final/manifest.json --output build/agent-work/H2-semantic/h2-init-ready-final-image/run-013/final-validation-final --seeds 7 20261024
```

Exit code 0. Report SHA-256 `336ba06a4a338cb805cd5b6bfcfd042ccfc7ea094ddecd11fbc3ebb0e021197a`.

- Calc: 16/16 persistent sequences, 54/54 ticks across seeds 7 and 20261024; wrong logical-map control detected.
- Draw: 46/46 directed cases; wrong helper-target control detected.
- Secondary: 34/34 cases across the same seeds; wrong-count mutant placed at the final cave VMA detected.
- Initializer: 10/10 cases across the same seeds. The exact production body runs at `0x002F4CA0`; task names and resource names are decoded from the copied pool. Comparison normalizes the expected pointer-address change while still checking string contents, helper order/arguments, work/global/config bytes, writes, return `r0`, PC/SP, and callee-saved state. A wrong-group-count mutant at the original entry is detected as a work difference.
- Ready gate: 4/4 cases at `0x002FC0EC`, with its `R_ARM_CALL` resolved at the final call site; the always-ready mutant is detected. This comparator verifies SP restoration and callee-saved GPR/VFP registers, not caller-owned stack bytes.

All five focused negative controls are reported as detected. Original subsystem helpers remain explicit dependencies and test boundaries according to each component report.

## State-9/10 caller composition

Command:

```powershell
python tools/h2_offline_caller_composition.py --patched-image build/agent-work/H2-semantic/h2-init-ready-final-image/run-013/combined-build-final/code.combined.bin --manifest build/agent-work/H2-semantic/h2-init-ready-final-image/run-013/combined-build-final/manifest.json --final-initializer --output build/agent-work/H2-semantic/h2-init-ready-final-image/run-013/caller-composition-final
```

Exit code 0. Report SHA-256 `5606654680b6083645086de13eea9e550c7b14398461b36995adf34cfb7af0cf`. The caller executes the production initializer and production ready gate from the patched image; `production_initializer_mode` is true. All three caller cases pass, and the wrong-primary-Calc-callback control is detected.

This caller harness still uses matched HLEs for allocation, task factory registration, task-active lookup, sprite/cursor/resource setup, sound/reset services, and several title transition helpers. It verifies registration tuples, title work/global state, the State-10 wait/reset path, and the flag gate. It never schedules or executes Calc, Draw, or Secondary via the task scheduler, and does not exercise rendered UI or physical input.

Caller-report provenance: the JSON root `source_sha256` and `object_sha256` identify the separately compiled experiment initializer artifact used only to construct the wrong-primary-Calc-callback control. The three positive patched-image caller cases pass `candidate=None` and execute the production initializer and ready gate in the exact image. Use the manifest's `initializer.source_sha256`, `initializer.object_sha256`, and `initializer.symbol_sha256` for production initializer identity. The callback-control candidate path is not a mutation of the exact production image.

## Remaining H2 runtime acceptance

The offline callback, patch, and caller closure is complete. H2's milestone acceptance still requires the Azahar CLI comparison: open the real settings screen, observe and edit the three options, test cancel/confirm/re-entry, compare saved configuration and restart persistence, and repeat against original and patched images under isolated profiles. No emulator, Azahar process, RSP connection, keyboard, or mouse was used for this offline batch. The prior RSP run stopped because the pinned GDB listener bound to `0.0.0.0`; resume only through a reviewed local-only route, retaining the CLI-only and no-keyboard/mouse constraints.
