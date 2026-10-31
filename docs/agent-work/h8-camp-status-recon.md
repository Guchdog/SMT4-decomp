# H8 Camp Menu, Inventory, and Party Management Architecture Reconnaissance Record

- **Milestone:** H8 (Camp Menu, Inventory, and Party Management / Menú de Campaña, Inventario y Grupo)
- **Status:** Complete & Reviewed
- **Target Subsystems:** Gauntlet / Burroughs Application Menu, Character / Demon Status Portrait & 3D Camera, Elemental Affinities Table, Touchscreen Bottom-Screen Status & Party Workspace, Inventory Item List & Sorter, Skill List Builder & Sorter.

## 1. Subsystem Boundaries and Mappings

Shin Megami Tensei IV camp menu and status subsystems are organized into three cooperating functional domains:

1. **Gauntlet / Burroughs Application Menu (`0x002E2454`):**
   - `GauntletAppMenu_Init` (`0x002E2454`, 764 B window, 268 B candidate, +496 B margin): Allocates 0x1B8-byte work buffer (`0x002C4B84`), zeroes memory, registers calculation task `"Gauntlet App CALC"` (`0x002C5978`, priority 2, callback `0x00329410`) and draw task `"Gauntlet App DDRAW"` (`0x002C4C00`, priority 0x57, callback `0x0032B070`), initializes sub-menu structures via `0x002C0BA8` with app IDs 0x521, 0x526, 0x527, 0x59F, initializes sub-task workspace `0x002488A8`, and loads script/dialogue resources `"camp/gauntletApp.mbm"` and `"camp/gauntletApp.bf"` (`0x002976AC`).

2. **Status Screen Top-Screen 3D Presentation & Affinities (`0x00223A90`, `0x00258E38`, `0x00293E4C`):**
   - `StatusBustUp_Init` (`0x00223A90`, 248 B window, 184 B candidate, +64 B margin): Demon/Flynn bust-up portrait visual renderer setup (`c:\SMT4\XRD686\sdds4\program\status\StatusBustUp.cpp`). Loads resources 0x17 (`0x002C4E28`) and 0x23 (`0x002C5B04`), allocates buffers 1 (0x266 bytes) and 2 (0x81 bytes), binds layout tables via `0x002C3B48`, and manages reference count.
   - `StatusCamera_Init` (`0x00258E38`, 480 B window, 360 B candidate, +120 B margin): Status 3D camera projection matrices and coordinate setup (`c:\SMT4\XRD686\sdds4\program\status\StatusCamera.cpp`). Allocates 0x53C-byte camera structure, copies position, target, and up vectors, sets 3DS top-screen 5:3 aspect ratio (`1.6666666f`) and near/far clip planes, and binds camera transform update callbacks (`0x002BC828`, `0x002C2210`, `0x002C20A8`, `0x002C1FFC`, `0x00298FEC`, `0x002C1740`, `0x002C1774`).
   - `Status_UpdateAffinityTable` (`0x00293E4C`, 520 B window, 316 B candidate, +204 B margin): Elemental resistance and affinity evaluation table. Reads active entity state flags at `+0x1E63`, `+0x1E66`, `+0x1E67`, evaluates Phys/Gun/Fire/Ice/Elec/Force/Light/Dark resistance parameters, and sets display mode (0, 1, 2, 4, 5) via `StatusDown_SetDisplayMode_00292f44`.

3. **Touchscreen Bottom-Screen Status, Inventory & Party UI (`0x002D931C`, `0x001EE7C8`, `0x0032C4BC`, `0x001EE5A4`):**
   - `StatusDown_Init` (`0x002D931C`, 764 B window, 440 B candidate, +324 B margin): Lower-screen status workspace initialization (`c:\SMT4\XRD686\sdds4\program\status\StatusDown.cpp`). Allocates 0x2394-byte workspace, registers calculation task `"TMD CALC"` (`0x002C5978`, priority 2, callback `0x001CA648`) and draw task `"TMD DDRAW"` (`0x002C4C00`, priority 0x57, callback `0x001CC914`), binds sprite tables at `g_StatusDownSpriteTable_00407d58`, initializes UI animated sprites at `work + 0x48` and `work + 0xD4`, and configures touch layout.
   - `StatusDown_PopulateItemList` (`0x001EE7C8`, 384 B window, 324 B candidate, +60 B margin): Inventory item list builder. Zeroes 0x1400-byte item array at `work + 0xE30`, iterates 1280 master item entries (`ItemTable_Get_002b9364`), tests usable/item flags and quantity in `item_counts`, builds active item array, sets up pagination via `UiPage_Setup_0029fae8`, and invokes `StatusDown_SortItemList_0032c4bc`.
   - `StatusDown_SortItemList` (`0x0032C4BC`, 372 B window, 208 B candidate, +164 B margin): Inventory sorting dispatcher. Reads sort mode from `UiMenu_GetSortOptions_002a0fac`, dispatches `qsort_002b7f0a` using ascending/descending comparators for ID (`0x00206CBC` / `0x002E4608`), Category (`0x002DCA98` / `0x002C6D30`), Type (`0x00206C38` / `0x002E4584`), and Cost (`0x001F61A4` / `0x001D1BB8`).
   - `StatusDown_PopulateSkillList` (`0x001EE5A4`, 548 B window, 368 B candidate, +180 B margin): Skill list builder. Zeroes 0x800-byte skill array at `work + 0x5C8`, iterates 1280 master skill entries (`SkillTable_Get_002b9364`), tests active bit in `skill_bitfield`, builds active skill entries, configures pagination, and dispatches skill sorters for ID (`0x00206BE8` / `0x002E4534`), Cost (`0x001F60DC` / `0x002DC96C`), and Name (`0x001F6174` / `0x002DCA04`).
