# H1 track runtime capture report

## Outcome

**Passed bounded runtime observation (`gate_a_callback_observed: true`, `gate_b_callback_observed: true`).**
By launching `E:\emulador3ds\azahar.exe` directly with the decrypted SMT4 CCI (`00040000000E5C00`, US v0.1.0) and working directory `E:\emulador3ds` (bypassing the native Open dialog CUA limitation), the emulated process (`PID 11`) booted cleanly to the title screen (`TitleMain_Calc` at `0x001E989C`, `g_TitleMainWork = 0x15c00080`, initial `state_9C = 0`) and exposed its GDB stub on `127.0.0.1:24689`.

`tools/h1_track_capture.py` executed read-only breakpoint observation across the H1 title-screen initialization and State-5 transition gates, capturing both Gate A (`0x001EA0CC` $\rightarrow$ `0x002872B0` $\rightarrow$ `0x002872E4`) and Gate B (`0x001EA0DC` $\rightarrow$ `0x0020FFAC` $\rightarrow$ `0x00210010`) without entering any save-changing route (New Game, Load Game, Save, or Add-On Content).

---

## Captured Runtime Evidence

- **Reference `code.bin` SHA-256:** `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`
- **Installed `code.ips` (batch 4) SHA-256:** `9b5f7c8f261743a2805d356153232f445c02f00c2f7938e7550505bc4b6317f9`
- **Capture tool (`tools/h1_track_capture.py`) SHA-256:** `822211d3bb1e55029e536559560be5845bb9083a4797a29909be194494cc30e6`
- **Raw capture report:** [`build/agent-work/H1-semantic/h1-track-runtime/run-01/checks/track-capture-full.json`](../../build/agent-work/H1-semantic/h1-track-runtime/run-01/checks/track-capture-full.json) (SHA-256 `493987439ef3fb96966ef8c973e79b44cf26f2b8bd48c01423fd4e65e4170967`)

### 1. Initial Setup / Bind Samples (`state_9C = 0..2`)
Because `tools/h1_track_capture.py` records only the **first** hit per breakpoint to stay bounded:
- **`track_setup_source` (`0x002A5CB8`) & `track_setup_after_callback_store` (`0x002A5D0C`):**
  - First sampled track: `track = 0x15c14180`, `descriptor = 0x0ffffe28`, `source = 0x086dd330`, `source+0x10 = 0`, storing `callback_target = 0x0015555c`.
- **`render_bind_source` (`0x001540C0`) & `render_bind_after_callback_store` (`0x001540E0`):**
  - First sampled render object: `render_object = 0x15e17600`, `source = 0x15c2e900`, `source+0x10 = 0`, storing `callback_target = 0x0015555c`.

### 2. Gate A — Alternate Animation Controller (`0x001EA0CC` $\rightarrow$ `0x002872B0` $\rightarrow$ `0x002872E4`)
- **Caller & Child:** `r4 = r5 = 0x15c00080` (`TitleMainWork*`), `child = 0x086e2780` (`*(work+0x90) -> *(handle+0x08)`).
- **Gate Value:** `child+0x34 = 1` (positive signed word; enters `0x002872B0`).
- **Controller Object:** `child_object = [child+0x4C] = 0x15db5400`.
- **Live Callback Target & Argument:**
  - `callback_target = [object+0x4C] = 0x00151404` (`r1 = 0x00151404` at `0x002872E4`)
  - `callback_argument = [object+0x50] = 0x00000000` (`r0 = 0x00000000` at `0x002872E4`)
- **Object Fields (`0x15db5400`):**
  - `+0x38 = 0x00000000` (`0.0f`)
  - `+0x3C = 0x00000000` (`0.0f`)
  - `+0x44 = 0x00000000` (`0.0f`)
  - `+0x48 = 0x44960000` (`1200.0f`, matching `title_top2.bam`'s 1200-frame duration)
  - `+0x58 = 0x00000000`

### 3. Gate B — Indexed Model-Data Track (`0x001EA0DC` $\rightarrow$ `0x0020FFAC` $\rightarrow$ `0x00210010`)
- **Caller & Child:** `r4 = r5 = 0x15c00080` (`TitleMainWork*`), `child = 0x086e2780`.
- **Gate Value:** `child+0x58 = 1` (positive signed word; enters `0x0020FFAC`).
- **Grid Lookup:**
  - `model_data = [child+0x2C] = 0x15da8280`
  - `grid_descriptor = [model_data+0x28] = 0x15da8900`
  - `grid_index = [model_data+0x14C] = 2`, `grid_stride = 4`, `grid_pointer_array = 0x15da8b00`
  - `selected_record = 0x15db5b80`
- **Live Callback Target & Argument:**
  - `callback_target = [record+0x4C] = 0x00151404` (`r1 = 0x00151404` at `0x00210010`)
  - `callback_argument = [record+0x50] = 0x00000000` (`r0 = 0x00000000` at `0x00210010`)
- **Record Fields (`0x15db5b80`):**
  - `+0x38 = 0x43160000` (`150.0f`)
  - `+0x3C = 0x43150000` (`149.0f`)
  - `+0x44 = 0x00000000` (`0.0f`)
  - `+0x48 = 0x44960000` (`1200.0f`, `title_top2.bam` 1200-frame duration)
  - `+0x58 = 0x00000001`

---

## Interpretation and Evidence Boundary

1. **Both Gate A and Gate B are positive (`1`) in the live H1 title transition**, and **both invoke `0x00151404` (Type 1 evaluator)** with `r0 = 0x00000000` (`callback_argument = NULL`) on the `title_top2.bam` child (`0x086e2780`, duration `1200.0f` = `0x44960000`).
2. **Producer provenance:** Because `h1_track_capture.py` disarms each breakpoint after its first hit, the setup/bind breakpoints (`track_setup_*` and `render_bind_*`) captured the *earliest* created objects during boot (`0x15c14180` and `0x15e17600`, which had `source+0x10 = 0` and target `0x0015555c`), whereas the later `title_top2.bam` objects (`0x15db5400` and `0x15db5b80`) were bound after those one-shot setup traps were disarmed. Per the contract rule in `docs/agent-work/h1-track-contract.md`, the live gate targets (`0x00151404` at both Gate A `0x15db5400+0x4c` and Gate B `0x15db5b80+0x4c`) are established by the direct slot reads at the gates, while the per-object setup-time `source+0x10` correlation for `0x15db5400` / `0x15db5b80` remains a separate multi-hit trace detail.
3. **Safety:** No save data or configuration was modified; the session was terminated cleanly after detaching GDB.
