# Independent review: `0x002B0188` manager resolver

## Decision

The resolver behavior is well supported for valid mapped manager tables and group IDs in the tested range. Its ARM ABI is a two-argument tail transfer: it selects the manager entry by group, leaves `r1` (the raw node index) intact, loads the selected entry into `r0`, and branches to `0x00138B90` without changing LR. That helper handles a null entry as a null return; for non-null entries it returns `base + trunc_signed(index/1000)*32`, using the original pinned ARM body.

The direct report covers the signed boundaries, null entries, seven directed groups, seeded indices, ABI-visible state, and two targeted mutations. The refreshed `0x002B88C4` composition then executes original `0x002BF6D0` and original `0x00138B90` with the compiled manager resolver installed, and records both resolver inputs. That is meaningful offline composition evidence, but the table and manager entries are synthetic fixtures and there is no runtime or natural scheduler scenario.

One report/record consistency issue needs correction: `report.json` says `byte_identical:false`, but that flag compares the temporary-address body. The report separately hashes the final-address body, and I independently relocated the existing `candidate-final.o` and found its 24 bytes exactly equal the pinned original 24-byte span. The configuration ledger already labels `0x002B0188` `matching`; the function record's statement that it remains `non_matching` is stale/inaccurate. The final-address identity claim should be the basis for classification.

## Frozen packet and artifacts

All 14 run001 `input_sha256` entries exist and match. The pinned image is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. Source SHA-256 values match the packet and reports: manager resolver `a8c8cd0f8914acc5e4638206ebb56b39cb8412d21e86cd6fc446a21039a9a6ec`, touch caller `f47e857eeba6f823046feb42821b0a2d85eb7cdac4073b6e0e456fdfefc58eb0`, and resolver `0x002BF6D0` TU `4302f6f6c9069e23bb24c9190ae64e8e98b265056cef08bfcb3df19bbbe20405`.

Direct resolver report SHA-256: `4e8e0afde7de748adc0b29665e794913e22ad5293499d995cee8cb84cc33ced0`. Refreshed touch composition report SHA-256: `87218489bf044b3a2a3f5e10219a78a9e839af9f4e5b5babb03bc6f512bb9a59`. I parsed both reports and inspected the already-existing candidate object; I did not compile, run either runner, or launch an emulator.

## Original instruction contract

The pinned ARM at `0x002B0188` is 24 bytes:

- `ldr r2, [pc, #0xC]` obtains the literal `0x0044EA28`;
- `add r0, r0, r0, lsl #1` forms `group*3`;
- `ldr r2, [r2]` loads the table pointer from `0x0044EA28`;
- `ldr r0, [r2, r0, lsl #3]` reads the first word at `table + group*24`;
- `b 0x00138B90` tail-calls with `r0=manager_entry` and original `r1=node_index`.

C++ expresses the same table-pointer load, 24-byte group stride and selected first word, then calls `func_00138b90(manager_entry,node_index)`. The compiled relocation is `R_ARM_JUMP24` at offset `0x10`, so this compiles to a tail branch and preserves the caller's LR. It fits the 24-byte slot. `r0-r1` are the two inputs; `r2` is caller-saved scratch; `r4-r11` and SP are preserved. The direct report exercises the pinned original `0x00138B90` tail target in all 261 original/temp/final comparisons.

That helper first checks `r0==0` and returns zero without dereferencing. Otherwise it loads the manager base at `[r0]`; `SMULL` with the pinned reciprocal constant, arithmetic shift and sign correction compute signed quotient truncating toward zero by 1000; `base + (quotient << 5)` supplies the 32-byte row stride with 32-bit ARM wraparound. The candidate resolver itself does not null-check the table pointer, validate group range, or validate a non-null entry. A null table or out-of-range group may fault. Null *manager entries* are tested and handled by the original tail helper.

## Direct report coverage

The 261 cases consist of 133 directed combinations (19 directed signed indices across groups `0,1,2,3,7,19,31`), 32 null manager entries (groups 0 through 31 with index 1234), and 96 seeded `u32` indices/groups. Directed inputs include negative multiples and adjacent values, `INT_MIN`, `INT_MAX`, and raw unsigned spellings of negative values. Checks include return vs signed quotient reference, tail args, `r4-r11`, SP, no writes, completion, and faults. The `group*24 -> group*20` and forwarded-index mutations are reported detected.

This is good evidence for quotient boundaries, stride, and register forwarding. It does not cover all 32-bit groups or table wraparound, invalid/unmapped tables, unreadable non-null entries, concurrent table mutation, or the natural state/lifetime of manager objects. It relies on the original pinned `0x00138B90`; that implementation's tested behavior is not reconstructed here.

## Refreshed `0x002B88C4` composition

The current 58-case report binds the manager source SHA and compiled 24-byte final body. The composition installs compiled `0x002B0188` at its final address; original `0x002BF6D0` forwards both arguments, and original `0x00138B90` executes. The fixture makes the manager table at `0x0044EA28` select a manager entry whose base is chosen so node index `0x572` resolves through the original helper to the intended manager; that manager then points to the synthetic node table and touch records. The report checks that `(group,node)` reach the resolver and compares caller return, record array/count, ABI state, and ordered write trace for the two touch-region forms and count cases. Capacity and flag-mask mutations remain detected.

It does not mock `0x002B0188` in this refreshed profile; it does mock the surrounding memory contents via controlled table, entry and manager fixtures. Thus it validates helper composition more strongly than the earlier stubbed profile while not establishing real table/global contents, live manager lifetime, natural outer caller reachability, touch input scheduling, or runtime behavior.

## Exact-identity discrepancy and recommendation

The direct resolver report has `body_sha256=a09fdc...` for the temporary-address body and `final_body_sha256=56f6bdb...` for the final body. Its `byte_identical` expression compares `temp` to the original span, which is not the final-address body. From the existing `candidate-final.o`, I applied its one final `R_ARM_JUMP24` relocation at `0x002B0188` to `0x00138B90`; patched bytes hash to `56f6bdb962a3bb0bb33d94e47d63956aa0ee5eaa45d40e27d9deaf2f2e34513d`, exactly the pinned original span hash, and the 24-byte sequences are equal. The function ledger row is `matching`. Therefore the function record phrase “ledger remains non_matching because its bytes differ” conflicts with the final body and ledger and should not be used as evidence; the report should distinguish temporary-body byte identity from final-body identity.

Recommendation: accept the resolver's bounded behavior and the refreshed 58-case composition. Preserve limits for valid groups/mapped table and manager records, original `0x00138B90`, synthetic fixture state, and no runtime. Treat `0x002B0188` as byte-matching at final address based on the final relocation/body, and reconcile the stale function-record wording/report boolean before using it as a status summary.

## Run002 follow-up — final-address identity correction (2026-11-02)

The refreshed run002 packet has 14 declared inputs; all exist and match their pinned hashes. The manager report now separates `temporary_byte_identical:false` from `final_byte_identical:true`, with the final body SHA-256 `56f6bdb962a3bb0bb33d94e47d63956aa0ee5eaa45d40e27d9deaf2f2e34513d`. I re-applied the `R_ARM_JUMP24` relocation in the existing final object and independently confirmed its 24 bytes equal the pinned `0x002B0188` original span. The revised function record now correctly says final identity matches and ledger status is `matching`; the earlier report/record inconsistency is resolved.

The refreshed composed report remains pinned at SHA-256 `87218489bf044b3a2a3f5e10219a78a9e839af9f4e5b5babb03bc6f512bb9a59` and still describes 58 cases with original `0x002BF6D0` and `0x00138B90` executing, and compiled `0x002B0188` installed in the final profile. The original bounded recommendation stands: valid fixture/table domain and offline composition support the resolver; synthetic manager-table state, dependency `0x00138B90`, outer caller/scheduler lifecycle and runtime are not generalized by these tests. No compilation, runner, build or emulator was run for this follow-up.
