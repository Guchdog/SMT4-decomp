# Independent review: TitleConfig sprite-group binder `0x002C32F8`

## Result

The fresh run supports the typed candidate for the exercised ordinary-RAM domain. With seed `20261219` and 64 randomized cases, all 67 direct comparisons passed; the exact TitleConfig init/bind caller slice passed; and the negative control removing the count halfword store was detected. The original and candidate both return raw `r0 = group + 0x14`. The candidate fills the 76-byte slot exactly and has no relocations. The ledger currently classifies the differing body as `non_matching`.

## Pinned body and ABI audit

I independently disassembled `[0x002C32F8,0x002C3344)` from the pinned image `extracted/exefs/code.bin`, SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. The 76-byte body hash is `61fe68830fbcd96e81c849f122c0d39d24cb8182fcf6f4fcaa3437ec653364bb`.

The entry ABI is `r0=group`, `r1=table`, `r2=count`, `r3=reg_word`, and seven raw 32-bit stack words at entry `[sp]` through `[sp+0x18]`. The original saves `r4-r6`; after the push, it loads stack words 0, 2, 4, and 6 into GPRs for halfword writes, and loads words 1, 3, and 5 into `s0-s2` only to store those raw bits back as words. It writes the low halfwords of count/stack words to `+0,+2,+4,+6,+8`, then table and `reg_word` at `+0x0C,+0x10`, then the final three stack-word payloads at `+0x14,+0x18,+0x1C`. The two bytes `+0x0A..+0x0B` are not addressed. The writeback stores and final add leave `r0=group+0x14` at return. `r4-r6` and SP are restored; `r7-r11` are not modified. The routine makes no calls and does not modify condition flags.

The candidate signature has the same first four register words and seven additional `u32` words on the stack. It uses halfword casts for the five truncated fields and word stores for the remaining five values, and returns the same address. It has no relocation. The runner checks preserved `r4-r11`, `d8-d15`, final SP, return, full 0x20-byte group, and fault state.

## Actual TitleConfig caller

The pinned caller slice `0x002F4D34..0x002F4D6C` calls the original group initializer `0x002C3344`, then prepares `r1=0x00407EC6`, `r2=0x18`, `r3=0`, and seven zero stack words before calling the binder at `0x002C32F8`. The exact caller slice passed on both original and staged images. Its final descriptor bytes were `180000000000000000000000c67e400000000000000000000000000000000000`; this represents count `0x18`, the untouched/zero gap and other zero fields, and table word `0x00407EC6`. The caller receives `group+0x14`; no resource table contents or visual result are established here.

## Fresh differential and staging evidence

Command:

```text
python tools/h2_2c32f8_group_bind_experiment.py --out build/agent-work/H2-semantic/h2-titleconfig-sprite-group-bind-002c32f8-review/run001/checks/review-seed-20261219 --seed 20261219 --random-cases 64
```

Exit code: 0. Report: `build/agent-work/H2-semantic/h2-titleconfig-sprite-group-bind-002c32f8-review/run001/checks/review-seed-20261219/report.json`, SHA-256 `f58bc473d3b22732cf3b8c3a91b8591df80b62043c70cb0784ac3af1a78ab451`. It records candidate body SHA-256 `2f2e086d0cb0979950f0d99f5b49fb67117139e584c620bf72eb0abed9642723`, 76/76 bytes, no relocations, 67/67 direct cases, caller pass, and the detected count-store control. The direct fixtures include three directed raw/truncation/padding cases plus 64 seeded cases; the independent expected-descriptor calculation passed throughout.

The candidate IPS SHA-256 is `441a4a6247c277995a83c16ebad6d1fa71ba17340c04806b4fff9676e3dfb160`. Independent application of the IPS reproduced the staged image exactly. The IPS addresses only the 76-byte slot `[0x002C32F8,0x002C3344)`; 55 bytes differ from the original. The target ledger row is `0x002c32f8,76,non_matching,...`, which is appropriate because candidate bytes differ.

## Store-order limitation and remaining scope

The compiled candidate reorders independent stores: it writes the table/word fields before the halfword fields, whereas the original writes the halfwords first. The differential compares final group bytes and does not capture/compare access order. The candidate leaves `+0x0A..+0x0B` unchanged, including poisoned gap bytes in direct cases. Therefore this is evidence for aligned ordinary writable RAM without MMIO or concurrent observers; it does not establish write-order equivalence for side-effecting memory.

The TitleConfig caller uses seven zero payload words. Direct cases exercise raw bit patterns, but this does not establish the meaning or validity of the resource table, visible rendering, physical UI behavior, pointer-fault behavior, scheduling, or complete H2 runtime. No full build or emulator was run.

## Recommendation

Accept as bounded independent offline evidence for the descriptor binder and exact TitleConfig caller setup. Preserve the `non_matching` ledger label and the write-order/domain limits; do not infer table contents or rendering behavior.
