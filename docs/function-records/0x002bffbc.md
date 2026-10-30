# `ui_func_002bffbc` — logical mode-1 input query

Address: `0x002BFFBC`  
Original span: 60 bytes  
Production source: `src/engine/leaf_batch32_c.cpp`  
Current classification: `non_matching`

## Recovered contract

The argument is an unsigned 32-bit logical query ID in `r0`. IDs `0..30` are
accepted; every value `>=31` returns zero before reading the global flag or
counter table. For a valid ID, the helper reads the 32-bit value at
`0x004650A8`. If bit 0 is set, it returns zero. Otherwise it reads the counter
at `0x004E3C58 + 4*id` and returns one only when that counter is exactly one.
The function does not write guest memory and uses only caller-saved registers.

The H2 Calc caller uses IDs 9, 0 and 1 through this mode-1 helper. A separate
producer audit identifies their table rows and state masks; it does not establish
physical button names, counter refresh cadence, or frontend provenance. Other
engine callers use the same helper, so ID 0..30 is the recovered helper domain,
while only IDs 9, 0 and 1 are directly established for the H2 Calc path.

## Evidence

- Pinned input image: `extracted/exefs/code.bin`, SHA-256
  `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
- Typed C++ differential report:
  `build/agent-work/H2-semantic/h2-logical-mode1-boundary-fix/run-002/reports/final-differential.json`.
- Differential status: passed, 506 calls. All 31 valid IDs were tested with
  flag values `0,1,2,3` and counter values `0,1,2,0xffffffff`. Invalid IDs
  `31,32,0x7fffffff,0x80000000,0xffffffff` were checked with bit 0 clear and
  set. SP, PC, faults, return value, r4-r11 preservation, and guest writes were
  compared. No original or candidate writes occurred.
- Wrong-flag-bit and wrong-counter-index controls were both detected.
- ID 31's upper-bound case seeds the adjacent counter slot to one, and detects
  a mutant that incorrectly accepts ID 31. Other invalid IDs
  `32,0x7fffffff,0x80000000,0xffffffff` are checked with the adjacent slot at
  its sentinel value.
- Eight production/caller TUs compiled successfully, including the definition
  TU and consumers. The compiled production body is 68 bytes, relocation-free;
  the original body is 60 bytes, so the ledger status is `non_matching`.
- Compile report:
  `build/agent-work/H2-semantic/h2-logical-mode1-query/run-003/checks/compile-consumers/compile-report.json`.

Differential report SHA-256:
`97268d810f2cbb95cb84c6fe9b18987971e0967b27eb6f0d2c28a5d92a352b27`  
Compile report SHA-256:
`0bc49ccbfe7101a86c03329330316ff8bb4c9f0a5ffd8b242d346bc9a15dd1d4`

## Limits

The cases establish the isolated helper under mapped, readable globals. They do
not prove the producer scheduling, input-state freshness, physical control
mapping, H2 event delivery, or integrated original-versus-patched runtime
behavior. See `docs/agent-work/h2-logical-input-table-producer-audit.md` for
producer and caller limits.
