# Independent review: H2 callback package 0x00221168

## Scope and inputs

Reviewed package script SHA-256 `6033a48f0504b1aa3a99e624daf57a8fc386a0c6b07fa0725218e5c387c2d8b7`, frozen candidate and runner identified in task packet, original code.bin, H2 base and generated image, IPS and manifest. Read-only Python/Capstone inspection and IPS round-trip; no build, differential run, emulator, runtime scenario, or modification of frozen inputs. Existing object-to-source provenance is not independently established by this review.

## Image and relocation

Recomputed SHA-256: base `acd8b2f35df08f225ca65b0fbf8aeef2dbbaa71171904e31c301e8bff6a51446`, image `061058c4c7e3ddc548c0166b41d837ab1ee88293c5500853faf79e6737b4e757`, IPS `69ac130f61e2393d4c75668cce9cbd9add8cb6b775284e780df34b43b11a7dec`, and image candidate slot first 140 bytes `eb896677b9318fddfed95b2d7232ef6eecff9c60e9ae4f0508bf1aa1c604f08b`; all match manifest. Applying IPS to pinned original with project's apply_ips reproduced the image byte for byte. Original SHA-256 is pinned by package script; the IPS comparison itself does not independently validate runtime execution.

There are 91 changed bytes between base and image, all inside 140 bytes beginning at guest 0x00221168. The remaining eight bytes in the original 148-byte span equal base. The H2 base already contains other patches; the IPS includes all differences from the pinned original, not merely the callback.

Capstone independently decodes six final image `BL` instructions: 0x00221174 -> 0x0028df3c, 0x00221178 -> 0x00289640, 0x002211b0 -> 0x0028686c, 0x002211c0 -> 0x00296f60, 0x002211c8 -> 0x00289640, and 0x002211e4 -> 0x00286928. These are direct ARM BL encodings and word-aligned destinations. The entry in the final image at 0x00406140 is the even ARM callback pointer 0x00221168, used by the handler BLX. These observations establish the reviewed call sites and table entry, not every runtime indirect caller or the state of arbitrary callers. The frozen runner also checks CPSR and SP alignment at selected hook entries.

## Interior references and limits

The packaging scan checks aligned words equal to interior word-aligned addresses and ARM-style branch immediates against the composed base and found no hits according to its passing manifest. Independently scanned every aligned 32-bit word with bit 0 masked, looking for an address strictly inside the span; found zero hits. This also covers aligned literal pointers carrying a Thumb bit, but may interpret data as pointers. It does not cover Thumb branch encoding, unaligned pointers, computed addresses, self-modifying code, or other indirect entry mechanisms. The package script's branch calculation does not explicitly decode ARM BLX-immediate H bit and therefore its zero-hit result is not a complete interworking audit. Eight retained original bytes are unreachable through normal new-entry fallthrough, but external interior entry cannot be ruled out solely by these scans.

## Evidence and promotion

The manifest reports 192 H2-base offline case comparisons; the script invokes the frozen runner against the composed base and uses 64 cases for three modes. This review inspected the code and artifacts but did not rerun or independently capture those comparisons. The selector is stubbed, and the original-helper scenario stubs 0x002c1f28 to return zero. The package report does not pin the compiler/object, all transitive Python imports, or an execution log; reconstruct source-to-image provenance independently or record those identities when integrating. Null +8 and wider aliasing remain outside the supported source domain as described in the earlier candidate review.

The image and IPS are internally consistent and their tested entry/call encodings are as expected. Do not infer complete helper semantics, full scenario equivalence or all-entry safety from this static review. Complete independent evidence inspection, ARM/Thumb offline and caller gates, then the defined original-versus-patched H2 runtime scenario. Review again if source, runner, composed base, generated binary or package tooling changes.
