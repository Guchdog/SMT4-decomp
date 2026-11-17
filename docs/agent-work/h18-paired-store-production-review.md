# Independent review: production paired store `0x00131414`

## Recommendation

The recovered machine contract and bounded ARM/Unicorn evidence are strong for the observed parser caller: store `a` at `p+4`, store `b` at `p+8`, and return `p+4`. The ABI and truthful `non_matching` ledger label are correct. **Request a small source correction before accepting the production C++ as standards-safe.** `fields[1]` performs typed `u32*` pointer arithmetic from the `data` member into the adjacent `chunk` member; those two members are not an array. The emitted ARM code works on the tested compiler/target, but the source expression has a C++ object-model issue that the machine-level differential cannot detect.

## Frozen source, declarations and layout

All hashes in the prepared packet matched, including production source, header, parser TU, tests, reports and producer handoff. The public declaration and definition are C linkage and agree on `u8* ui_func_00131414(u8*,u32,u32)`. The parser alias declaration also returns `u8*` and takes the three matching parameters. Its caller casts the actual `AsdFontParseState*` to `u8*`, passes the resource base and found chunk address, then ignores the helper's return and sets the parser result to `1`.

`AsdFontParseState` is a three-word structure with `u32 data` at `+4` and `u32 chunk` at `+8`; compile-time `offsetof` and size assertions confirm offsets 0/4/8 and size 12. This is good evidence that the concrete caller points into a live, aligned structure with two real `u32` subobjects. An aligned ARM BL scan over the pinned image found the one direct call at `0x00121d1c` in `ui_func_00121b80`; this does not exclude indirect, Thumb or computed references.

The source currently does:

```cpp
u32* fields = reinterpret_cast<u32*>(p + 4);
fields[0] = a;
fields[1] = b;
return p + 4;
```

At the actual parser call, `fields` points at the `data` member. `fields[1]` computes `fields + 1` and dereferences it to reach the adjacent `chunk` member. C++ pointer arithmetic permits a non-array object to be treated as a one-element array for this purpose; incrementing to its one-past pointer and dereferencing it is outside that object. The adjacent `chunk` member is a distinct object, not an element in an array with `data`. See the [C++ working draft rule for additive/pointer arithmetic](https://eel.is/c++draft/expr.add). The `u8*` byte offsets themselves are reasonable for accessing the structure's object representation; the specific concern is indexing through a `u32*` across separate scalar members. A narrow repair is to address each word independently at `p+4` and `p+8` (or write those actual named struct members through a shared struct type); `memcpy` to each byte offset is another standards-safe option. Then rerun the production-symbol and caller evidence because code generation and memory behavior are integration inputs.

## Ledger, emitted code and differential evidence

The original 12-byte bytes are `040080e2060080e81eff2fe1` (`add r0,r0,#4; stm r0,{r1,r2}; bx lr`). The production object emits `060080e9040080e21eff2fe1` (`stmib r0,{r1,r2}; add r0,r0,#4; bx lr`), also 12 bytes but non-identical. The ledger row is correctly classified `non_matching` and preserves the original address/span.

Both frozen production-run reports pass 260 cases: four directed pairs include all-zero, max values and signed-boundary values, followed by 256 randomized pairs. They compare full `r0-r12`, SP/LR/PC/CPSR, mapped data and stack snapshots, write addresses, and the continuation. The single `second_store_xor_1` negative control is detected in both reports. No independent compilation or rerun was performed in this review (compiler budget 0).

The real caller window starts at `0x00121d14`, executes the argument setup and BL at `0x00121d1c`, then returns success at `0x00121d20`, stopping at `0x00121d24`. The helper's returned pointer is not consumed by this caller, but the return register remains covered in isolated differential cases and the declaration preserves the ABI. The caller test uses representative prepared state, not the full parser/resource loader. There is no emulator or runtime evidence.

## Domain and next action

The differential domain is non-null, four-byte-aligned pointers to at least 12 writable bytes in ordinary RAM. It excludes MMIO, misalignment, invalid pointers, concurrent observation and partial-fault ordering. This exclusion matters because original code adjusts `r0` before its stores, whereas emitted code adjusts `r0` after `STMIB`; if a store faults, the register/fault-order behavior could differ. Within the tested all-writable domain, stores and return agree.

**Next step:** replace the cross-member `u32*` indexing with two independent typed-address stores or a safe byte-copy implementation; update the source-contract test if its pattern changes, recompile the production TU, and rerun both seeds plus the caller window. Keep the ledger `non_matching`. The existing parser struct and caller provide a suitable typed contract for these fields; no broader generic-byte-buffer lifetime claim is established here.
