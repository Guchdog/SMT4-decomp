# H6 Persistence Architecture Reconnaissance Record

- **Milestone:** H6 (Save and Reload / Guardado y recarga)
- **Status:** Complete & Reviewed
- **Target Subsystems:** ASD Low-Level File Persistence, SaveLoad Task Lifecycle & FSM, SaveLoad UI Workspace

## 1. Subsystem Boundaries and Mappings

SMT4 persistence execution is organized into three cooperating layers:

1. **ASD Save/Load File Stream Handlers (`0x0021041C`, `0x002104E8`):**
   - `AsdSaveCommon_func_0021041c` reads stream header, verifies `g_asd_save_common_file_ptr` (`0x00424564`), reads payload via `AsdFile_Read_00210340`, performs endian/payload validation, and copies decompressed stream into target buffer using `AsdMem_CopyFrom_002bd610(src, dst, size)`.
   - `AsdSaveCommon_func_002104e8` verifies write readiness, prepares output buffer, serializes system header and checksum metadata, and writes stream to storage via `AsdFile_Write_00210374`.

2. **SaveLoad Process Lifecycle & FSM Handlers (`0x0026B874`, `0x002EF9AC`, `0x002EFB50`, `0x00322D70`, `0x00322F0C`):**
   - `SaveLoadProcess_Init` (`0x0026B874`) spawns task `"Load"` (tag 2, priority `0x0020f924`, callback `SaveLoadProcess_Step`), allocates 0x24-byte work buffer at `0x0043E2F0`, and initializes stream reader with slot index `r1`.
   - `SaveLoadProcess_Step` (`0x002EF9AC`) executes a 6-state finite-state machine (states 0..5):
     - State 0: Allocates decompression heap buffer via `Heap_Alloc_002c4450`.
     - State 1: Initiates asynchronous stream read via `SaveLoadProcess_Read`.
     - State 2: Polls I/O worker status.
     - State 3: Dispatches loaded game state to global world context `0x0044E300`.
     - State 4: Finalizes state transition and notifies UI manager `g_SaveLoadUIManager_0044de28`.
     - State 5: Destroys Load task and releases work buffer.
   - `SaveLoadProcess_Write` (`0x002EFB50`) executes write serialization state machine, saving player progress, inventory, demon compendium, and difficulty parameters to target save slot.
   - `SaveLoadProcess_Read` (`0x00322D70`) executes low-level block reads, verifying magic numbers, CRC-32 checksums, and slot headers.
   - `SaveLoadProcess_Close` (`0x00322F0C`) initializes `"Save"` task with priority `0x0020f924` running `SaveLoadProcess_Write` with `state = 0` and slot/difficulty parameters.

3. **SaveLoad UI Workspace Initialization (`0x00191EAC` - `saveLoadUI_Init`):**
   - Verifies existing UI tasks, allocates and zeroes 0x388-byte manager workspace in `g_SaveLoadUIManager_0044de28`, and registers render/input tasks `"BOOT C"`, `"Boot"`, `"Boot UpDraw"`, and `"Boot UpDraw_R"` with priorities `0x0020f980`..`0x0020f9ac`.
