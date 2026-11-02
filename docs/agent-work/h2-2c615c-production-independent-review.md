# Independent production review: `0x002C615C` — run001

## Recommendation

The run005 rerun independently supports the standalone production trampoline for the tested H1 interpolation domain. The `u64` ARM return correctly expresses quotient in `r0` and remainder in `r1`; zero divisor yields `r0=0`, `r1=numerator`. The production body is 164 bytes with no relocations. Redirecting only the original entry preserves six direct branch targets into the old function body, which remains intact.

This standalone patch is not ready to merge as-is into the accumulated five-callback H2 image: it allocates the shared `.text` tail at `0x003FE624`, which that image also allocates. The integration report and rerun expressly cover an original-image patch, not a merged shared-cave image. Use a single cave allocator/merged builder and rerun the final merged image before claiming production H2 integration. No semantic counterexample was found in the bounded direct and preview caller runs.

## Provenance and independent run005

All 23 input hashes in the review packet recompute exactly. Important pinned identities:

- Original image: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`
- Production source: `427c2b44894dc27b770f431ab501a390589e40d7d010547d4976fee269769697`
- Original run004 report: `a9440c5d9f66420893eccaf1350b215e489635d6ead5ec97167fc842d7cd4e94`
- Production object: `778a6e0259ae83d34f1da7eefc9b51ebbeabef62ddbfb13d83155fdb8ab23b07`
- Extracted body: `d98896af49e2177a7afea432b3f88daa517652ea0e22e086b6c514928dc12c71`, 164 bytes, no relocations

I ran the production integration runner with one compiler job and a fresh output at `build/agent-work/H2-semantic/h2-titleconfig-002c615c-production/run005/`, using seed `20261025` and 256 random samples. It exited 0. The run005 report SHA-256 is `a9440c5d9f66420893eccaf1350b215e489635d6ead5ec97167fc842d7cd4e94`, identical to the pinned run004 report. It reproduces the same patched image SHA-256 `5d5fc7af6a39eda53418f41add058059d940cad30450870d2685572ccbc6f221` and IPS SHA-256 `d635ba9b2f88712482feb211dda30a8fceb8e3ef080a6a90caccfe955c953519`. I independently applied run005’s IPS to the pinned original using the repository IPS applier; it recreated `code.production.bin` byte-for-byte.

## ABI, declarations and return behavior

The production definition is `extern "C" u64 ui_func_002c615c(u32,u32)`. Under the 32-bit ARM AAPCS integer return convention, the 64-bit return is returned low word in `r0` and high word in `r1`. Source aliases in `src/camp/unite_extras.cpp` and `src/script/script_vm_extras.cpp`, and the inspected assembly caller declarations, use the same `u64` prototype. C++ quotient-only consumers explicitly cast to `u32`, taking the low word; the H1 assembly caller consumes `r0` after each `BL` and overwrites `r1` before using it. The binary’s second output is remainder in `r1`, caller-saved in the observed callers.

The implementation uses unsigned magnitude arithmetic and explicit sign correction. For nonzero divisors, it matches the signed divide path: quotient sign is the XOR of operand signs, remainder follows numerator sign; nonnegative values give ordinary unsigned quotient/remainder. For divisor zero, the candidate returns the original numerator bits in the high half and zero in the low half. The pinned routine’s path calls `0x0014E604` (which branches to a `BX LR` return) and returns the same `r0/r1` pair. Run005 reports nine zero-divisor cases among 368 direct comparisons.

The production direct report compares `r0`, `r1`, fault/return PC, preserved registers, SP and data bytes; it records direct stack-residue equality for 0/368 cases. The original can leave temporary bytes below restored SP while the compiled body leaves different scratch bytes. The report exposes this instead of claiming full stack-memory identity. The two real preview-caller projections passed, including their caller-stack snapshots. Invalid memory, unusual stack observers, interrupt/concurrent access and MMIO are outside evidence.

## Interior branches and exact patch

The production patch is an unconditional ARM `B` at `0x002C615C` to even ARM cave address `0x003FE624` (`entry_branch` bytes `30e104ea`). It changes two nonoverlapping IPS ranges: the 4-byte original entry and 164-byte cave body. The rest of the original 556-byte body is preserved exactly; I independently confirmed `[0x002C6160,0x002C6388)` is byte-identical to the pinned original in run005.

The report’s interior-entry census finds six external branches from `0x002C6C10` targeting `0x002C6190`, `0x002C61B8`, `0x002C61E8`, `0x002C621C`, `0x002C6240`, and `0x002C6264`, plus no aligned absolute pointers into the body. Retaining the original suffix is necessary so those branches continue to execute. The wrong entry-target control (`branch to candidate body +4`) is detected.

## Direct and caller evidence

Run005 passed 368/368 direct comparisons, with no first mismatch; this includes nine zero-divisor observations and the deterministic H1-domain, directed signed-boundary, and seeded signed-bit inputs. The production `ui_func_002c615c` C++ API and the observed two-register result agree on the reported ABI projection.

Both preview compositions execute the pinned original `0x002BF9F0` helper and other original callees using synthetic ordinary-memory fixtures, with the patched divide body reached through the final guest image. Each performs two divide calls with positive duration: direction zero uses numerator `0x2000`, denominator `8`; direction one uses `0xFFFFE000`, denominator `8`. Both caller cases pass return/state/trace/ABI comparisons. This supports the intended positive-duration H1 interpolation domain, not the H2 cursor caller at `0x0029F278`; that caller remains static-only.

## Placement and remaining limits

The standalone patch places the 164-byte body at `0x003FE624`, in a zero-filled `.text` tail. The accumulated five-callback H2 patch also allocates that shared tail, and the run005 patch was rebuilt from the standalone original image. Therefore its IPS must not be applied alongside the accumulated image without a merged layout and overlap check. Runtime was not run. Physical timing, save persistence, other caller domains, the full `0x0029F278` cursor path, and whole-game behavior remain unproven.

Next action: have the integrator allocate all H2 cave bodies and entry redirects in one merged patch, preserve this helper’s original suffix for the six interior entries, then run a final-image differential and the relevant H2 caller composition before promotion to that accumulated image.
