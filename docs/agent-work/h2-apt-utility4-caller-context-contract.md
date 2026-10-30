# H2 APT utility-4: observed caller context contract

## Static path

The ledger places `engine_func_00103e4c` at `[0x00103E4C,0x00103EF8)` (172 bytes). Its code starts with `push {r4,r5,r6,lr}`, sets `r4=1`, makes setup calls to `0x002C541C` twice and `0x002C3B00`, then loads `r5=0x00465198`, stores byte `1` at `[r5]`, and calls `0x002C5624` at `0x00103E80`. The dynamic LR observed at the APT entry was `0x00103E84`, matching this call's return address.

The bridge at `0x002C5624` is 28 bytes. It compares incoming `r0` with zero, loads `r0=0x0044E3B0` from the literal at `0x002C5640`, sets `r1=1`, and stores one byte at that global. The conditional branch at `0x002C5634` uses the comparison flags: zero input returns through `BX LR` at `0x002C563C`; nonzero input takes the unconditional tail `B` at `0x002C5638` to `0x002C0EFC`. The caller sets `r0=1` before calling the bridge, so that branch reaches the APT entry in this path. The previously observed entry LR `0x00103E84` and tail-step capture agree with this static route for that execution.

After return, the caller continues at `0x00103E84`, sets `r0=1`, stores byte one at `[r5+1]`, and calls `0x002C4244` with `r5+4` and `r5+0xC`. It then invokes helpers at `0x00110030`, `0x0011001C`, `0x00110744`, and `0x002C57B4`. A nonzero return from `0x002C57B4` sets the final result to zero. Otherwise it calls `0x002C57A4`; a nonzero result also sets zero. If both readiness helpers return zero, it returns one. The epilogue at `0x00103EDC` restores `r4-r6` and returns. The wrapper result from APT is overwritten by `mov r0,#1` in the continuation; the entry's raw wrapper-return contract is established by separate direct-entry tests, not this caller's final result.

## Evidence and boundary

An offline Unicorn comparison executes this entire caller body and the original bridge, while using controlled hooks for the original APT wrapper and the other listed helpers. It observed `LR=0x00103E84` and bridge-loaded `r0=0x0044E3B0` at candidate entry. It covers the two primary readiness branches and arbitrary wrapper return values against both the pinned original and reviewed composed H2 image. The current result is 40 cases passed per base image; exact hashes and limitations are in `docs/agent-work/h2-apt-utility4-observed-caller-context.md` and its run report.

This recovers the local caller/bridge contract for the tested route, not the full behavior of their untyped dependencies. In particular, helper side effects and service behavior are controlled or unresolved; other callers, indirect or Thumb paths, and runtime integration remain separate evidence requirements. The LR observation is one dynamic sample, not a complete trace of every invocation.
