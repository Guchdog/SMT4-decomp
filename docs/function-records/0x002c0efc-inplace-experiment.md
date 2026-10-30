# 0x002C0EFC — compact experimental C++

Status: experimental, in-place offline candidate; not promoted. The source calls the original wrapper at `0x002B5A1C` with six words `(4,0,0,0,0,0)` and returns its raw word. Clang compiles the function to 40 bytes with a function-level `minsize` attribute; one `R_ARM_CALL` is resolved and verified at the original function address. The original entry is 44 bytes, so four trailing original bytes remain unchanged.

Across the pinned original and the reviewed composed H2 image, the candidate passed 80 bounded caller-window cases and 16 direct-entry cases per base image. These compare the exact original ARM `BL`/`B` instructions and `0x002C0EE0` fallthrough using controlled hooks for the wrapper and two helpers. Wrong-command, wrong-target, and oversized-body controls were detected. Three focused unit tests passed. Reproduction commands and hashes are in `docs/agent-work/h2-apt-utility4-inplace-candidate.md` and its referenced report.

The wrapper and helper hooks do not execute the actual service path. Upstream setup, caller continuation, Thumb/interworking, indirect calls, and runtime integration remain untested. This per-entry record does not close H2 or justify a ledger status change.
