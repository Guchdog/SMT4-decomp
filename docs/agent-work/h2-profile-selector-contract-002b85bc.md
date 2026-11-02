# H2 profile selector contract: `0x002B85BC`

## Recommendation and scope

This is a feasible bounded non-leaf C++ target if the four direct service callees remain original first: `0x002AEA28`, `0x002BF030`, `0x002A8A8C`, `0x002BDAC0`, and `0x002AA268` (five addresses; `0x002AEA28` is called twice). The wrapper has clear six-slot loops and a two-slot follow-up branch, but these service calls own substantial state changes that this wrapper audit does not model. Use explicit manager/object/profile fixtures and record ordered calls and writes. No live TBB population, profile meaning, audio output, or runtime lifecycle is established.

## Entry, data, and ABI

The pinned slot is `[0x002B85BC,0x002B8794)`, 472 bytes. ARM instructions run through the cleanup branch at `0x002B878C`; the last word at `0x002B8790` is the manager-root literal `0x0043DA28`. The function pushes r4-r8/lr (24 bytes), makes no other stack allocation, and returns with `pop {r4-r8,pc}`. It contains no VFP instructions. It preserves r4-r8/SP if callees obey the ABI; r0-r3/r12/CPSR are scratch. It has no caller stack arguments.

The only input is the full 32-bit request in r0, saved in r5. Let M=`0x0043DA28`, and O=`*(u32*)(M+4)`. There is no null check before dereferencing O. It reads the current selected profile byte `O+0x4C9`, calls `0x002AEA28(current_id)`, saves its raw pointer in r4, then calls `0x002AEA28(request)` and leaves that raw result in r0. Both lookups occur even if the first returns null. If either result is null, it immediately returns the second lookup's raw r0; thus old-null/new-nonnull returns the new pointer, while new-null returns zero. Effects of the two lookup calls are retained.

## Ordered control flow and effects

### Both profile pointers nonnull; old profile byte +0x0C nonzero

It reloads O from M+4 and iterates slot `i=0..5`. Each iteration first calls:

```text
0x002BF030(O + 0x34 + 0x8C*i, 1)
```

Then it reads status byte `O+0x494+4*i`. Zero skips the status service calls. For nonzero status, 7 or 9 first calls `0x002A8A8C()` and then reloads the status byte. The reloaded value controls the next block: value 8 executes three calls to `0x002A8A8C()`; any other value executes one call. Thus an unchanged initial 8 produces three calls, an ordinary nonzero value produces one, and initial 7/9 produces one call plus either three more if the service changed the byte to 8 or one more otherwise. The three-call 8 block and status reload are explicit in the ARM control flow.

### Old profile byte +0x0C zero; new profile byte +0x0C nonzero

It loads O and iterates the same six `0x002BF030` calls. For each nonzero `O+0x494+4*i`, it clears that byte to zero and calls `0x002A8A8C()` once; zero skips both actions. It then iterates `j=0..1` over `O+0x37C+0x8C*j`. For each slot, it rereads byte `O+0x4C8`:

- If it equals 1, call `0x002BDAC0(slot_ptr, 3, 0)`.
- Otherwise call `0x002AA268(slot_ptr, 0, 1)`.

The byte test is repeated for each of the two iterations.

### Old and new profile byte +0x0C both zero

It iterates the six slots as in the old-profile-active branch: call `0x002BF030(slot_ptr,1)`, read the status byte, skip if zero, then follow the same 7/9 service call and status-reload logic. A reloaded status 8 runs three service calls; a reloaded non-8 status runs one. It does not clear the status byte and does not run the two-slot follow-up.

### Normal cleanup and return

All non-null paths converge on a fresh load of O from M+4. The function stores word 0 to `[O+0x0C]` using pre-indexed writeback, then stores word 3 to `[O+0x10]`, in that order, and returns r0=`O+0x0C`. This O reload means the cleanup object can differ from the object cached for the preceding loops if a callee changed M+4. The null-profile return skips cleanup and returns the new lookup's result instead.

## Relation to `0x002B8B78` and H2 evidence

The original caller at `0x002B8BE4` sets r0 to its saved full-width request and directly calls `0x002B85BC`; it ignores the return and then rereads the original cached object’s selected ID at `+0x4C9`. The selector call happens only after the caller's same-profile check and its signed manager-latch path. Therefore the selector’s normal return pointer is not a success flag and does not control the caller’s next branch.

The two reviewed `0x002B8B78` caller slices use requests `0x99` (direct TitleConfig initializer) and `0xDC` (conditional nested callback). The reviewed wrapper experiment used controlled dependency implementations and explicitly did not validate transitive memory/audio effects of `0x002B85BC`. The call arguments and static route are established, but selector behavior for those IDs against naturally populated profiles, its profile-byte branch combinations, service effects, and runtime reachability are not established by those slices.

## Dependencies, domain, and focused tests

Keep all direct callees original for the first differential. In particular, do not treat `0x002AEA28` as a pure lookup or infer that returned pointers refer to live profile objects; its resource domain is separately bounded by its own review. The semantics and state ownership of `0x002BF030`, `0x002A8A8C`, `0x002BDAC0`, and `0x002AA268` are also outside this wrapper contract. The manager root/object, profile pointers and bytes through +0x0C, slot records through `O+0x4C8`, and registry service effects must be valid and mapped. Null/unmapped manager or object, invalid profile/table pointers, aliasing, concurrent mutation, service faults, and live resource/audio behavior are unsupported.

For a candidate, compare return r0, manager/object/profile bytes, ordered stores, all dependency arguments/call counts, SP and r4-r8. Direct fixtures should cover both lookup-null combinations; old/new profile byte+0x0C combinations; six status bytes at 0, 1, 7, 8, 9, and another nonzero value; the two-slot mode byte at 1 and non-1; helpers mutating M+4 before cleanup; and distinct slot data. Include service hooks that mutate an initial 7/9 status to 8 and verify the subsequent three-call block. Include negative controls for loop bounds/stride, clearing status in the wrong branch, the 8-branch three-call multiplicity and 7/9 status reload, swapping 2BDAC0/2AA268 arguments, and omitting the final cleanup. Separately compose the real `0x002B8B78` callsite for requests `0x99` and `0xDC` with identical explicit selector fixtures; do not describe these as natural runtime H2 reachability.

This is static contract work only. No compiler, ARM execution, differential, emulator, or live TBB/profile inspection was performed.

## Provenance

All 14 declared input hashes in the task packet matched, including `code.bin` SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. The complete 472-byte region was independently decoded as ARM, including the manager literal and common cleanup path. The `0x002B8B78` callsite at `0x002B8BE4` was verified from the pinned image. No source, ledger, board, or shared files were edited.
