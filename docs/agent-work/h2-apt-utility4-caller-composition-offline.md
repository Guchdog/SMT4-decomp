# H2 APT utility-4: bounded offline caller composition

The isolated reference image and its provisional relocated image were compared in Unicorn using the actual original ARM instructions at seven branch sites and the original 0x002C0EE0 fallthrough. This is not a runtime-approved image. The report records reference, object, source and patched-image hashes and the exact compile command: build/agent-work/H2-semantic/h2-apt-utility4-caller-composition-offline/run-001/checks/report.json.

| Window start | Executed | Stop / continuation |
| --- | --- | --- |
| 0x002C0F6C, 0x002C1260, 0x002C1304 | Original BL instruction, target entry/candidate, controlled wrapper | At BL + 4 before executing the next instruction |
| 0x00106F00, 0x0010700C, 0x002A8164, 0x002C5638 | Original tail B instruction, target entry/candidate, controlled wrapper | Synthetic even ARM return address initially placed in LR |
| 0x002C0EE0 | Original instructions including calls to 0x002BB7A0 and 0x002BB774, original fallthrough, target entry/candidate | Synthetic even ARM return address initially placed in LR |

Each window begins with randomized registers and flags and an aligned synthetic stack with random sentinels; the stated starts do not execute earlier caller setup or subsequent continuation instructions. For 0x002C0EE0, helper hooks record r0 and return without other effects; the wrapper hook records six arguments, ARM state and stack alignment and injects its chosen return word. These are controlled dependencies, not implementations of their real global or IPC effects.

Seeds 7 and 2026 with return values 0, 1, 0x7fffffff, 0x80000000, 0xffffffff passed at each of eight starts (80 cases). Assertions cover returned word, restored SP, r4-r11, caller-visible synthetic memory and live stack, return PC, six wrapper arguments, ordered helper/wrapper calls, ARM state and wrapper stack alignment. Modifying the entry trampoline to BL is detected via return/stack/trace faults, and changing the candidate's command to 5 is detected in the wrapper trace. One focused unit test passed.

This evidence does not exercise full real callers, the 0x00103E80 to 0x002C5624 prefix, effects of the real helpers or wrapper, caller continuations, dynamic/computed incoming paths, or Thumb interworking. No synthetic Thumb case is claimed because its original caller ABI/context has not been established in this bounded task. Original zero padding and the reference-only patch do not establish cave availability in the final composed image or executable permissions at runtime. No emulator, saves, ledger or production integration were used.
