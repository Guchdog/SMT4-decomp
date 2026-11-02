# Independent review: typed resource resolver `0x002B96F0`

## Recommendation

The typed resolver is supported for the controlled raw-address fixtures and the paired `TitleConfig_Calc` call slice in the pinned report. The final-VMA object has a single absolute ARM `JUMP24` relocation at offset `0x10`; rebasing its branch to `0x00145798` reproduces the original 24-byte slot exactly. The 103 reported resolver cases and both negative controls support the stated group/table arithmetic, second-index forwarding, register/stack preservation, ordered reads and no writes. Runtime is not established.

## Pinned identities and relocation audit

All 14 packet inputs match their recorded SHA-256 values. Key hashes: original `code.bin` `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; source `src/engine/leaf_batch39_a.cpp` `a84ae4ecb6fdde99b45ffd273cc79aa683894de3f8686626678bca5f0a7a132e`; final build object `build/h2-resource-resolver-full/engine/leaf_batch39_a.o` `5baa77fd34ff92ca118926fe2165a8a36a1632ad6cf8ae015d0f91bb43bb6b8d`; report `1de074973983e86cf4c719eb0d983514c0e7da38f45453edc449b931755ee40a`.

I independently extracted the object function body and its relocation and applied the ARM branch rebase at final VA `0x002B96F0`. The 24-byte body contains exactly one `R_ARM_JUMP24` relocation (type 29) at offset `0x10`, with no symbol and no explicit addend. The instruction is an ARM unconditional `B`, so LR is preserved. Its place is `0x002B9700`; PC is `0x002B9708`; target `0x00145798` gives displacement `-1,523,568` bytes (word displacement `-380,892`) and relocated instruction `0xEAFA3024`. Decoding that instruction yields `0x00145798`.

Rebased bytes are `0c209fe5800080e0002092e5800192e72430faea28ea4400`, exactly equal to the original image slot at `0x002B96F0`. Both final and original span SHA-256 are `02cf845b4b0a1b44a1806fcbd3f528b001a84ed79acf464543b5607d41e6f5bf`. The temporary body differs due to its distinct placement; the final-VMA identity is the relevant placement result.

## Contract and bounded differential

The C++ body reads the table pointer at `0x0044EA28`, loads the 32-bit manager entry at `table + group * 24`, then tail-branches to `0x00145798` with `subindex` still in `r1`. The original helper at `0x00145798` remains in use: it checks `r0`, loads the first word of a non-null manager, adds `(r1 << 5)`, and returns via `bx lr`. Thus the candidate does not replace that tail helper or independently validate arbitrary pointers.

The report covers 103 cases: 7 directed cases plus 96 seeded cases (`Random(0x2B96F0)`). Directed cases include the null table entry, the H2 `(group=0x2F, subindex=0)` input, group stride differentiation, large/wrapping raw indices and bases. The reported comparison includes the ordered reads, return value, `r1`, callee-saved registers, SP, completion/fault state and no writes. Both controls were detected: changing group stride 24 to 32 and forwarding the group instead of the second index. The second-index mutant is rejected because it no longer fits the function span, a structural rejection rather than a semantic counterexample.

The ABI is a two-argument raw `u32` interface. The tested body preserves `r1`, `r4-r11` and SP, makes no stores, and leaves the tail helper responsible for the final record computation. Null manager entry returns zero through that helper. These controlled Unicorn fixtures do not establish behavior for arbitrary invalid non-null pointers, unmapped table state, concurrency or every caller's surrounding assumptions.

## Paired caller composition and limits

The report composes final-VMA resolver bytes with the typed predicate in the actual `TitleConfig_Calc` call slice. For flags `0`, `4`, and `0xFFFFFFFF`, the paired return/zero-flag results are `(0,true)`, `(1,false)`, and `(1,false)`, matching the original slice. This is bounded call-slice evidence, not a natural runtime audio-settings scenario or whole-image equivalence. The report marks runtime `not_run`.

I did not compile, rerun the differential, or launch an emulator; this review independently recomputed the pinned hashes and relocation/body identity, and statically inspected the candidate, runner and report.
