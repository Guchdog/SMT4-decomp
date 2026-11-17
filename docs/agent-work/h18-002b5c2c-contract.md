# Contract recon: 0x002b5c2c

## Identity, ISA and boundaries

The ledger entry is `0x002b5c2c,20,matching,ui,ui_func_002b5c2c,src/engine/leaf_batch39_a.cpp`. The wrapper stores raw halfwords and annotates `.arm`, but these bytes form a valid Thumb routine, and every discovered code reference uses ARM `BLX` immediate, which switches to Thumb. The stock `split_asm.py --addr 0x002b5c2c` output is therefore misleading ARM decoding; the byte stream was decoded manually as Thumb. Input code SHA-256 is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.

Thumb body: `0x002b5c2c..0x002b5c3d`, with `bx lr` at `0x002b5c3c`. The remaining halfword `0xffff` at `0x002b5c3e` is trailing data/padding within the 20-byte catalog span. No stack frame is created and no callee-saved registers are touched.

## Recovered contract (facts)

The helper takes a pointer in `r0`; incoming `r1-r3` and stack arguments are unused. It initializes `r1=0`, then repeatedly loads an unsigned 16-bit halfword from `[r0]`. If that value is nonzero, it increments `r1`, advances `r0` by two bytes and repeats. On the first zero halfword it returns `r1` in `r0` (`mov r0,r1` / Thumb `lsls r0,r1,#0`) and executes `bx lr`.

Equivalent bounded-domain C++:

```cpp
uint32_t count_nonzero_u16(const uint16_t* p) {
    uint32_t count = 0;
    while (*p++ != 0) {
        ++count;
    }
    return count;
}
```

The function performs reads only, one halfword per element including the terminating zero. It has no global/helper dependencies. The loop updates APSR flags, but these flags are caller-clobbered under the observed ABI. For valid, aligned, readable, zero-terminated halfword sequences shorter than `UINT32_MAX`, return equals the count of nonzero 16-bit elements, excluding the terminator. Input is not modified. The machine counter wraps at 32 bits and pointer arithmetic is machine-width; malformed/unbounded inputs are outside the supported C++ domain and cannot be made safe from these bytes alone.

## Direct callers and use

An aligned ARM BLX-immediate scan over `code.bin` (base `0x00100000`) found 15 call sites; an aligned pointer-word scan found none for `0x002b5c2c` or `0x002b5c2d`. The complete direct call-site set, matched to catalog owner rows, is:

- `0x0021f504` — `engine_func_0021f480`: input `r5`; doubles returned count (`lsl #1`) before passing a byte-size/offset value to `engine_func_00359c9c`.
- `0x0023495c` — `engine_func_0023494c`: input saved from its `r1`; treats zero specially, otherwise forwards count into `engine_func_002c3b48` as a size-like argument.
- `0x002a8868` — `ui_func_002a882c`: input `r4`; computes `(count+1)*2`, accounting for a terminator in a halfword buffer before later copy/setup calls.
- `0x002adadc` — `ui_func_002ada98`: listed by static scan; caller context artifact is included under `run-001/disasm`.
- `0x002bb930` — `engine_func_002bb8e4`: input held in `r5`; computes `(count+1)*2` and stores the resulting size for a subsequent helper.
- `0x002e0e0c` — `engine_func_002e0dd0`: input is original entry `r2` (`r6`); doubles count and forwards it as `r3` to `0x00248e58` with key `0x6e`.
- `0x003104a8` — `engine_func_00310448`: uses the returned count in constructing a size/offset for a later operation.
- `0x003529f0` — `ui_func_00352974`: computes `(count+1)*2`, stores the size with a local buffer descriptor and proceeds to copy/setup.
- `0x00352b80` — `ui_func_00352b30`: same `(count+1)*2` size pattern.
- `0x00356028` — `engine_func_00355fe0`: same `(count+1)*2` size pattern.
- `0x0035c340` — `ui_func_0035c32c`: passes input `r2`; stores original pointer and returned count into a two-word output structure.
- `0x0038c7c8` and `0x0038c840` — `script_vm_func_0038c43c`: use the return as loop/length bounds while traversing halfword elements.
- `0x0038da94` and `0x0038db04` — `script_vm_func_0038d7b0`: analogous paired calls for script VM strings/sequences.

These call patterns independently support “count nonzero halfwords until zero,” especially the repeated `(count+1)*2` conversions and the script loops over halfword elements. The helper's return is not a global-dependent arithmetic result: it depends on memory contents at the input pointer.

Static scan limitations: only aligned words decoded as ARM branch instructions were used to find BLX immediate calls; the caller scan can miss Thumb-origin calls, indirect/computed dispatch, and data-driven references. All listed hits are ARM BLX immediate instructions. Function owner names came from pinned `config/functions.csv`; caller disassemblies were generated from the pinned code image.

## Caller `0x002e0dd0` interpretation

At `0x002e0e0c`, `0x002e0dd0` passes its original `r2` pointer to this helper. It doubles the returned element count and passes that byte count as `r3` to `0x00248e58`, with object field in `r0`, key `0x6e` in `r1`, and the original pointer in `r2`. This makes the observed argument tuple coherent as pointer plus byte length. The `0x002e0dd0` result itself remains 0/5 according to the separate `0x00263534` bit31 gate; `0x002b5c2c` is only reached on the gate's clear-bit path. The helper does not alter that return contract.

## Bounded implementation and validation plan

A direct typed C++ replacement is well supported for the bounded domain of a non-null, halfword-aligned, readable zero-terminated sequence. Prefer `const uint16_t*` plus `uint32_t` count, with no global or helper interface. Focused offline differential cases should cover empty input, lengths 1 and several, embedded nonzero values across low/high-bit ranges, and caller-side byte-size uses (`count*2`, `(count+1)*2`). Negative controls should detect byte-wise scanning, including the terminator, counting code units with a different zero rule, and stopping at the first nonzero. No compile, differential, runtime, or emulator validation was run for this static recon.

## Provenance

The report is `docs/agent-work/h18-002b5c2c-contract.md`. The raw helper wrapper is in pinned `src/engine/leaf_batch39_a.cpp`; caller rows were found from aligned BLX scan and mapped with pinned `config/functions.csv`. No production C++, ledger, runner, or shared interface was changed. Caller disassembly artifacts reside under `build/agent-work/batch-h18-001/h18-contract-002b5c2c/run-001/disasm`.
