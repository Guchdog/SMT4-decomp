# H2 config mapper production integration — run-008

## Result

The three reviewed `titleConfig` byte-to-index mappers now have readable C++
definitions in their existing production translation units. Each compiled body
is 48 bytes inside its original 92-byte function span, has no ELF relocations,
and reads the same pinned read-only threshold table as the original. The patch
builder pads each body to 92 bytes with ARM NOPs and applies the three records
to the independently reviewed run-013 five-function image.

The resulting image passes all three production mapper comparisons for every
byte value plus 256 seeded cases under each of two seeds. The run-013 five
callback validation passes again on the mapper-extended image, including the
initializer's calls through the mapped mappers. The State-9/10 caller
composition also passes 3/3 cases with the production initializer and ready
gate. This is offline evidence; H2's Azahar UI/input/persistence acceptance
remains open.

## Contract and C++ implementation

Each function scans eleven ascending bytes at its original table address and
returns the first index whose threshold is at least the input. If no threshold
qualifies, it returns zero. The H2 initializer loads the persisted values with
`LDRB`; `TitleConfig_Calc` also calls the helpers with byte-valued config fields.
The supported production caller domain is therefore zero-extended `u8` (`0..255`).

The production bodies use a readable C++ loop over a `volatile const u8*` at the
original ROM table address. The volatile reads preserve the explicit lookup
behavior. The loop pragma keeps the ARMv6K Clang output compact. The compiled
body is 44 executable bytes followed by its four-byte in-body table-address
literal. It returns before that literal. The patcher checks the local branch,
return, literal location/value, symbol size, no-relocation condition and
original 92-byte span before writing any bytes.

| Address | Table | Thresholds | Production symbol SHA-256 |
|---|---|---|---|
| `0x002CAB70` | `0x004077EB` | `0,10,20,25,30,35,40,45,50,70,90` | `fbb5b34c4b5b94322cb10ba9da7257fa4010d82c3aa6f754e54d6b32a14c2438` |
| `0x0021F39C` | `0x004077F6` | `0,10,20,30,40,50,60,70,80,100,120` | `616fdaa08187217f5859996444b65cdce852f6b045f047e0497df4602eaa0451` |
| `0x002E0AF4` | `0x00407801` | `0,10,20,30,40,50,60,70,80,100,120` | `8b99e056165e42868b91ef1d6498d392261d3fd37197b6ac42331d75ea2e5aaa` |

## Build and patch identity

Production translation units were built separately with one job each:

```powershell
python tools/build_check.py --repo-root . --tu src/engine/leaf_batch32_b.cpp --out-dir build/agent-work/H2-semantic/h2-config-mapper-production-integration/run-001/checks/production-tu-b --jobs 1 --force
python tools/build_check.py --repo-root . --tu src/engine/leaf_batch32_c.cpp --out-dir build/agent-work/H2-semantic/h2-config-mapper-production-integration/run-001/checks/production-tu-c --jobs 1 --force
```

Both exited 0 under Clang 23.1.3 targeting ARMv6K hard-float with `-O2`.
Object SHA-256 values are `2aea8bc429a521f894546bd550b44b53d8940493d10d880b06dc188c588d772d`
for `leaf_batch32_b.o` and
`5d0f079cfc288754d3035e0aa2484b88b5e04dcac6e95073efa9280d5931c58d` for
`leaf_batch32_c.o`. The patch-builder SHA-256 is
`5ed130126718742795dafe6c3d68674233bc11c7a3782d9181533d6119cbabcd`.

Patch chain:

| Stage | Base image SHA-256 | IPS SHA-256 | Result image SHA-256 |
|---|---|---|---|
| Reviewed run-013 five-function image | `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558` | `3901823e725afb914a9bc49c5f86038f8c285c107eedaa3a4337a64bc5b062d3` | `7b2bc2983a890e1c4cf1ae71beca9f574260d98d6cfcdffb3bbb34bd3eb2b291` |
| Three mapper replacements | `7b2bc2983a890e1c4cf1ae71beca9f574260d98d6cfcdffb3bbb34bd3eb2b291` | `72b9c68d2aca701c899978adeb793698032097a2599d70ab9c90a0361336e214` | `97b6c2ab9ea7f15904bbee3ad42115599bd3529220dbfba818a77bbbcfbe321c` |

The final manifest SHA-256 is
`e3f3502e9326cbf82e37ad995d8fb8889dc7a58a71f6ad88676182f7748cf2d5`. Two
independent patcher runs produced identical image, IPS, manifest and
differential-report hashes. The IPS reapplies to the exact run-013 image and
recreates the final image. The three write spans are each 92 bytes; total
changed bytes from run-013 are 209.

The direct-branch scan covered all 10,967 ledger spans in both the pinned
original and run-013 image. The aligned absolute-word scan covered the full
`code.bin`. Neither found an external direct branch or aligned pointer into an
overwritten mapper interior. Computed or encoded-relative indirect targets and
unaligned pointer interpretations are outside this scan.

## Differential and caller evidence

Fresh reports from
`build/agent-work/H2-semantic/h2-config-mapper-production-integration/run-008/checks/production-mapper-patch/`:

- Seed 7: all three functions pass 512 cases each (256 exhaustive bytes plus
  256 seeded byte cases); report SHA-256
  `7d2518fa46cceb30944882ae302c32751d8d6e11e77a898e26a645c24e829cf6`.
- Seed 20261024: all three functions pass 512 cases each; report SHA-256
  `55cbdf3d48a91f5ebb6ef136cf95570fe8332002e73f22f4ac19f5c698f7462f`.
- Both sides have empty data/stack write sets and preserve callee-saved
  registers, SP and `d8-d15`. The original and replacement read the same table
  addresses across the exhaustive byte domain; read footprints are recorded,
  not required to match per case.
- The threshold-10-to-11 negative control is detected at input 11 (`2` versus
  `1`). Focused patcher tests pass 4/4.

The existing combined final-address suite was rerun against the final image:
Calc 16/16 sequences and 54/54 ticks; Draw 46/46 cases; Secondary 34/34;
initializer 10/10; ready gate 4/4. The report SHA-256 is
`9c398ceabf142fb6557f60545ced5c7a9878e0a741b892a3ec3191bfe24c8a1c`.
The initializer differential maps both images and executes their mapper calls
from the images; its other declared services remain HLEs.

The State-9/10 composition uses the exact mapper-extended image and production
initializer/ready gate. It passes 3/3 caller cases and detects the wrong-Calc
callback control. Report SHA-256:
`be882f832025a6f3e4fb864fb40ee23bfae7267bbf21a7c25207fee52b1b210c`. The
caller runner models allocation, task factories, task-active lookup,
sprite/cursor/resource setup, sound/reset and other services as matched HLEs;
it does not schedule Calc, Draw or Secondary.

`asm_diff.py` was run through a private copy of each production TU. It reports
48 compiled bytes versus 92 original and `Exact Match: False` at all three
addresses, as expected. The production ledger rows are `non_matching`, which
truthfully records the changed bytes. These semantic reports do not change
that exact-byte classification.

## Limits

The mapper contracts and H2 caller byte domain are supported by the reviewed
isolated and production differentials. This does not establish physical button
meanings, touch/input delivery, rendered UI behavior, scheduler lifecycle,
cancel/confirm semantics, save-file persistence, re-entry after a real edit,
restart behavior or Azahar equivalence. Keep H2 runtime acceptance open and
continue using the CLI-only/no-keyboard-or-mouse route when runtime work resumes.
