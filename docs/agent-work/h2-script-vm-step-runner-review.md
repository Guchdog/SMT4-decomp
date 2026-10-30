# Independent review — H2 script-step dispatcher

## Finding

The production `script_vm_func_0019dfbc(void*)` is a boundedly acceptable typed reconstruction of the dispatcher contract for valid mapped work/table pointers and valid handler IDs. Its lookup, branches, state writes, returns, and preserved callee-saved registers agree with the pinned ARM path. This recommendation is limited to the synthetic handler model exercised offline. It does not establish what real scripts or result `2` mean, and it is not patch-image or H2 runtime acceptance.

## ARM and source review

I verified `extracted/exefs/code.bin` against the pinned US v0.1.0 SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. Decoding the 120-byte span at `0x0019DFBC` shows the implementation contract:

- Preserve `r4-r6` and return through a balanced `push {r4,r5,r6,lr}` / `pop {r4,r5,r6,pc}` frame.
- Load the work instruction at `+0x18` and method table pointer at `+0xBC`; add `instruction * 4`, read the halfword handler ID, then load the callback from `0x0044DED0 + 4*handler_id` and call it with the original work pointer.
- Result `0`: clear `+0xD0`, return `2`. Result `2`: increment 32-bit counters at `+0xCC` and `+0xD0`, return `1`. Result `1`: clear `+0xD0` and dispatch again. Other results dispatch again without dispatcher counter changes.

The typed production body expresses these same offsets and branches. The candidate source and production symbol compile to the same 128-byte relocation-free body (SHA-256 `c0cbad2f317c22e16ea12159e32e8b13180ca5ad4df12af8d994f53f8508cd48`). I independently extracted both existing objects: candidate object SHA-256 `a75be9760192e5dd849a43166e425903a51a88aca339fb7cc8a2dfb339e90949`; production TU object SHA-256 `0dc95e41b5cb062ea9d30d15f6b70766565956f575d0b51fb20b887a910f8956`. Both target symbols had no relocations. The 128-byte production body exceeds the original 120-byte span; it remains classified `non_matching`, and no code.bin patch is evidenced.

## Differential and compile evidence review

The final differential report is `build/agent-work/H2-semantic/h2-script-vm-step-runner/run-003/reports/final-differential.json`, SHA-256 `ebb2f58ad9f659234c20d8dd96df26ea7118bd245536d10ebc03831e1174da91`. Its reference hash agrees with the pinned image. Five synthetic sequences report full work-byte, return, PC, SP, and `r4-r6` agreement, with directed state checks:

| Callback outcomes | Result / index / `+0xCC` / `+0xD0` / calls |
|---|---|
| `[0]` | `2 / 1 / 19 / 0 / 1` |
| `[2]` | `1 / 1 / 20 / 34 / 1` |
| `[1,0]` | `2 / 2 / 19 / 0 / 2` |
| `[3,1,2]` | `1 / 3 / 20 / 1 / 3` |
| `[255,0]` | `2 / 2 / 19 / 0 / 2` |

The deliberate always-return-2 negative control is detected (`original_return=1`, mutant `2`). For the non-advancing result-1 callback, the harness stops at the same eighth callback-entry boundary on both implementations; both have equal callback count and PC (`0x02000080`) and match state. This proves parity only at the explicit bounded stop; it is not a termination or liveness claim. The harness callback stubs advance the script index except in this deliberate stuck case and increment a synthetic callback counter. They are models, not discovered game handlers.

The private compile report is `build/agent-work/H2-semantic/h2-script-vm-step-runner/run-003/reports/compile-report.json`, SHA-256 `02ea661f57c288a28ac93aae4ed654f4d687b040078061f9bb18b3c792982dbd`. All seven listed objects exist and match their recorded SHA-256 values: the production TU plus six caller TUs (`leaf_batch19_a`, `leaf_batch19_b`, `leaf_batch20_c`, `leaf_batch22_c`, `leaf_batch29_c`, and `leaf_batch32_c`), each with successful compile exit code. The report ties the production TU to the source hash reviewed here. I reviewed, but did not rerun, the recorded compile and differential commands.

## Limits and next action

Open limits include real method-table contents and valid handler-ID domain, callback semantics/side effects, work-object bounds and pointer validity, the meaning of state-2 result `2`, actual H2 edit/exit behavior, persistence/scheduling, and Azahar execution. The offline results do not establish whole-game equivalence. Keep the source-level reconstruction as bounded synthetic-handler evidence; before promoting it as H2 behavior, obtain justified real caller/script evidence and a supported integrated image plus the assigned runtime comparison.
