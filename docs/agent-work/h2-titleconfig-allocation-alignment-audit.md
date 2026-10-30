# H2 titleConfig allocation alignment audit

## Finding

For the pinned titleConfig call, the two 0x100 register arguments do not request 0x100-byte alignment. The first selects the ordinary 0x100 allocation branch in the allocator dispatcher. The second is decoded by that dispatcher to a four-byte alignment request for the lower pool allocator. Separately, the outer allocator wrapper computes the returned user pointer to be 0x80-byte aligned. This latter alignment is visible directly in its pointer arithmetic and is the relevant guarantee for the titleConfig work object.

Conditional on the normal allocator returning a valid 0x280-byte backing span, the 0x158-byte TitleConfigWork object is zero-filled, begins at an address divisible by 0x80, and its FillPair target at work+0x1C is four-byte aligned and in bounds. The pinned path has no graceful allocation-failure handling: a no-fit zero from the lower pool allocator is dereferenced by the outer wrapper while writing allocation metadata. If the outer helper were to return null by another route, the initializer publishes it without checking, and later uses work+0x1C. This is a conditional static contract, not evidence that allocation succeeded in a runtime session.

## Pinned call and size

The pinned US v0.1.0 code image is SHA-256 1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558, as recorded in config/game_info.json.
The checked-in allocator assembly mirrors inspected here are src/engine/leaf_batch35_a.cpp (SHA-256 a5805888b7f3acb940be42d6c495b0fb31cc34c0d0becf79ce1326cc538e8d2f) and src/engine/leaf_batch46_a.cpp (SHA-256 795d87d4ad778a5aa8fb3a49657207b34d561d0637b51c05cd194abb426263a8); the shared allocator declaration header is include/engine/asd_symbols.h (SHA-256 d81f738951edf5a71ae53249010d7f8cb75e40dcbf01421cb69e7048753ea8f1).

At titleConfig_func_002f4ca0 (0x002F4CA0), the call at 0x002F4CCC sets:

- r0 = 0x100
- r1 = 0x100
- r2 = 0
- r3 = 0x158
- fifth argument at [sp] = 1

It calls engine_func_002c4b84 (0x002C4B84). The function record and source layout describe TitleConfigWork as 0x158 bytes. The initializer saves the return in r4 and publishes it to g_TitleConfigWork at 0x0044E2D0 without a null check. At 0x002F4DBC-0x002F4DC4 it calls UiConfig_FillPair with r0 = r4+0x1C and r1 = 0xFFFFFFFF. The pair helper writes eight bytes, covering offsets 0x1C through 0x23. That range is within a 0x158-byte object: 0x24 <= 0x158.

## Allocation chain

The disassembly shows the following path:

1. engine_func_002c4b84 saves the first three register arguments and requested size. It acquires the manager lock at the global rooted at 0x00465120, offset +4, then forwards r0-r3 and the fifth argument to engine_func_002c54f0 (0x002C54F0). On return it tests the result; if nonzero, it calls engine_func_002c3b48 with that pointer and the original requested size, then unlocks and returns the pointer. The zero helper writes zero bytes for the requested length. Thus successful AsdMem_Alloc returns a zero-filled 0x158-byte object.
2. For this call, engine_func_002c54f0 takes the normal 0x100 branch (its special cases are 0x20000 and 0x30000). It computes a backing request as (size + 0x100 + 0x3B) rounded down to a 0x80 boundary. With size 0x158 this is 0x280. It passes 0x100, 0x100, 0, 0x280 and fifth argument 1 to engine_func_002b2690.
3. At engine_func_002b2690, the second 0x100 is copied into a working selector, 0x100 is subtracted, and switch case zero sets r7=4. The fifth argument is loaded from the caller stack. If it is zero the function negates r7; here it is 1, so r7 remains +4. Thus this call sends a positive four-byte alignment value down the allocation path. The first 0x100 selects the manager route rooted at [0x00465170+4], then uses its pool subobject at +0x1C and lock at +0x74. The original third argument zero is overwritten at the start of 0x002B2690 and does not affect this selected route in the observed body.
4. The pool wrapper engine_func_002c3a44 is called with pool+0x1C, size 0x280, alignment +4, r3=0, and two zero stack words. It configures pool fields from those control values, then calls engine_func_00146ad8 with pool+0x18, size 0x280, and alignment +4. The lower allocator rounds size to a word boundary and uses alignment-minus-one (3) when finding a suitable pool span. For positive alignment it searches the forward free-list path. On a fit, it delegates block splitting to func_0014f608 and returns the selected aligned block address; its no-fit result remains zero. This supports the meaning of the forwarded 4 as a lower-pool alignment request; it is not the final user-pointer guarantee by itself.
5. Back in engine_func_002c54f0, the raw allocator result is wrapped in metadata and the user pointer is advanced to a 0x80 boundary. If p is the raw pointer, the code computes pad = (0x80 - ((p+0x3C) mod 0x80)) mod 0x80 and returns p+pad+0x3C. Therefore the returned pointer modulo 0x80 is zero. The backing span is 0x280 bytes; the maximum user offset from p is 0xBB, and 0xBB+0x158 = 0x213, within 0x280. The metadata writes and the user extent fit this over-allocation.

The shared declaration in include/engine/asd_symbols.h has the five-argument form AsdMem_Alloc(a0,a1,a2,size,flag); its convenience overload forwards the two 0x100 setup values and zero third value. The binary call explicitly supplies fifth argument 1. Do not conflate that call-specific fifth argument with the convenience overload's default flag 0x100. The precise high-level names/policies for the two 0x100 setup values, pool reuse behavior, and other flag values remain undocumented; the selector-to-4 mapping and 0x80 returned-pointer arithmetic above are direct disassembly facts.

## Failure and guarantee boundary

The lower allocator's no-fit path returns zero. The 0x002B2690 dispatcher forwards that result. On the ordinary 0x100 path, 0x002C54F0 performs metadata stores through the returned raw pointer without a null check (the first word store is at [r0]). Consequently, lower allocation failure does not safely propagate as a null result through this path; it accesses address zero unless the platform maps it, and is expected to fault in the ordinary memory map. The outer 0x002C4B84 non-null check only guards the subsequent zero-fill after 0x002C54F0 returns; it cannot guard the metadata stores that occur earlier.

At the titleConfig caller, there is also no null check before publishing the pointer or before later FillPair use. The evidence therefore supports the conditional statement “if this allocator path completes with its normal backing span, work is aligned and the pair write is in bounds,” not a claim of allocator success or failure recovery. The analysis does not establish pool availability, allocator global state, reuse behavior, OS mapping at address zero, or actual runtime success.

## Evidence and method

- Verified all declared packet input hashes before inspection.
- Pinned disassembly commands: python tools/split_asm.py --code extracted/exefs/code.bin --functions config/functions.csv --addr 0x002F4CA0; repeat for 0x002C4B84, 0x002C54F0, 0x002B2690, 0x002C3A44, 0x00146AD8, and 0x002C3B48.
- Cross-checked the initializer argument table, caller offset/extent and open allocator assumptions in docs/agent-work/h2-init-dependency-contracts.md and docs/agent-work/h2-pair-fill-caller-audit.md; declaration in include/engine/asd_symbols.h; function addresses/extents in config/functions.csv.
- This is static analysis only. No build, test, emulator, UI, RSP, or runtime allocator observation was performed.

Next action: keep the initializer's original allocator call when reconstructing orchestration. A runtime claim about successful allocation needs an explicitly assigned CLI-driven observation or a supported allocator-state fixture. Do not add null recovery or replace the object with local storage without new contract evidence.
