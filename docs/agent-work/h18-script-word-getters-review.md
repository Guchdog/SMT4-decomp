# Independent review: script word getters `0x002345f0` / `0x002345fc`

## Verdict

The machine candidates support the same value and machine state as the originals for aligned, side-effect-free ordinary RAM where both original halfword bytes are readable. That domain fits the synthetic tests and is plausible for the script VM caller, but is not established for every caller or a real runtime. The narrower read is a real contract difference: do not claim MMIO, read-width-sensitive, fault-boundary, or concurrently observed equivalence. Before promoting the C++ source, also resolve the typed `uint16_t*` alias/object-lifetime precondition or express the ordinary-RAM low-byte contract with a byte-safe access.

## Original and compiled candidate

The pinned image hash is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. Both 12-byte entries end in `bx lr`; each is an independent complete ARM leaf:

- `0x002345f0`: bytes `b804d0e1ff0000e21eff2fe1`, `ldrh r0,[r0,#0x48]; and r0,r0,#0xff; bx lr`.
- `0x002345fc`: bytes `ba04d0e1ff0000e21eff2fe1`, `ldrh r0,[r0,#0x4a]; and r0,r0,#0xff; bx lr`.

The return is the unsigned low byte of the addressed halfword, zero-extended in `r0`. On this little-endian ARM target the low byte is at the halfword's first address. The frozen source uses `uint16_t` loads and `& 0xffu`; the verified Clang 23.1.3 ARMv6K objects emit:

```text
candidate_002345f0: ldrb r0, [r0, #0x48]; bx lr
candidate_002345fc: ldrb r0, [r0, #0x4a]; bx lr
```

The 8-byte symbol hashes are `5dac101bc7f2f36db7218703716d78bc3787e02d26c6a86cffa02fb836445d10` and `625a82d0921c23382b989586102834aa8cb97e995ce4bb16e9698edc793a89fe`. The object SHA256 is `6fec789a305042b3f3ed7e4a202b4f1d692d2b94c5eb40111196a6d173babeba` in both seeds, and its extraction metadata records identical compiler, flags, and dependencies. The candidate intentionally changes the read width and is not byte-identical.

## Differential and controls

Both frozen reports pass. Each seed tests both functions with 16 directed halfword values (including `0x00ff`, `0x0100`, `0x7fff`, `0x8000`, `0xff00`, `0xffff`) and 8 seeded values: 24 cases per address per seed. Comparisons cover `r0-r12`, SP, LR, PC, NZCV, memory and writes. Wrong-offset, signed-extension, omitted-mask, and memory-write controls were each detected. Report hashes: seed 7 `8e1dd5ec608674551b94773d1c874f607d921f6a8b113cfcbe1023c87ff1a334`; seed 20261024 `80ea538234f020ac491f3511c9d929ae6304e39331ae372e780619f4474c4a81`.

Read footprints are explicitly **not** equalized as an acceptance claim. The runner replaces the original read set with the candidate read set for its RAM comparison, while saving both actual sets. Reports show original reads at `p+0x48` and `p+0x49` versus candidate read only at `p+0x48`; likewise `p+0x4a/+0x4b` versus only `p+0x4a`. That is appropriate for side-effect-free ordinary RAM, but means these passes do not prove access-width equivalence. With an inaccessible second byte, a faulting halfword read, MMIO side effects, races, or a concurrent observer, behavior may differ. Those paths are outside the exercised contract.

## Caller evidence

Aligned ARM `BL` scanning reports 16 direct call sites per target across the same four script VM caller functions; the reports preserve the full inventories. Only two adjacent sites in `script_vm_func_0038c43c` are executed as caller windows, once per seed:

- `0x0038c5e4`: `add r0,sl,#0x28`; call `0x002345fc` at `0x0038c5e8`; `mov r4,r0` at `0x0038c5ec` consumes the value.
- `0x0038c5f0`: `add r0,sl,#0x28`; call `0x002345f0` at `0x0038c5f4`; `mov r2,r0` at `0x0038c5f8` consumes the value.

Each window passes one directed case per seed, including the consumer instruction. Reports explicitly record the differing reads. The harness sets `sl` to an aligned Unicorn RAM address and populates the two requested halfwords with distinct low-byte results. It does not run the full caller or game script. The 16-site scan is aligned ARM immediate-BL only; it does not cover indirect/computed or Thumb callers, and only this one paired sequence was composed dynamically.

## C++ and integration conditions

The production signatures already return `u32` and accept `const u8*`, matching the experiment's external ABI. The source's dereference through `reinterpret_cast<const uint16_t*>` still assumes a valid suitably aligned `uint16_t` object at the address. The runner proves emitted ARM behavior, not C++ object lifetime or aliasing safety for arbitrary byte-backed script records. For a general `const u8*` contract, a byte access that directly returns `p[offset]` is the clearer alias-safe expression of the tested ordinary-RAM behavior; alternatively recover the actual script record type and establish these offsets as real `uint16_t` fields. Preserve any documented read-width requirement if later callers show MMIO or other observable memory.

Current source remains the original inline-assembly body and both ledger entries remain `matching` for the exact 12-byte original. If promoting the 8-byte implementation, change the ledger to a supported non-matching classification and retain this semantic record; never mark the changed bytes matching. Then validate the actual four caller functions or their relevant compositions and the defined runtime scenario. Unaligned pointers, invalid/unmapped inputs, MMIO, races, exceptions, and game runtime have not been tested.
