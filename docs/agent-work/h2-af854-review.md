# Independent review: 0x002af854 indexed field selector

## Scope and identities

Read-only review of production `src/engine/leaf_batch13_a.cpp` SHA-256 `4e07716f52ef03f88fc2be3cf5ef9124c5dd116fa2cdd44bdd7ca0b557e772a7`, experimental source SHA-256 `c3ee4a189453399f905a1778a41b45dc2c90e832412f3117e7c902e6a33365f3`, runner SHA-256 `bb3d5a0f91447bb1eacb2416997ab7229571f52480047d3c3a016e63122177a8`, object files and recorded output. Reference code.bin is pinned to SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. No compilation, differential execution or emulator operation was performed in this review.

## Original and compiled behavior

Original ARM reads a list pointer at object+0x58; if null, returns incoming r0 with no stores. Otherwise it stores index low 16 bits at object+0x5c, zero halfword at +0x5e, zero bytes at +0x87 and +0x8a, mode low byte at +0x60, and a word from list+index*12+(mode != 0 ? 4 : 0) at object+0x20. It returns the object pointer in r0. Mode selection uses the full 32-bit value: for mode 0x100 the selected field is +4 even though the stored byte is zero. The C++ expresses those results on the documented domain.

The original's stride arithmetic wraps at 32 bits; the supported C++ domain is narrower: valid mapped/aligned ordinary RAM, non-overflowing index and selected element, valid object, and list bytes disjoint from object fields written in the function. Candidate and production extracted symbols are identical 64-byte ARM bodies without symbol relocations and differ from original; candidate object SHA-256 `355c9550f83885191cadfa739c0cfc1088e5ecf56f1b6b1bde32074e16ea230a`, production object `1530b31d9b5de7459b4eef7a5bb2d6313a7c875d8df2ae47285376a8e8dca8e0`. Ledger `non_matching` correctly records differing bytes.

The compiler reorders stores and advances the list read ahead of some original stores. The runner compares sorted write tuples, deliberately not write ordering. Correct final-state comparison therefore does not cover list/object aliasing, MMIO, concurrent observers or faults midway through the operation. The reviewed source has no guarantee for null object, invalid list or wraparound; no fault parity is asserted. Caller-clobbered registers and condition flags differ in generated code and should not be assumed preserved.

`src/engine/leaf_batch22_c.cpp` has a `void` no-argument declaration used by inline ARM, and `src/camp/unite_extras.cpp` declares a three-argument `void` function; the new production definition returns the object pointer and uses typed arguments. The register interface is supported for the tested ABI, but full cross-TU C++ type compatibility or LTO is not. Inspect actual symbol binding, affected consumer builds and final ARM/Thumb state in the integrated image.

## Recorded evidence

`build/h2-af854/offline-closure.txt` SHA-256 `d1cad014ad0cb25fcbccf334ccaa9de047e8ec3bfebb5b7020887a41a20d7710` reports 371 direct cases, 32 original 0x002b8d24 caller cases, and four detected controls. Source inspection confirms direct test inputs include null/non-null list, index 0,1,2,7,19,127 and deterministic random indices below 128, modes 0,1,0x100,0xffffffff, seeded distinct objects/lists, register and final-memory comparison. Mutants target null branch, selection, stride and return; mutation on invalid memory can count as a detected difference.

The caller fixture executes original 0x002b8d24 with table index 2 and requires exactly two entries into 0x002af854, using two valid disjoint lists. It compares r0, SP, r4-r11, selected memory and sorted write events; the original byte-store tail remains in execution. This supports the selected bounded composition, not all table indices, entry states, helper branches, nested H2 lifecycle or actual runtime scheduling. Recorded results were not independently rerun in this review.

## Assessment

No new static counterexample was found within the stated disjoint ordinary-RAM domain. The experimental candidate and production object match prior to final placement. Cumulative patch and interworking verification, original-versus-patched runtime scenario, and explicit limits for aliases/ABI remain necessary for integration; none of the present results establishes full H2 or whole-game equivalence.
