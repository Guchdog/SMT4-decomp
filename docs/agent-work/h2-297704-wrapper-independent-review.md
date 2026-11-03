# Independent review: `0x00297704` TitleConfig loader wrapper

## Finding

The pinned 32-byte ARM body is a forwarding wrapper. Its entry ABI is `(name, out_status, flags, ignored_r3)`. It sets `r3=0`, creates the legacy base-AAPCS outgoing stack words `[sp]=0` and `[sp+4]=4`, calls the original loader at even ARM address `0x002AE6C8`, restores the caller stack, and returns the loader's raw `r0`. The typed C++ candidate follows this contract with the loader declaration using `pcs("aapcs")`; the ignored input word is not forwarded.

The exact TitleConfig caller slice `0x002F4DC8..0x002F4DEC` made two requests in order: `camp/config.bf` to `work+0x14C`, then `camp/config.mbm` to `work+0x150`, both with flags zero. Both candidate traces show `r3=0`, stack words `(0,4)`, and 8-byte-aligned helper SP.

## Independent fresh run

Ran the frozen experiment with seed `20261219` and 64 random cases. It passed 66 direct cases and the caller composition with no failures. Compared fields include the loader call trace, controlled raw return, final SP, `r4-r11`, `d8-d15`, and output memory. The size-argument negative control changed 4 to 8 and was detected (`calls differs`).

The candidate body is 24 bytes in the 32-byte slot. It has one `R_ARM_CALL` relocation at body offset 16 to `0x002AE6C8`; the target is even (ARM) and the pinned entry word is `0xE92D43F0`. The fresh staged image and IPS replay agree. The 45-byte IPS changes bytes only within `[0x00297704,0x00297724)` (26 differing bytes against the original); the final slot has two ARM NOP padding words. Current ledger classification is `non_matching`, consistent with differing bytes.

Fresh artifacts:

- Report: `build/agent-work/H2-semantic/h2-titleconfig-async-table-wrapper-00297704-review/run001/checks/review-seed-20261219/report.json` (SHA-256 `d16becf130f7c3a4cbdd3c60b71fe4e6c7d406e5e7cd788caf5b9ee81da8f661`)
- Candidate IPS: SHA-256 `4f5bc9df5a5ec70dbeaa38ed7b4e356efb8a9b68a30977b1d301fe40e513ed67`
- Staged image: SHA-256 `214499b98f249f63046cd064d054044d202deecb69f656960ed343e56d8e1d66`
- Pinned candidate source SHA-256: `096dab963546272519381c123dda584d1ce592c97d3c631e3ca0c3de4a789958`

## Limits

The downstream loader is intercepted at entry and returns a controlled value. This supports the wrapper's forwarding and raw-return ABI only. It does not exercise actual path resolution, async queue/request mutation, completion timing, failure behavior, loaded asset contents, resource lifetime, or initializer readiness. The test domain is ordinary mapped name/output memory; condition-flag parity is not asserted. No emulator or full build was run. This review supports the bounded wrapper contract and does not establish H2 lifecycle or whole-game equivalence.

## Reproduction

```powershell
python tools/h2_297704_wrapper_experiment.py --out build/agent-work/H2-semantic/h2-titleconfig-async-table-wrapper-00297704-review/run001/checks/review-seed-20261219 --seed 20261219 --random-cases 64
python tools/agent_workflow.py check-handoff --task h2-titleconfig-async-table-wrapper-00297704-review --run run001
```
