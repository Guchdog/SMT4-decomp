# Independent caller and negative-control review: `0x00286928`

## Verdict

The frozen run supports **bounded offline candidate evidence** for `0x00286928`: 296 direct original-versus-candidate comparisons, four comparisons through the original pinned callback at `0x00221168`, and six detected negative controls. The callback code is present from the pinned image in both sides; only the `0x00286928` entry is replaced with candidate bytes on the candidate side. This does not validate original dependency bodies, the handler continuation after the callback, or runtime/game equivalence.

## Provenance and binary evidence

I recomputed all 13 input hashes in the review packet; all match. This includes pinned `code.bin` SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`, candidate source `dc7a1cc97a91bdf31dafac283ddfa90903fa77f5b7fd13caa24bcb3659ddb810`, runner `c395f1538c6df8e908abe599758d68eafa2b693807f6a9655151d008adcdfb9a`, and offline report `26a4aa424513aa08c6cda1121d1c36e76bc1beb3cabe9dc6883f88cc9cc41fa7`.

The offline report records object SHA-256 `10bc610e6f180e54f380c415ba77baac573047cd6677103d259dd17b688f8280`, an 812-byte compiled body with SHA-256 `cf49833b73ea58eeff3986af47a8c86d05c848123248a255f168bdb58e99c62c`, and an 820-byte slot padded with two ARM NOP words (8 bytes). It lists 22 relocations, all type 28 (`R_ARM_CALL`) to even ARM addresses present in the ledger. The runner additionally resolves these as unconditional, aligned, in-range ARM BL instructions. The candidate fits the original span; this is a size/interworking report, not whole-image integration evidence.

## Callback composition and capture

The runner maps the pinned image at its original addresses and begins both callback cases at `0x00221168`. In the candidate run it writes candidate bytes only at `ENTRY=0x00286928`, leaving callback instructions at `0x00221168` untouched. The code hook records entry into `0x00286928` without skipping it, so the original/candidate helper body then executes from the corresponding mapping.

For each of four callback cases, it compares the full returned machine state, ordered events, external writes, fixture memory snapshots, fault and completion state between original and candidate. It separately asserts the helper ABI capture:

- `r0=0x12003456` from the callback's stubbed `0x0028686c` getter;
- `r1=0x87654321` from stubbed `0x00296f60`;
- `r2` equal to the second stubbed `0x00289640` getter result, set to the case's `incoming_r2`;
- `r3=6`; stack words `(1,0)`.

There are two seeds, each with one case where the first `0x00289640` result is zero and one where it is one. The callback raw return is part of compared `r0`; the candidate result is not normalized in the harness. Ordered writes and fixture snapshots are also compared, so callback-visible and helper-visible effects in this fixture must agree. However, the report does not serialize the actual per-case return values, call traces, or write values: it records the comparison count and passes, while the runner source supplies the assertions. Treat the return/effect result as a differential pass, not a separately tabulated expected-value oracle.

## Six negative controls

Each named mutation is source-generated and compiled by the frozen runner. The runner rejects a mutant if its extracted function body equals the candidate body, then executes its designated control case against pinned original ARM and requires the states to differ. The six mutant object hashes are each distinct from the candidate object hash, confirming each changed compiled output:

| Control | Mutant object SHA-256 | Runner outcome |
|---|---|---|
| `mode_11` | `f856d52cf9fda26052ee23a21053e8890fd3d343307583f2e3b3b1e0d8d1724c` | detected |
| `selector15_prewrite` | `083874b98fae15efc0e0732319fe3ae7989d165096d8d5b8280e5e5d88ff5e55` | detected |
| `selector19_pointer` | `4489e6101d9cff93784bc7ef5e7df3b4c87d9564732b11f94b46c85979b904ad` | detected |
| `r2_zero_state_call` | `ed901aa1da26991d8e8c288e9615bdebdce5c509101e84c80c107c183d2cd63b` | detected |
| `df54_value` | `a037c850c1db4534f736c42f97aacd46b825bc76a1fd34d2abe7b1fa2fbcbfe0` | detected |
| `six_iteration_loop` | `a9f34eba9feaccd0f6015aa1cb471b19ba17af5bff077b8d61a22c72146e58f2` | detected |

The report sets all six controls to `true`; source inspection confirms the compile-difference and baseline-versus-mutant checks. This independently audits the recorded frozen run; I did not invoke the runner or compiler.

## Limits and recommendation

All direct callees of `0x00286928`, as well as the callback's getter callees (`0x00289640`, `0x0028686c`, `0x00296f60`), are intercepted. Getter results are synthetic. Other dependency stubs implement only selected narrow behavior; in particular, `0x002b8d24` does not execute its original body. The callback's globals and object pointers are valid synthetic fixture RAM. The four compositions exercise callback-to-helper entry and return, not the caller above `0x00221168`: handler `0x001a07cc`, its table selection, and its post-callback continuation are not run. No runtime or whole-game claim follows.

Recommendation: accept the 296 direct cases, four callback compositions, six controls, 812/820-byte fit, and 22 ARM call relocations as bounded validation evidence. Preserve the original dependencies and keep the callback/fixture and caller-continuation limits attached to any integration decision.
