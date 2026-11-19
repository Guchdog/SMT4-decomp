# ComWin_Calc private paired runtime scenario

On 2026-11-18, after the offline ARM/interworking, entry differential and original-registration-boundary composition checks, the coordinator ran the private loopback Azahar lifecycle verifier against the pinned original and an image with only the experimental 0x0011b094 ComWin_Calc slot patched. This was not the seven-slot cumulative H2 image. The private staged candidate came from `build/agent-work/batch-h18-001/h18-h2-comwin-integration-study/run-001/checks/review-001/`; its candidate body is 144 bytes in the 148-byte subentry, with 128 changed bytes inside that subentry and an IPS roundtrip.

Command:

```powershell
python tools/h2_full_lifecycle_runtime_verify.py --final-image build/agent-work/batch-h18-001/h18-h2-comwin-integration-study/run-001/checks/review-001/staged_code.bin --final-ips build/agent-work/batch-h18-001/h18-h2-comwin-integration-study/run-001/checks/review-001/candidate.ips --output-dir build/agent-work/batch-h18-001/comwin-paired-runtime-001 --base-port 60170
```

Exit code 0. The verifier recorded 20/20 matching checkpoints, equal scripted-input traces, controlled lifecycle and same-session reentry completion, and matched cold-restart outcome. The result report is `build/agent-work/batch-h18-001/comwin-paired-runtime-001/autonomous-gdb-verification.json`, SHA-256 `8145b4c33dbf0d6ce5be01830f9c8d8dfcc7a0fa790dd5e28f992af21cbd059c`. Original code SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`, staged image `351656ece85df9fc76478e1e767e0069b23cded1df7bc5f247051e6cc83a46f2`, IPS `9fe024f83bcf2fb4fb5aed60fc60a9ae1416409975c8d8a88ff7860de59f3636`.

This is parity for the defined controlled lifecycle and these image bytes. The verifier forces logical query responses at 0x002c1830 during part of the scenario; it does not establish physical input mapping. It has no hit counter or breakpoint for 0x0011b094, so it does not establish that the callback executed. It also does not prove scheduler/widget semantics, code-source provenance beyond the pinned patch, or whole-game equivalence. The source placeholder and compound ledger span remain unchanged.
