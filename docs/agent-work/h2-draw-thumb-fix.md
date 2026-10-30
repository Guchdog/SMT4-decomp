# H2 Draw formatter Thumb-state fix

## Result

Changed the production Draw callback and experimental candidate to pass the Thumb-tagged formatter entry `0x002BE7FD` to `BLX`. The pinned original uses an ARM `BLX` immediate to `0x002BE7FC`, which selects Thumb state. The prior even pointer selected ARM state at Thumb instructions. The runtime Draw/Secondary split crash is consistent with this defect, but has not yet been retested with the corrected full H2 image.

The coordinator also strengthened `tools/h2_draw_experiment.py`: each mocked service boundary checks CPSR.T; the formatter trace records the mode; the fixture's indirect cache callback asserts its expected ARM state. The wrong-state negative control compiles the prior even pointer and is rejected specifically with `format_text entered with CPSR.T=0, expected 1`.

## Build and differential evidence

- Production `src/engine/leaf_batch43_a.cpp` compiled with the repository ARMv6K Clang flags into the private `run-001/production-rerun` directory. Exit 0. Object SHA-256 `250598c55e1b175f1e9316425cc83810331340e92286346b8d5f87b9dd89adb4`, size 99,776 bytes. Its manifest binds it to current source SHA-256 `5ca7486aaa1244ae5e95b9e5073a7f1c49d1568cd6ad01139bc14bd86c0c0726` and the recorded compiler/flags.
- In `ui_func_002cafd0`, disassembly at object offset `0x117ac` is `add r3, r10, #129`; at `0x117b0` it is `blx r3`. `r10` is loaded from the formatter base literal, and adding `0x81` preserves bit 0. Thus the emitted indirect BLX selects Thumb. The equivalent original call is `blx` immediate to the even code address, which changes state based on the instruction encoding rather than the destination address's low bit.
- Candidate runner report: `build/agent-work/H2-semantic/h2-draw-thumb-fix/run-001/checks/after-thumb-fix/report.json`, SHA-256 `92e7ed77d510c7f82ae0bc94719daba41265070eb8ec18760bffdaef81241184`. The candidate object is 2,252 bytes, SHA-256 `b81e681ed76e104ad07cb26397758dd6495f21b43eddb0cf9f564f8ebb679fff`. All 46 directed scenarios passed. No counterexample. The existing wrong-stride control was detected (`trace differs`); the new wrong-state control was detected at the formatter hook. The pinned input image SHA is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
- `python -m unittest tests.test_h2_draw_experiment`: exit 0, 5 tests passed.

## Changed files

- `src/engine/leaf_batch43_a.cpp`
- `experiments/semantic_equivalence/h2_draw_candidate.cpp`
- `tools/h2_draw_experiment.py`
- `tests/test_h2_draw_experiment.py`

## Limits and next action

The helper hooks still replace formatter, layout, TBB, renderer, touch, and cache-callback behavior. The differential proves the selected contract under those mocks and now detects the previously hidden instruction-state mismatch; it does not prove real helper side effects, formatter string/descriptor reads, caller reachability, the full titleConfig initializer, or runtime equivalence. Rebuild the production patch chain from the pinned original, recheck code-cave size/relocations and all derived IPS/profile hashes, get independent review, then repeat the original-versus-patched Audio Settings CLI scenario with user-controlled inputs. Preserve crash dumps privately.
