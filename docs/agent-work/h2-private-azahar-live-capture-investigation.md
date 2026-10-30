# H2 private Azahar live capture investigation

## Outcome

The first private live build froze during startup because its Dynarmic
`PreCodeTranslationHook` inserted `CallHostFunction` IR at the H2 PCs even when
the observer was disabled. A bounded no-observer control reproduced the freeze
before the fix; gating the injected calls allowed the same private build to
reach normal APT/menu activity. A no-op injected host call also froze when live
mode was active, so `CallHostFunction` is not a viable capture route in this
pinned build.

An attempted replacement sampled from Dynarmic `AddTicks`. The private live
window reached Audio Settings, but the user saw Azahar's fatal-error dialog
while taking a second manual snapshot. The JSONL contains only the first
`manual_state_snapshot` (377 bytes); it contains no second snapshot or logical
query record. The Azahar log ends with shader-cache `SaveRaw` errors and no
guest exception detail. A matching Windows Application Error/Crash event was
not found. The precise fatal-error cause therefore remains unknown.

Independent review found `AddTicks` is a timing callback, not a synchronized
guest-PC/register hook. Dynarmic may invoke it at dispatcher return and before
SVC/exception callbacks, and its API does not promise `jit->Regs()` contains a
coherent sampling point. It must not be used as H2 runtime evidence.

The `AddTicks` sampler has been removed. The current private executable is
`build/agent-work/H2-semantic/h2-private-azahar-source/build-clang64/bin/Release/azahar.exe`,
SHA-256 `1384f7cb6e45c28b3bfac43f97db69847c168b7b2836ba367c2ba77a1950aaaa`.
`h2_live_preflight.py` and `h2-delivery-manifest.json` pin that binary. The
current build has not been relaunched after removing the sampler.

## Evidence and limits

- The stock staged Azahar cold-profile control progressed through menu APT
  activity; the earlier cold-shader-cache theory alone did not explain the
  private build freeze.
- Private Azahar with live observer and JIT host-call hooks disabled reached
  menu APT activity. The later `AddTicks`-based live run also reached the menu.
- The user's previous original/patched manual UI checks remain positive for
  opening Audio Settings, B cancel behavior, A confirmation, session slider
  values, and slider bounds. They are not paired logical-query trace evidence.
- The failed live run was not a valid original-versus-patched comparison. Do
  not count it toward H2 runtime acceptance.
- No Azahar process remains running. The user's installed Azahar and profiles
  were not modified; the run used the isolated stage under
  `E:\SMT4decomp\build\h2-manual-comparison\run-013`.

## Next step

Keep emulator work paused. Replace JIT host-call injection and the timing-only
`AddTicks` sampler with a supported Dynarmic block-exit/dispatcher hook that
observes state only after it is synchronized, or document an acceptable
runtime-evidence fallback. Before asking the user to repeat a manual scenario,
prove that the private live observer can open Audio Settings, take two manual
snapshots, and close cleanly in a bounded run. H2 remains open until the
capture path is valid and the paired original/patched scenario is recorded.
