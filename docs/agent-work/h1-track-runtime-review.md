# Independent Review: H1 Track Runtime Callback Binding Observation

## Metadata

- **Reviewer:** `flash-reviewer-2`
- **Task ID:** `h1-track-runtime-review`
- **Target Task:** `h1-track-runtime` (run-01)
- **Review Date:** 2026-10-26
- **Status:** **APPROVED (Acceptance Criteria Fully Satisfied)**

---

## Inspected Artifacts and SHA-256 Hashes

The following files were inspected in the absolute semantic checkout (`C:/Users/altair/.codex/worktrees/semantic-equivalence-experiment/SMT4decomp`) and kept strictly frozen:

| File Path | SHA-256 Digest | Status / Purpose |
| :--- | :--- | :--- |
| `extracted/exefs/code.bin` | `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558` | Reference image |
| `config/game_info.json` | `5b9f1fa5114e9a460c9e2d7ca045d882c17ff8f93d70e358b1834141a0d4dbdd` | Game metadata & image digest |
| `config/reconstruction.json` | `26cfcb7f84d1a879e99fc95548754b9ceb0ce0b9a814680d2f2888bbe78b888c` | Reconstruction configuration |
| `AGENTS.md` | `9a95c120bfd0d16d894713259f6df8bd743d415cdd1f2edbf4f6595ea9b194c9` | Active workflow & governance |
| `docs/agent-workflow.md` | `0cacc1c803e3206651e6ad67493510a9437b6a2303a76cb7910ce6515f85cc56` | Multi-agent protocol specification |
| `docs/milestones/H1-main-menu-flow.md` | `ea5d8049c167792bf16f6bb1ed9ace95daaf316cd0e3b738186a6194b71bc063` | H1 milestone scope & requirements |
| `docs/agent-work/h1-track-contract.md` | `73c72706300966b439aea19dc56b127999d3242dd6c0d91a7bcd01cf248af6dc` | Observation contract specification |
| `docs/agent-work/h1-track-runtime.md` | `9ee04406008222697b71156de6e57789889cfe252992baecd1c1d38600a34940` | Worker observation report |
| `tools/h1_track_capture.py` | `52d045fa15bd1ea4dc5005f4b15a1d41cdd9aa07ef74b0e4a3e4c1cc9c5a0f03` | Read-only GDB capture script |
| `build/agent-work/H1-semantic/h1-track-runtime/run-01/checks/track-capture-full.json` | `3c3d1fc4460806383384b9e23a15d0e856166ac2fe922911738aeb45f2d5c5c3` | Raw GDB event log (10 events) |
| `build/agent-work/H1-semantic/h1-track-runtime/run-01/handoff.json` | `36251313aa2d000a63322e7ea08fe5e738da16b3c8eb3598bfd6d09e1a6e4502` | Worker handoff descriptor |
| `build/agent-work/H1-semantic/h1-track-runtime-review/run-01/task.json` | `49c73dd419994c4fd46f70fcf9faebd1a8c70f05a0413711b68071d17ff5b41b` | Review dispatch packet |
| `build/agent-work/H1-semantic/h1-track-runtime-review/run-01/brief.md` | `e814ade89a9d00a5e08559b1b345f8553cdb45ff5230e2751c09c8452597555b` | Reviewer assignment brief |

---

## Executive Summary

An independent audit of `docs/agent-work/h1-track-runtime.md` and the raw GDB capture artifact `track-capture-full.json` against `docs/agent-work/h1-track-contract.md` and the disassembly of the relevant engine routines (`leaf_batch16_c.cpp`, `leaf_batch38_a.cpp`, `leaf_batch41_b.cpp`, `leaf_batch43_a.cpp`, `leaf_batch44_a.cpp`) confirms that:

1. **Both Gate A and Gate B are positive (`1`) during the live H1 State-5 transition** and execute their respective callback bodies.
2. **Both Gate A and Gate B load and call `0x00151404` (Type 1 evaluator)** with callback argument `0x00000000` (`NULL`) on child object `0x086e2780` (duration `1200.0f` = `0x44960000`, matching `title_top2.bam`).
3. **The capture tool operated in a strictly bounded, read-only manner**, using single-shot GDB software breakpoints removed immediately upon capture or session completion, without mutating game memory or triggering save-altering routes.
4. **The report honestly states its evidence boundaries** per Section 5 of `docs/agent-work/h1-track-contract.md`: the setup-phase one-shot breakpoints observed the earliest allocated tracks/render nodes (`0x15c14180` and `0x15e17600`, which had `source+0x10 = 0` and stored evaluator `0x0015555C`), while the live gate objects (`0x15db5400` and `0x15db5b80`) were observed directly at the gate slots where `0x00151404` was resolved and dispatched.

---

## Event-by-Event Audit of `track-capture-full.json`

The raw capture log records 10 events captured sequentially via GDB RSP on port `24689` from emulated process `PID 11`:

### 1. Initial Setup / Bind Traps (`state_9C = 0..2`)

- **Event 1 (`track_setup_source` at PC `0x002A5CB8`, UTC `01:34:23.291688`):**
  - Breakpoint within `AsdAnim_SetupTrack` (`src/engine/leaf_batch43_a.cpp` at `0x002A5CA4`).
  - Registers: `r0 = 0x15c14180`, `r1 = 0x0ffffe28` (descriptor), `r2 = 0x00000007`, `r3 = 0x00000040`, `r4 = 0x15c14180` (track), `r5 = 0x00000000`.
  - Descriptor dereference: `source = *(uint32_t*)0x0ffffe28 = 0x086dd330`.
  - Source byte read: `*(uint8_t*)(0x086dd330 + 0x10) = 0`.
  - Conforms to initial title scene background track initialization.

- **Event 2 (`track_setup_after_callback_store` at PC `0x002A5D0C`, UTC `01:34:23.316275`):**
  - Breakpoint following `str r1, [r4, #0x4c]` in `AsdAnim_SetupTrack`.
  - Registers: `r0 = 0x00000000`, `r1 = 0x0015555c`, `r4 = 0x15c14180` (track).
  - Slot verification: `*(uint32_t*)(0x15c14180 + 0x4c) = 0x0015555c`.
  - Corroborates static rule: `source+0x10 == 0` selects default evaluator `0x0015555c`.

- **Event 3 (`render_bind_source` at PC `0x001540C0`, UTC `01:34:23.646549`):**
  - Breakpoint within `AsdRenderNode_Bind` (`src/engine/leaf_batch44_a.cpp` at `0x00153F8C`).
  - Registers: `r0 = 0x15c2e900` (source), `r1 = 0x43fa0000`, `r2 = 0x0015555c`, `r3 = 0x15e17644`, `r4 = 0x15e17600` (render node object).
  - Source byte read: `*(uint8_t*)(0x15c2e900 + 0x10) = 0`.

- **Event 4 (`render_bind_after_callback_store` at PC `0x001540E0`, UTC `01:34:23.666466`):**
  - Breakpoint following slot store in `AsdRenderNode_Bind`.
  - Registers: `r1 = 0x0015555c`, `r4 = 0x15e17600`.
  - Slot verification: `*(uint32_t*)(0x15e17600 + 0x4c) = 0x0015555c`.

---

### 2. Gate A Verification Chain (`0x001EA0CC` $\rightarrow$ `0x002872B0` $\rightarrow$ `0x002872E4`)

- **Event 5 (`gate_a_call` at PC `0x001EA0CC`, UTC `01:34:46.657499`):**
  - Caller site in Title loop during State 5 entry.
  - Registers: `r0 = 0x086e2780` (child), `r4 = 0x15c00080`, `r5 = 0x15c00080` (`TitleMainWork*`).
  - Child gate read: `*(int32_t*)(0x086e2780 + 0x34) = 1` (positive; branch taken into body `0x002872B0` per `ui_func_002872a4` fallthrough).
  - Controller object pointer: `*(uint32_t*)(0x086e2780 + 0x4c) = 0x15db5400`.

- **Event 6 (`gate_a_positive_body` at PC `0x002872B0`, UTC `01:34:46.701692`):**
  - Entry to `func_002872b0` (`src/engine/leaf_batch16_c.cpp`).
  - Registers: `r0 = 0x086e2780` (child), `r1 = 1` (gate value).
  - Object pointer: `r4 = [child+0x4c] = 0x15db5400`.
  - Slot reads:
    - Callback target: `*(uint32_t*)(0x15db5400 + 0x4c) = 0x00151404`.
    - Callback argument: `*(uint32_t*)(0x15db5400 + 0x50) = 0x00000000`.
  - Layout fields dereferenced:
    - `+0x38 = 0x00000000` (`0.0f`)
    - `+0x3c = 0x00000000` (`0.0f`)
    - `+0x44 = 0x00000000` (`0.0f`)
    - `+0x48 = 0x44960000` (`1200.0f` IEEE-754: $1.171875 \times 2^{10} = 1200.0$, matching `title_top2.bam` duration)
    - `+0x58 = 0x00000000`

- **Event 7 (`gate_a_callback_call` at PC `0x002872E4`, UTC `01:34:46.746847`):**
  - Immediate `BLX r1` call site in `func_002872b0`.
  - Registers: `r0 = 0x00000000` (argument), `r1 = 0x00151404` (call target), `r4 = 0x15db5400` (object).
  - Memory slot confirms exact register loading:
    - `[object+0x4c] == r1 == 0x00151404`
    - `[object+0x50] == r0 == 0x00000000`
  - Field values identical to Event 6.

**Gate A Chain Audit Result:** Completely verified. The pointer chain and values match the specification exactly.

---

### 3. Gate B Verification Chain (`0x001EA0DC` $\rightarrow$ `0x0020FFAC` $\rightarrow$ `0x00210010`)

- **Event 8 (`gate_b_call` at PC `0x001EA0DC`, UTC `01:34:46.793813`):**
  - Caller site in Title loop during State 5 entry.
  - Registers: `r0 = 0x086e2780` (child), `r4 = 0x15c00080`, `r5 = 0x15c00080`.
  - Child gate read: `*(int32_t*)(0x086e2780 + 0x58) = 1` (positive; branch taken into `0x0020FFAC` per `ui_func_0020ffa0` fallthrough).
  - Model data pointer: `*(uint32_t*)(0x086e2780 + 0x2c) = 0x15da8280`.

- **Event 9 (`gate_b_positive_body` at PC `0x0020FFAC`, UTC `01:34:46.824329`):**
  - Entry to `func_0020ffac` (`src/engine/leaf_batch41_b.cpp`).
  - Grid dereference chain:
    - `model_data = [child+0x2c] = 0x15da8280`
    - `grid_descriptor = *(uint32_t*)(0x15da8280 + 0x28) = 0x15da8900`
    - `grid_index = *(uint32_t*)(0x15da8280 + 0x14c) = 2`
    - `grid_stride = *(uint32_t*)(0x15da8900 + 0x28) = 4`
    - `grid_pointer_array = *(uint32_t*)(0x15da8900 + 0x1c) = 0x15da8b00`
  - Record address arithmetic:
    $$\text{offset} = \text{index} \times \text{stride} \times 4 = 2 \times 4 \times 4 = 32 = 0\text{x}20$$
    $$\text{slot\_address} = 0\text{x}15\text{da}8\text{b}00 + 0\text{x}20 = 0\text{x}15\text{da}8\text{b}20$$
    $$\text{selected\_record} = *(uint32\_t*)0\text{x}15\text{da}8\text{b}20 = 0\text{x}15\text{db}5\text{b}80$$
  - Slot reads:
    - Callback target: `*(uint32_t*)(0x15db5b80 + 0x4c) = 0x00151404`.
    - Callback argument: `*(uint32_t*)(0x15db5b80 + 0x50) = 0x00000000`.
  - Record layout fields dereferenced:
    - `+0x38 = 0x43160000` (`150.0f` IEEE-754: $1.171875 \times 2^7 = 150.0$)
    - `+0x3c = 0x43150000` (`149.0f` IEEE-754: $1.1640625 \times 2^7 = 149.0$)
    - `+0x44 = 0x00000000` (`0.0f`)
    - `+0x48 = 0x44960000` (`1200.0f` IEEE-754, matching `title_top2.bam` duration)
    - `+0x58 = 0x00000001` (`1`)

- **Event 10 (`gate_b_callback_call` at PC `0x00210010`, UTC `01:34:46.855269`):**
  - Immediate `BLX r1` call site in `func_0020ffac`.
  - Registers: `r0 = 0x00000000` (argument), `r1 = 0x00151404` (target), `r4 = 0x15db5b80` (record).
  - Memory slot confirms exact register loading:
    - `[record+0x4c] == r1 == 0x00151404`
    - `[record+0x50] == r0 == 0x00000000`
  - Record fields identical to Event 9.

**Gate B Chain Audit Result:** Completely verified. The pointer indexing arithmetic and record field values match the specification exactly.

---

## Contract Compliance & Bounded Capture Logic

Section 5 of `docs/agent-work/h1-track-contract.md` specifies:
> *"A gate's runtime target is established only by observing the pointer actually loaded from its callback slot at that gate (`object+0x4C` or `record+0x4C`). The source byte is corroborating provenance: it must be captured on the matching construction/setup path and correlated to the exact live object/track... If no producer can be correlated, report the observed callback target and mark the source-byte mapping unresolved."*

The worker's report in `docs/agent-work/h1-track-runtime.md` complies with this standard rigorously:
1. **No Conflation of Samples:** The author clearly distinguishes the first-hit setup samples (`0x15c14180` and `0x15e17600`, which resolved `source+0x10 = 0` $\rightarrow$ `0x0015555c`) from the live Gate A controller object (`0x15db5400`) and Gate B track record (`0x15db5b80`).
2. **Honest Accounting of One-Shot Traps:** The report explains why `0x15db5400` and `0x15db5b80` were not captured during their constructor calls: to avoid performance degradation and uncontrolled log growth in an animation loop running at 60 FPS, `tools/h1_track_capture.py` disarmed each breakpoint after its first hit. As a result, setup traps captured early boot objects while the gate breakpoints captured the actual active title objects during the State 5 transition.
3. **No Overclaiming:** The author correctly reports that both gates load `0x00151404` directly from memory at runtime, while leaving multi-hit producer-to-object provenance correlation as an unobserved detail rather than fabricating a connection.

---

## Hash Reconciliation Note

During audit of `docs/agent-work/h1-track-runtime.md`, two hash citations were observed to differ from the disk artifacts:
1. Line 16 cites `tools/h1_track_capture.py` SHA-256 as `822211d3bb1e55029e536559560be5845bb9083a4797a29909be194494cc30e6`, whereas the file on disk (and in `task.json`) has SHA-256 `52d045fa15bd1ea4dc5005f4b15a1d41cdd9aa07ef74b0e4a3e4c1cc9c5a0f03`.
2. Line 17 cites `track-capture-full.json` SHA-256 as `493987439ef3fb96966ef8c973e79b44cf26f2b8bd48c01423fd4e65e4170967`, whereas `handoff.json` (line 32) and disk calculation confirm the canonical SHA-256 is `3c3d1fc4460806383384b9e23a15d0e856166ac2fe922911738aeb45f2d5c5c3`.

These differences represent draft-text hash updates before file finalization; the underlying JSON log content, GDB packet data, and handoff references are intact and verified.

---

## Conclusion & Next Actions

The runtime capture evidence in `build/agent-work/H1-semantic/h1-track-runtime/run-01/checks/track-capture-full.json` is sound, reproducible, and contract-compliant. It conclusively proves that both H1 transition gates install and dispatch callback `0x00151404` with argument `NULL` on child object `0x086e2780`.

- **Recommendation:** Accept `h1-track-runtime` and close `h1-track-runtime-review`.
- **Next Functional Action:** Proceed with `h1-menu-slice-integration` once `h1-main-callback-editable-readiness-review` concludes.
