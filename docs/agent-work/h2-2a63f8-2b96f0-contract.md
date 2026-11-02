# Resource resolver 0x002B96F0 and flag predicate 0x002A63F8

## Recommendation

The two functions form a coherent, bounded candidate pair and are directly relevant to H2: pinned `TitleConfig_Calc` calls 0x002A63F8 at 0x001EA96C with r0=0x2F and r1=0, then compares its result with zero. This establishes a static direct dependency, not execution in a runtime scenario. Keep the two-index ABI and original null behavior. The short 24-byte spans make compile/relocation/placement checks necessary; a valid C++ model alone does not establish fit or integrated equivalence.

## Pinned ARM contract

0x002B96F0 uses r0 as a 32-bit first index and r1 as a 32-bit second index. Literal at 0x002B9704 is 0x0044EA28. In order it reads the table pointer from [0x0044EA28], computes 3*r0 and reads a 32-bit object pointer at table + 8*(3*r0), i.e. stride 24 with 32-bit ARM wraparound. At 0x002B9700 it executes an ARM B (tail transfer, unchanged LR) to **0x00145798**, not to the next address 0x0014579C. That four-instruction target is `cmp r0,#0; ldrne r0,[r0]; addne r0,r0,r1,lsl #5; bx lr`. A zero object pointer returns zero without reading its first word; otherwise it returns the first word of that object plus (r1 << 5), with 32-bit wraparound. A zero loaded base with nonzero r1 can produce a nonzero result; do not conflate null object and null loaded base. The resolver has no explicit stores or stack use, touches r0/r2 and condition flags, and leaves r1 unchanged; its target leaves r4-r11 and SP unchanged and uses no VFP. The returned value is a raw address; interpretation of negative indices as signed is unnecessary to reproduce ARM bit arithmetic, and out-of-bounds/wraparound is not a validated C++ pointer domain.

0x002A63F8 forwards its incoming r0/r1 unchanged to 0x002B96F0 via BL, unconditionally reads a 32-bit word at returned pointer+0x10, tests bit 2, and returns exactly 1 when set, otherwise 0. It preserves r4 and SP, saves LR, and has no explicit non-stack writes or VFP operations. A null resolver result is NOT handled; it faults if the address is unmapped. Do not silently convert that path into false. Flags and r0-r3/r12 are not guaranteed preserved. Valid registry, readable table/objects/record, alignment, aliasing and lifetime are preconditions; neither function supplies bounds checks. No claim is made about concurrency, memory faults, MMIO, or arbitrary malformed addresses.

## Audit: all 20 aligned ARM BL sites to 0x002B96F0

The scan covers the pinned image interpreted as aligned ARM words, so it can include data false positives and excludes Thumb, indirect and dynamically generated calls. The following surrounding disassembly supports a common raw `(u32 index, u32 subindex) -> record*` machine ABI; it does not by itself prove high-level type names or all possible call domains.

| BL site(s) | r0 / r1 evidence and returned use |
| --- | --- |
| 0x001169BC | constants 14 / 0; reads result+8. |
| 0x00210804, 0x0021081C | r7 / [r5], repeated; reads +0x10 bit 2, then tests second returned pointer. |
| 0x0023E54C | wrapper forwards incoming r0/r1; passes result onward with flag 0x20000. |
| 0x00295290 | pair loaded from input object+8/+0xC; forwards returned pointer to 0x0023E4D4. |
| 0x002A6218 | wrapper forwards incoming pair; passes result onward with flag 0x10000. |
| 0x002A6290 | r6 / r8; tests result before reading +4. |
| 0x002A63FC | predicate forwards incoming pair; reads result+0x10 without null check. |
| 0x002A6448 | wrapper forwards incoming pair; passes result onward with flag 0x30000. |
| 0x002AEB30 | wrapper forwards incoming pair; tests returned pointer and reads +0xC. |
| 0x002AEBD4 | r6 / r7; tests returned pointer. |
| 0x002C1DE8 | wrapper forwards incoming pair; reads returned pointer+8. |
| 0x002C5ABC | wrapper forwards incoming pair; tests returned pointer and sets flag 0x10000. |
| 0x002E14AC, 0x002E1504 | wrappers forward incoming pair; test returned pointer with flags 0x20000 / 0x30000 respectively. |
| 0x0033F3B8 | pair loaded from input object+8/+0xC; passes result to 0x0023E4D4. |
| 0x00388910 | [r4] / r8; result saved in r6. |
| 0x00389100, 0x0038A1CC | constant 0x17 / r5 or fp respectively; result saved. |
| 0x00393614 | incoming r0 and incoming r3 forwarded in r1 before BL; reads result+8. |

A separate aligned scan found one ARM B into the predicate at 0x00294234, no ARM B into the resolver, and its own B into 0x00145798. These are static raw scans, not a complete function-pointer or runtime call graph. Some predicates/callers dereference without checks; others test the returned pointer, which confirms that a resolver-level null result matters.

## Validation plan and limits

For controlled valid memory, compare ARM original and compiled replacements at final VMA, separately and as a pair. Resolver fixtures: multiple first/second indices including 0, 1 and titleConfig 0x2F/0; distinct table records to detect 24/32 strides, null object, non-null object with zero and nonzero base, edge values where safely mapped, r0/r1/r2 and preserved registers/SP, ordered read/write hooks and no stores. Exercise wrapping only in an explicitly mapped, defined harness; avoid introducing undefined C++ pointer arithmetic. Predicate fixtures: result flag 0, bit 2 alone, all ones, unrelated flags, both indices varied; compare fault behavior for null separately rather than inventing a false result. Negative controls should mutate table stride, record stride, base dereference, null branch, bit mask and predicate polarity. Compose the actual `TitleConfig_Calc` branch with the same valid global/table state, preserving original downstream dependencies, plus representative resolver callers that test and dereference the result. Verify ARM interworking, ABI, linker placement and affected consumers; then independent review and integrated original-versus-patched runtime scenario.

This report is static only: no candidate, compile, differential, caller execution or runtime test. Aligned scans do not establish all indirect callers, table bounds, real resource lifecycle or runtime reachability; finite fixtures cannot prove arbitrary malformed, concurrent, faulting or wraparound behavior.

## Provenance

All declared packet input SHA-256 values were recomputed and matched at analysis time. Pinned `extracted/exefs/code.bin`: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; `src/engine/leaf_batch17_c.cpp`: `2ac80c59385ad0f595815a2f2de37da15932242a3656f696d0e5ef94d79cd7d9`; `src/engine/leaf_batch39_a.cpp`: `a8c8cd0f8914acc5e4638206ebb56b39cb8412d21e86cd6fc446a21039a9a6ec`. Read-only Capstone disassembly, image scans and hash verification exited 0.
