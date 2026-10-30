# H4 Navi divisor source review

## Result

The divisor-source recon is acceptable as a bounded static dependency map. I independently checked its entry, caller-side divides, initializer, bounded literal scan, and claims against the frozen packet. The 18 declared packet input hashes all matched. The pinned image is `extracted/exefs/code.bin`, SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; the recon report is pinned as `1a03adaad1b85f670e7143ee80b57be11bab40e0214bfeac5c20b3069fac71a3`.

## Accessor and initializer

Capstone ARM disassembly of `0x0039FA68` confirms the four-instruction body: `LDR r0,[pc,#8]` reads the literal at `0x0039FA78` (`0x0044CDF0`); `LDR r0,[r0]` loads the current host pointer; `VLDR s0,[r0,#0x34]` loads the raw 32-bit field into VFP `s0`; and `BX lr` returns. The helper does not use its incoming `r0` before overwriting it, and has no explicit stack operation, store, pointer/range check, or float-domain guard. Thus the report correctly states the raw accessor behavior and does not promise that the field is valid, finite, or nonzero. A null/unreadable global pointer or host and fault behavior are not tested or specified by this body.

At `0x00291CAC`, the straight-line initializer path calls allocator `0x002C4B84` with `r0=0x100`, `r1=0x100`, `r2=0`, `r3=0x12344`, and stack word `1`. It stores returned `r0` into `0x0044CDF0`, then writes literal `0x3F800000` (1.0f) to host+`0x34` at `0x00291D14`; the same sequence zeros host+`0x18`, `+0x38`, and `+0x3C`. This supports an initializer store conditional on reaching the path with a usable returned allocation. It does not guarantee initializer execution, object lifetime, absence of later writes, or any runtime divisor range. The recon states these limits appropriately.

The caller instructions independently confirm `0x0044CDC8` is loaded as a separate multiplier. The value from `0x0039FA68` is saved in `s16` and used as divisor at `0x0039CA64` and `0x0039CA7C`. The reviewed path contains no zero/finite test between accessor and those `VDIV` operations. This is static path evidence, not evidence that a particular runtime invocation took that branch or that the architecture's exceptional numeric behavior has been measured.

## Writer-scan and run-004 limits

I reproduced the recon's bounded aligned-word scan result: 43 occurrences of `0x0044CDF0` in `[0x00100000,0x003FE624)`. The recon's review of ledger functions containing those words is a useful direct-alias triage method, and it explicitly disclaims exhaustiveness and sole-writer proof. Other pointer derivations, indirect/Thumb paths, helpers, or code outside this scan can still access the field. No material overclaim found.

The paired run-004 records show the global slot address/pointer and four-byte snapshots at host+`0x30` and host+`0x38`; the callback object prefix begins at host+`0x40`. Those ranges do not include host+`0x34`. The observed return at `0x00399DAC` is after the `0x0039C944` call; the capture has no breakpoint at `0x0039FA68` or either divide site. Therefore it establishes neither the sampled divisor bits nor which internal divisor path executed. It cannot support 1.0f for that invocation or a general valid-domain claim. The recon describes this accurately.

## Recommendation and scope

Accept this recon for bounded dependency-recon use. Keep its unresolved items: alias/writer completeness, global-slot and host lifetime, allocator/null/fault behavior, divisor zero/negative-zero/NaN/infinity/boundary behavior, and FPSCR effects. Implementation or semantic equivalence would require further contract-specific evidence. No build, test, emulator, save access, or guest-memory write was performed.
