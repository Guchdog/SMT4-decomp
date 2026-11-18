# H18 candidate: initializer entry `0x003F3274`

## Result

Recovered the 112-byte ARM initializer and its 16-byte literal pool within the `0x003F31D8` compound catalog span. Added an experimental editable C++ implementation and a private offline Unicorn differential runner. The candidate is not integrated into production source or the ledger.

The pinned bytes show this entry ends with `BX LR` at `0x003F32E0`; its four literal words end at `0x003F32F3`, and the next code entry starts at `0x003F32F4`. The routine initializes two global word pairs and 11 configuration words at the addresses and values listed in [the function record](../function-records/0x003f3274.md). No aligned direct ARM `BL` or exact aligned pointer word to this entry was found in `code.bin`; the startup/registration path is not established.

## Validation

`python -m unittest tests.test_h18_003f3274_experiment -v` passed three tests for candidate/runner presence, explicit recovered constants, and the original callable boundary/literal pool. `python -m py_compile tools/h18_003f3274_experiment.py tests/test_h18_003f3274_experiment.py` exited 0.

The private differential runner passed 20 seeded cases at seed 7 and 32 at seed 20261024. It exercised all 16 input NZCV combinations and varied target-memory initialization. Both runs detected five negative controls: wrong first sentinel, wrong config offset, wrong config size, wrong final marker, and wrong second sentinel. Reports and hashes are recorded in [the function record](../function-records/0x003f3274.md).

## Scope and caveats

The comparison covers exact global values/write ranges, final watched RAM, callee-saved registers, SP, PC continuation and CPSR. Caller-saved register equality is not required. Temporary compiler stack writes below the incoming SP are allowed; they do not persist in the global-state comparison. No full caller composition or emulator run was performed, and the concrete registration/startup route remains unknown.

The first harness run exposed two harness issues before the passing reports were generated: changing Unicorn CPSR mode after setting banked LR lost the trap return address, and the candidate legitimately used caller-saved LR plus temporary stack space. The runner now sets CPSR mode before SP/LR and checks ABI-preserved state while bounding stack scratch. These are harness corrections; no counterexample remained in the completed reports.
