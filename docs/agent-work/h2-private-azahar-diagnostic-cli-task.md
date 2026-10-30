# H2 private Azahar diagnostic CLI task

## Goal

Produce a private, pinned-source Azahar diagnostic build that can capture a small,
explicitly allowlisted set of H2 guest values at safe callback boundaries. Reuse
Azahar's existing movie record/play support for repeatable HID input. The intent is
to supply the missing guest-state evidence for H2 Audio Settings without using
GDB/RSP, RPC, sockets, firewall changes, host keyboard automation, or direct guest
memory writes.

This is supporting diagnostic infrastructure, not a game-code reconstruction and
not an H2 acceptance task. H2 remains open until captures and the title's input and
callback behavior are independently interpreted and reviewed.

## Pinned inputs and required reading

- Azahar source commit: `219d743a1e698101fe1ab8bef43e6563126c3c27`
  (2126.2 / `HEAD-219d743` in the saved launch records).
- Original game image SHA-256: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
- H2 corrected image, CCI, executable, and staged-profile identities: read the
  reviewed `h2-manual-final-image-stage` manifest and
  `h2-manual-final-image-runtime-review` before designing a runner. Never use an
  installed Azahar profile or a user's ordinary save tree.
- Read `AGENTS.md`, `docs/agent-workflow.md`,
  `docs/agent-work/h2-diagnostic-azahar-feasibility.md`,
  `docs/agent-work/h2-safe-guest-state-capture-route.md`,
  `docs/agent-work/h2-input-seam-contract.md`,
  `docs/agent-work/h2-calc-contract.md`,
  `docs/agent-work/h2-manual-final-image-runtime.md`, and
  `docs/emulator-testing-guide.md`.

The emulator-testing guide describes an older GDB/live-write recipe. It is
superseded for this task by the reviewed no-network route and the explicit
prohibitions below; do not copy its GDB, code-cave, or memory-write steps.

## Required implementation

1. Obtain/build a private checkout of the exact Azahar commit above. Keep source,
   patch, build tree, binaries, and captures under ignored `build/` task paths.
   Do not edit or replace the installed Azahar build. If the exact commit or
   required build dependencies are unavailable, return a precise blocker rather
   than silently switching emulator versions or installing system dependencies.
2. Add an opt-in CLI capture mode, for example
   `--h2-snapshot <output.jsonl>`. It must be disabled by default and accept only
   the expected SMT4 program ID and a task-owned output directory. Reject an
   unexpected title, output path outside the designated run root, duplicate or
   malformed configuration, and unsupported snapshot requests before emulation
   starts.
3. In capture mode, route the Qt emulation thread through the existing
   `System::SingleStep()` API. At the `Core::System::RunLoop` dispatch boundary,
   check a fixed, source-reviewed allowlist of H2 guest PCs and take snapshots
   on the emulation thread immediately before the matching instruction. Use the
   current guest thread's owning process and the process-scoped
   `MemorySystem::ReadBlock` API. Do not read guest state concurrently from the
   GUI, command, or worker thread.
4. Make observation strictly read-only and bounded. The caller cannot choose
   arbitrary guest addresses, lengths, breakpoints, registers, or processes. Do
   not add guest writes, code patches, memory-watchpoint reliance, RSP/GDB/RPC,
   network listeners, host-input injection, or external scripting sockets.
5. Emit one documented JSONL record per allowlisted hit. Include schema version,
   sequence number, guest PC, title/process identity, movie identity (when
   playing), and named snapshots with address and length. Bound record count,
   per-snapshot length, total output size, and I/O failure behavior. A failed or
   truncated capture must exit nonzero and be visibly marked incomplete; never
   report it as a valid comparison.
6. Reuse the pinned frontend's existing `--movie-record` and `--movie-play`
   behavior; do not build a second input-replay protocol. Add a small offline
   preflight/manifest check that verifies the CTM header's program ID and source
   revision against the run manifest and verifies the original/patched title
   image identities before either playback launch. Azahar itself does not enforce
   the title-ID match. Clearly describe that movies reproduce HID pad/touch
   records, not proven logical query results.

## H2 capture scope

Snapshot only addresses and lengths supported by the reviewed H2 contracts. At a
minimum, cover:

- `g_ConfigBytes[0..8)` at the H2 Calc boundary.
- `TitleConfigWork[0..0x158)` and its cursor at `work+0xE8` (0x64 bytes), when
  the current pointer is valid and belongs to the title process.
- The input/event evidence already specified in
  `h2-input-seam-contract.md`: Calc's event-handle arguments and return values,
  logical query `(id, mode)` and results, and the reviewed `IfTouchWork` fields /
  registered region records when their pointers and indices are validated.
- Callback PC and event ordering sufficient to relate snapshots to Calc,
  Secondary, and the title caller. Do not infer physical button labels from
  logical IDs or infer touch meanings from raw values.

Addresses such as `g_TitleConfigWork` (`0x0044E2D0`), `g_ConfigBytes`
(`0x0044E0F8`), `TitleConfig_Calc` (`0x001EA928`),
`TitleConfig_Secondary` (`0x002CAEF0`), and `TitleConfig_IsReady`
(`0x002FC0EC`) are leads from the current pinned image contracts. Confirm each
address, guest mapping, process ownership, snapshot size, and callback timing
against the pinned game image and source before adding it to the allowlist. Use
only small ordinary guest-RAM reads; do not inspect device registers or
rasterizer-owned state.

The known manager/input producers and exact physical-event mapping are not fully
resolved. Capturing raw manager fields is evidence for later interpretation,
not proof that a movie event reaches a particular H2 branch. Do not write
`g_ConfigBytes`, `TitleConfigWork`, `IfTouchWork`, or logical input tables to
manufacture an event.

## Safety and run boundaries

- The observer has no network component and must leave Azahar GDB/RPC disabled.
- Do not modify firewall rules, user/installed Azahar settings, profiles, save
  data, or staged manifests/seeds. Build only into a fresh task-owned ignored
  directory and preserve the pinned original and corrected inputs.
- No keyboard/mouse automation. A human may record one representative movie
  through the existing Azahar CLI-supported recording path; thereafter the same
  CTM is replayed for original and corrected images. Do not launch Azahar for an
  end-to-end capture until the source diff and observer design have independent
  review and the coordinator explicitly assigns the runtime step.
- Validate title, executable, CCI, IPS, profile-root, movie, and output identities
  before playback. Use disposable staged profiles copied from the same pristine
  seed, serialized one process at a time.
- Keep all guest observations read-only. Capture only explicitly declared H2
  values. Do not include save contents, personal paths beyond the task run root,
  or unrelated process memory in reports.

## Validation and evidence

The implementation worker should deliver focused offline tests for CLI parsing,
title/path/range/size rejection, JSONL schema and incomplete-output handling, CTM
identity checks, and observer-disabled behavior. Build the exact pinned source
with a private output tree and record exact command lines, exit codes, toolchain
versions, source diff hash, binary hash, and logs. The build must prove the
default observer-disabled path compiles and retains the normal run-loop policy.

After independent source review, a separately assigned runtime owner may record
one human-operated movie and run matched original/corrected captures with the
reviewed staged profiles. Compare event order, config bytes, work/cursor values,
logical-query arguments/results, touch-manager values, and visible H2 outcomes.
Use no-op, cancel, confirm, re-entry, and restart scenarios where supported by
the same trace. Include a wrong-title/movie negative control and verify logs show
GDB/RPC disabled. The runtime owner must distinguish observed values from
interpretation and report divergences, missing callback hits, crashes, or
truncation honestly.

Do not require every capture scenario to be automated in this implementation
task. Do not claim that a successful build, movie replay, or one matched snapshot
closes H2. Independent review must examine the source diff, read-only invariants,
process/address validation, bounds, output schema, build provenance, and focused
tests before any emulator launch or H2 evidence use.

## Deliverables

- Private Azahar source patch and build instructions/artifacts under ignored
  `build/`; no Azahar source vendoring or binary committed to Git.
- A concise CLI usage note and documented snapshot schema.
- Focused offline tests and machine-readable test/build reports under the task's
  private run output.
- A structured handoff with input hashes, changed paths, command arguments and
  exit codes, report/binary/diff hashes, negative-control results, limitations,
  and the exact next step. The worker must not edit the active task board or H2
  milestone/status.

## Stop conditions and completion definition

Stop and report a bounded blocker if the pinned revision is unavailable, build
prerequisites cannot be used without system installation, the process-scoped
read API cannot be tied to the correct guest process, safe single-step capture
cannot be kept on the emulation thread, a required value lacks a validated
address, or any solution would require a network listener or guest write. Do not
switch to Panda3DS, Mikage, or another Azahar version to bypass a blocker.

This task is complete only when the private diagnostic CLI patch builds, focused
offline checks pass, its read-only/local-only invariants are independently
reviewed, and a structured handoff is accepted. H2 remains open pending a
separate authorized original-versus-corrected runtime capture/review and the
remaining semantic acceptance criteria in `docs/milestones/H2-audio-settings.md`.
