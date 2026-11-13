# Contract recon: `script_vm_func_002a72fc` (0x002a72fc)

## Identity

- Original span: `[0x002A72FC, 0x002A7540)`, 580 bytes, ARM.
- Source: `src/engine/leaf_batch45_a.cpp` (currently naked/raw).
- Category: `script_vm`.
- Reference: `extracted/exefs/code.bin`.

## ABI

- Entered with `r0 = ctx` (large script/system context; saved as `r5`).
- Returns `u32 = 1`.
- Preserves `r4-r8, sb, sl, lr`; stack adjustment is only the prologue/epilogue
  (`push {r4-r8,sb,sl,lr}`), no local frame.
- Tail/cleanup function: it releases owned resources and clears the pointers.

## Behavior (ordered)

1. `0x2A7BD4(ctx)`.
2. For `i = 0..3`:
   - `p = ctx + 0x28C + 4*i`
   - if `*p != 0`: `0x2A7B50(*p)`, then `*p = 0`.
3. `0x2AEB2C(0x31, 0)`.
4. `0x2AEA7C(0x31)`.
5. `0x2A4974(ctx+0x20)`.
6. `0x14C968(ctx+0x20)`.
7. `0x14C970(ctx+0x20)`.
8. If `ctx[0xFAC] != 0`:
   - `0x2A4EF0(ctx[0xFAC])`
   - `0x2B2520(ctx[0xFAC])` (the ARM adds and subtracts `0x400+0xCC`
     immediately, so the argument is the original pointer)
   - `ctx[0xFAC] = 0`.
9. If `ctx[0xFB8] != 0`:
   - `0x152AF8(ctx[0xFB8])`
   - `0x2A7AA0(ctx[0xFB8])`
   - `ctx[0xFB8] = 0`
   - `0x2A7604(0)`.
10. For `i = 0..5`:
    - `a = ctx + 0xD10 + 4*i`; if `*a != 0`: `0x152AF8(*a)`,
      `0x2A7AA0(*a)`, `*a = 0`.
    - `b = ctx + 0xD28 + 4*i`; if `*b != 0`: `0x152AF8(*b)`,
      `0x2A7AA0(*b)`, `*b = 0`.
11. Individual pointer cleanup, each only when nonzero, clearing the field:
    - `0x5A8 -> 0x2A755C`
    - `0x5A0 -> 0x2C4360`
    - `0x5A4 -> 0x2C4360`
    - `0x5B4 -> 0x2A755C`
    - `0x5AC -> 0x2C4360`
    - `0x5B0 -> 0x2C4360`
    - `0x5C0 -> 0x2A755C`
    - `0x5B8 -> 0x2C4360`
    - `0x5BC -> 0x2C4360`
12. `0x2C0128()`.
13. Return `1`.

## Proposed C++

```cpp
extern "C" void engine_func_002a7bd4(void* ctx);
extern "C" void engine_func_002a7b50(void* p);
extern "C" void engine_func_002aeb2c(u32 a, u32 b);
extern "C" void engine_func_002aea7c(u32 a);
extern "C" void engine_func_002a4974(void* p);
extern "C" void engine_func_0014c968(void* p);
extern "C" void engine_func_0014c970(void* p);
extern "C" void engine_func_002a4ef0(void* p);
extern "C" void engine_func_002b2520(void* p);
extern "C" void engine_func_00152af8(void* p);
extern "C" void engine_func_002a7aa0(void* p);
extern "C" void engine_func_002a7604(u32 v);
extern "C" void engine_func_002a755c(void* p);
extern "C" void engine_func_002c4360(void* p);
extern "C" void engine_func_002c0128();

extern "C" __attribute__((noinline)) u32 script_vm_func_002a72fc(u8* ctx) {
    engine_func_002a7bd4(ctx);
    for (u32 i = 0; i < 4; ++i) {
        u32 off = 0x28C + 4 * i;
        void* p = *reinterpret_cast<void**>(ctx + off);
        if (p != nullptr) {
            engine_func_002a7b50(p);
            *reinterpret_cast<void**>(ctx + off) = nullptr;
        }
    }
    engine_func_002aeb2c(0x31, 0);
    engine_func_002aea7c(0x31);
    engine_func_002a4974(ctx + 0x20);
    engine_func_0014c968(ctx + 0x20);
    engine_func_0014c970(ctx + 0x20);
    if (*reinterpret_cast<void**>(ctx + 0xFAC) != nullptr) {
        engine_func_002a4ef0(*reinterpret_cast<void**>(ctx + 0xFAC));
        engine_func_002b2520(*reinterpret_cast<void**>(ctx + 0xFAC));
        *reinterpret_cast<void**>(ctx + 0xFAC) = nullptr;
    }
    if (*reinterpret_cast<void**>(ctx + 0xFB8) != nullptr) {
        engine_func_00152af8(*reinterpret_cast<void**>(ctx + 0xFB8));
        engine_func_002a7aa0(*reinterpret_cast<void**>(ctx + 0xFB8));
        *reinterpret_cast<void**>(ctx + 0xFB8) = nullptr;
        engine_func_002a7604(0);
    }
    for (u32 i = 0; i < 6; ++i) {
        u32 a = 0xD10 + 4 * i;
        u32 b = 0xD28 + 4 * i;
        if (*reinterpret_cast<void**>(ctx + a) != nullptr) {
            engine_func_00152af8(*reinterpret_cast<void**>(ctx + a));
            engine_func_002a7aa0(*reinterpret_cast<void**>(ctx + a));
            *reinterpret_cast<void**>(ctx + a) = nullptr;
        }
        if (*reinterpret_cast<void**>(ctx + b) != nullptr) {
            engine_func_00152af8(*reinterpret_cast<void**>(ctx + b));
            engine_func_002a7aa0(*reinterpret_cast<void**>(ctx + b));
            *reinterpret_cast<void**>(ctx + b) = nullptr;
        }
    }
    struct Cleanup { u32 off; void (*fn)(void*); };
    const Cleanup cleanups[] = {
        {0x5A8, engine_func_002a755c}, {0x5A0, engine_func_002c4360},
        {0x5A4, engine_func_002c4360}, {0x5B4, engine_func_002a755c},
        {0x5AC, engine_func_002c4360}, {0x5B0, engine_func_002c4360},
        {0x5C0, engine_func_002a755c}, {0x5B8, engine_func_002c4360},
        {0x5BC, engine_func_002c4360},
    };
    for (const Cleanup& c : cleanups) {
        void* p = *reinterpret_cast<void**>(ctx + c.off);
        if (p != nullptr) {
            c.fn(p);
            *reinterpret_cast<void**>(ctx + c.off) = nullptr;
        }
    }
    engine_func_002c0128();
    return 1;
}
```

The cleanup table must be emitted without a dynamic initializer; use a plain
`static constexpr` array of `{u32, function pointer}` in the final source if the
compiler accepts it in this freestanding TU. If function-pointer tables create
unwanted relocations, use explicit `if` blocks instead; behavior is identical.

## Differential plan

- Stub every direct call with a hook that logs `(name, r0..r3)` and has no
  memory side effects.
- Fixture: a 0x2000-byte `ctx` with all pointers initially zero; snapshot after
  the call.
- Cases:
  1. all fields zero (only the unconditional calls and return 1);
  2. each 0x28C loop slot individually nonzero, then all four nonzero;
  3. 0xFAC nonzero (both calls and clear);
  4. 0xFB8 nonzero (three calls, clear, `0x2A7604(0)`);
  5. each 0xD10/0xD28 loop slot individually nonzero and all six nonzero;
  6. each of the nine individual cleanup slots individually nonzero;
  7. all fields nonzero in one combined fixture.
- Compare: return, continuation PC, SP, `r4-r11`, ordered call log, and the full
  `ctx` snapshot. Add a negative control that changes one cleanup call target
  or skips one clear and verify the comparator detects it.
- Explicitly exclude: real destructor semantics of the called helpers, object
  lifetime, and runtime/emulator behavior.

## Limits

- The instance is presumed to be a live context; null/partial contexts are only
  covered where the branch explicitly tests the pointer.
- Helper effects are stubbed; no claim is made about what they free internally.
- The ARM's `add/sub 0x400+0xCC` around `0x2B2520` is treated as a no-op address
  recomputation; the differential must confirm the argument word.
