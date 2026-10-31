# H9 Cathedral of Shadows: Fusion & Compendium Architecture Reconnaissance Record

- **Milestone:** H9 (Cathedral of Shadows: Fusion & Compendium / Catedral de las Sombras: Fusión y Compendio)
- **Status:** Complete & Reviewed
- **Target Subsystems:** 3D Fusion Summoning Effects, Demon Compendium Devil Book Manager, Legion Skill Selection, Legion Stereoscopic Draw Manager, Fusion/Compendium Sorting Modal, Fusion Roster Evaluator & Bucket Sorter, Compendium Demon Inspector, Dynamic Button Help HUD.

## 1. Subsystem Boundaries and Mappings

Shin Megami Tensei IV Cathedral of Shadows (Jakyou / Mido) subsystems are organized into three cooperating functional domains:

1. **3D Fusion Summoning Ritual & Particle Presentation (`0x002E315C`):**
   - `UniteEffect_Init` (`0x002E315C`, 344 B window, 244 B candidate, +100 B margin): Allocates 0x50-byte 3D fusion effect workspace (`0x002C4B84`), zeroes memory, registers calculation task `"UNITE EFFECT CALC"` (`0x002C5978`, priority 2, callback `0x00329598`) and draw task `"UNITE EFFECT DRAW"` (`0x002C4C00`, priority 0x57, callback `0x0032B258`), and initializes 3D particle lighting handles (`0x002C0BA8`, `0x002488A8`, `0x002976AC`).

2. **Demon Compendium (Devil Book) & Legion Inspection (`0x00269CC8`, `0x003AB770`, `0x003AD300`, `0x003A7AD8`):**
   - `bibleMain_Init` (`0x00269CC8`, 352 B window, 228 B candidate, +124 B margin): Demon Compendium manager initialization. Allocates 0x240-byte compendium workspace (`0x002C4B84`), zeroes memory, registers `"BIBLE CALC"` (`0x002C5978`, priority 2, callback `0x00293188`) and `"BIBLE DRAW"` (`0x002C4C00`, priority 0x57, callback `0x00293774`), stores handle into `g_BibleMainWork_0043da10`, and loads compendium script/mbm assets.
   - `bibleLegionSkill_Init` (`0x003AB770`, 592 B window, 404 B candidate, +188 B margin): Cathedral of Shadows Legion Skill setup and UI list initialization. Allocates 0x1B8-byte workspace, registers calculation task `"BIBLE LEGION SKILL CALC"` (priority 2, callback `0x0033B6D8`) and draw task `"BIBLE LEGION SKILL DRAW"` (priority 0x57, callback `0x0033BD54`), clears active skill bitfield, and initializes touch UI list entries.
   - `bibleLegionDraw_Init` (`0x003AD300`, 596 B window, 484 B candidate, +112 B margin): Legion upper/lower stereoscopic draw manager setup (`0x0043D9E0`). Zeroes manager buffer, initializes upper 3D screen rendering node and lower touchscreen sprite nodes (`0x002C4C00`), sets stereoscopic depth separation parameters, and binds vertex/index buffers.
   - `bibleDevil_Init` (`0x003A7AD8`, 668 B window, 504 B candidate, +164 B margin): Compendium demon inspector. Allocates 0x1F0-byte demon view workspace, registers calculation task `"BIBLE DEVIL CALC"` (callback `0x00336210`) and draw task `"BIBLE DEVIL DRAW"` (callback `0x003366D4`), loads 3D demon model viewport, binds elemental affinity badges, and initializes demon stat layout.

3. **Demon Fusion Engine, Roster Sorting & Button Help HUD (`0x0029E63C`, `0x003C9EBC`, `0x0028D974`):**
   - `SortMenu_Init` (`0x0029E63C`, 644 B window, 364 B candidate, +280 B margin): Demon fusion and compendium sorting modal and comparator dispatcher. Initializes `g_SortMenuManager_0043dd20`, registers modal calculation task (callback `0x0020B440`) and draw task (callback `0x0020BA90`), loads UI layout tables, and binds sorting comparator callbacks for Level, Race, HP, MP, St, Dx, Ma, Ag, Lu, and Alphabetical order.
   - `UniteCtrl_RosterPopulate` (`0x003C9EBC`, 664 B window, 504 B candidate, +160 B margin): Demon fusion candidate roster counter, race bucket allocator, and qsort sorter. Iterates active party and stock demons, partitions eligible fusion ingredients into race-indexed buckets, computes candidate combinations, executes `qsort_002b7f0a` using fusion priority criteria, and zeroes tail boundary slots (`+0x118..+0x17C`).
   - `ButtonHelp_Init` (`0x0028D974`, 736 B window, 604 B candidate, +132 B margin): Dynamic button prompt HUD and input helper. Initializes `g_ButtonHelpManager_0043da28`, registers calc task (callback `0x00207394`) and draw task (callback `0x002079C8`), allocates prompt text layout buffers, loads glyph sprites for 3DS face buttons (A, B, X, Y, L, R, Start, Select), and sets dynamic visibility flags.
