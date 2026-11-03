# `0x002AA268` — profile-record pointer selection and copy

## Scope and pinned inputs

This is a static contract for the 72-byte ARM function at `0x002AA268`, read
from `extracted/exefs/code.bin` (SHA-256
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`). The
function bytes decode completely as 18 ARM instructions. It contains one
conditional early return and no calls. The H2 direct caller is the two-record
loop inside `0x002B85BC`, at its `BL 0x002AA268` instruction at
`0x002B86FC`.

## Static instruction contract

The likely interface is `u32 camp_func_002aa268(void* record, u32 index,
u32 selector)`, with arguments in `r0`, `r1`, and `r2`. These are full-width
inputs; the two metadata stores truncate them independently.

1. Load `T = *(u32*)(record + 0x64)` into `ip`. If `T == 0`, return directly.
   This path performs no writes and does not dereference either input value.
2. Store `(u16)index` at `record + 0x68`; clear the halfword at `+0x6A`.
3. Clear bytes `+0x88` and `+0x8A`.
4. Compute `entry = T + 12 * index` with 32-bit ARM arithmetic (wrap modulo
   `2^32`). Store `(u8)selector` at `+0x6C`.
5. Test the full 32-bit `selector`. If it is zero, load one word from
   `entry + 0`; otherwise load one word from `entry + 4`.
6. Store that exact 32-bit loaded value, in order, to `record + 0x24`, `+0x28`,
   and `+0x2C`.
7. Return the original `record` pointer in `r0`.

The order in steps 2–6 is the instruction order. In particular, the table
pointer is read before any record writes, but the selected table word is read
after the halfword and byte metadata writes. If the table aliases the record,
those earlier writes can change the selected word before it is loaded. There is
no bounds check, pointer validation, alignment check, or table-length evidence.

`selector == 0x100` is a useful discriminator: the branch selects `entry + 4`
because the compare uses the whole register, while the stored selector byte is
zero. Likewise `index == 0x10000` writes zero at `+0x68` but addresses the
record at `T + 0x30000`; reducing the index to its stored halfword changes the
selected address.

## ABI and effects

The function uses no stack and does not write callee-saved registers. It leaves
`r0` equal to the incoming record pointer on both paths. `r1`, `r3`, and `ip`
are scratch; `r2` is not modified. Condition flags are changed and should not
be treated as preserved. On the non-null path the listed memory accesses are
the complete observed effects; the null-table path reads only `record + 0x64`.

The expected valid domain for a later reconstruction is an aligned, writable
record covering at least `+0x8B`, a readable table entry at the computed
address, and a table pointer whose arithmetic lands on that entry. The code
itself does not enforce this domain. Invalid `record` faults on the initial
word load; an invalid selected table address faults after metadata writes, so
the pre-fault partial state is observable. Those fault cases remain to be
tested by any later differential.

## Actual H2 caller path

At `0x002B86D8`, the caller reads the byte at `object + 0x4C8` and compares it
to 1. When it equals 1, the branch at `0x002B86F0` selects neighboring helper
`0x002BDAC0`. Otherwise the path sets `r2 = 1`, `r1 = 0`, and calls this
function at `0x002B86FC`.

The call is inside a two-iteration loop. For iteration `i = 0, 1`, the caller
passes:

```text
r0 = object + 0x37C + i * 0x8C
r1 = 0
r2 = 1
```

Thus this caller chooses the table word at `entry + 4`, writes selector byte
1, uses index zero, and copies the selected pointer word to the three record
fields. The loop's `object`, mode byte, table pointer and selected words are
runtime state; static code alone does not prove either branch is reached in a
game session.

The equal-to-1 branch calls `0x002BDAC0` at `0x002B8718` with the same computed
record pointer but `(index, selector) = (3, 0)`. It is not a substitute for
this helper. `0x002BDAC0` reads its table pointer at `+0x4C`, writes metadata
around `+0x50`, reads signed halfwords from a 12-byte entry, scales them, and
writes coordinates at `+0x0C/+0x10`. `0x002AA268` instead uses a table pointer at
`+0x64`, selects a 32-bit pointer at entry offset 0 or 4, and copies it to
`+0x24/+0x28/+0x2C`. Their shared caller record does not imply shared
semantics.

## Bounded reconstruction and differential plan

Use explicit `u32` arguments and volatile typed accesses where needed to keep
the observed read/write ordering under aliasing. Return the original pointer.
Before implementation acceptance, compare original and candidate return,
register/stack state, complete mapped memory, ordered memory events, and fault
address plus pre-fault writes for these cases:

- Null table: varied full-width `index`/`selector`; no writes and no table read.
- Non-null table: indices `0`, `1`, `0xFFFF`, `0x10000`, and `0xFFFFFFFF`; map
  the computed wrapped entry to controlled memory so the test checks full-width
  address arithmetic separately from the low-halfword metadata store.
- Selectors `0`, `1`, `0x100`, `0x10000`, and `0xFFFFFFFF`; distinct values at
  entry offsets 0 and 4 verify full-width branch selection and low-byte store.
- Distinct selected pointer values, verifying exact 32-bit copies and the
  ordered destinations `+0x24`, `+0x28`, `+0x2C`.
- A table/record alias fixture where metadata writes overlap the selected entry,
  proving the original store-before-load order.
- Fault controls for an invalid record and a valid record with an unreadable
  selected entry; check the fault and partial write sequence.
- Original caller composition for the two loop iterations at `0x002B86FC`,
  plus the mode-byte `== 1` branch to `0x002BDAC0`; verify exact arguments and
  that the helpers remain behaviorally distinct.
- Negative controls: branch on the stored selector byte instead of full `r2`,
  truncate index before address arithmetic, use a different table stride,
  reorder the selected load before metadata stores, or update fewer than all
  three pointer destinations.

This report establishes static behavior and a concrete offline validation
plan only. No candidate was compiled or executed; no runtime reachability,
table population, pointer lifetime, or game-level profile behavior is claimed.
