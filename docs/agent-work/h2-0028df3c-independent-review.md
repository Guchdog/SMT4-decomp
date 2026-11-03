# Independent review: 0x0028DF3C conditional global store

## Finding — accept bounded evidence

The run001 record incorrectly called the direct testing exhaustive over 32-bit inputs. The frozen run002 record corrects this: the implementation expresses the formula for the full u32 domain, while execution sampled 59 cases. No semantic counterexample was found in those tests. Accept only the bounded direct and original-callback evidence; the cross-TU declaration and runtime limits below remain.

## Contract and fresh replay

Pinned ARM and typed C++ both return input r0 unchanged and store that word at 0x0043E0BC exactly when unsigned `(input+1) mod 2^32 < 3`, i.e. input 0, 1 or 0xFFFFFFFF. No other input causes the direct store. There is no stack use or pointer check; normal mapped writable global memory is assumed. The predicate's exhaustive input characterization is static reasoning, not exhaustive testing. Cross-TU `leaf_batch30_c.cpp` consumes a `uint32_t` return, whereas `leaf_batch45_a.cpp` declares the same symbol `void` and discards the return for input 0xFFFFFFFF. At the ARM register boundary both pass the word and the latter does not consume r0, but the incompatible C++ declarations require source-level interface review; do not infer full language-level correctness from these fixtures.

Fresh `python tools/h2_8df3c_experiment.py --out build/agent-work/H2-semantic/h2-callback-global-condition-0028df3c-review/run001/fresh --seed 20270120` exited 0: 59/59 direct and 18/18 original 0x00221168 callback cases matched. Two mutants—non-wrapping `value<2` and storing `value+1`—were detected. Additional replay of all direct cases checked no faults, r0, SP and r4-r11. The runner compares ordered writes in selected globals; its hook is range-filtered, so it does not itself prove no unexpected write to every possible address. Callback uses original set-global, state/context/value getters and a controlled final 0x00286928 seam; it checks the call sequence, stack arguments and raw return but does not validate that helper or H2 runtime.

Fresh body is 24 bytes, zero relocations and SHA-256 `6bf4594c0a01e64932b8b7ef3b3e269e7006820e0492b0e4d88616e8f99abcb9`. Independent IPS replay reproduces the staged image with a single 24-byte getter slot; original callback BL at 0x00221174 targets even ARM 0x0028DF3C. Invalid mapping/fault behavior, concurrent writes, CPSR/VFP and installed runtime remain outside scope.

## Ledger and provenance

Ledger has 10,882 matching functions / 3,116,780 bytes plus eight matching spans / 484 bytes = 3,117,264 matching; 77 non-matching functions / 21,844 bytes; total 3,139,108. The README percentage 99.3041% is the correct four-decimal rounding of 99.30413353092662%; target row is truthfully `non_matching`. All 14 run002 input hashes matched; the only changed input from run001 is the corrected function record. The run001 replay, source, production object, IPS and staged-image hashes were rechecked unchanged and reused without recompilation. Pinned image SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; production source `bac906992ee4dbdf3240f6c2bca152c75e83c248fbef1c016583f9fc7fc512e6`; runner `383ff75752e1748bd1781e34092e697040f59ad3bb543f872dc1f85a98fd3897`; fresh report `f66076bbbeb6139b0e85af1eb5314aa2e4acd87bc1f05754d808b5474d5fe1ce`. No emulator or runtime used.

The coverage wording is now corrected. Separately address the cross-TU interface and validate the complete final helper and H2 runtime before broader claims.
