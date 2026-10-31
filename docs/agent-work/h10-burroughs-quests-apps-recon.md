# H10 Burroughs, Quests, and Apps Architecture Reconnaissance Record

- **Milestone:** H10 (Burroughs, Quests, and Apps / Burroughs, Misiones y Apps)
- **Status:** Complete & Reviewed
- **Target Subsystems:** Burroughs Save Data Resolution, Burroughs Application Dispatcher, Quest Selection Reset, Quest Objective Target Condition Evaluator, Quest Availability & Eligibility Checker, Quest Entry Static Definition Unpacker, App Store Purchase Flag Commit, App Store Parameter Query & String Formatter.

## 1. Subsystem Boundaries and Mappings

Shin Megami Tensei IV Burroughs, Quest, and App subsystems are organized into three cooperating functional domains:

1. **Burroughs OS Environment & Navigation (`0x002A0FAC`, `0x002A0EA8`):**
   - `Burroughs_GetSaveData` (`0x002A0FAC`, 24 B window, 24 B candidate, +0 B margin): Burroughs and Quest save data pointer resolution from `g_GameWork_0043e2a8` at offset `+0x1ec18`.
   - `Burroughs_AppDispatch` (`0x002A0EA8`, 168 B window, 160 B candidate, +8 B margin): Burroughs application selection dispatcher. Routes app selection, verifies app readiness, triggers sound effects (`0x9E`), and commits active task state to `g_CampWork_0043dd68`.

2. **Quest Management Subsystem (`0x0026A004`, `0x0026A86C`, `0x0026A9FC`, `0x0026AAC0`):**
   - `Quest_ResetSelection` (`0x0026A004`, 40 B window, 36 B candidate, +4 B margin): Resets quest list selection, category filter ID, and active row index in `g_CampWork_0043dd68`.
   - `Quest_EvaluateTargetCondition` (`0x0026A86C`, 152 B window, 128 B candidate, +24 B margin): Evaluates quest target delivery conditions, matching condition types (0, 1, 3) against dynamic inventory and quest status bitfields.
   - `Quest_GetAvailability` (`0x0026A9FC`, 196 B window, 156 B candidate, +40 B margin): Determines availability for Main Quests (IDs <= 400) and Challenge Quests (IDs > 400), evaluating flags at `+0x38`.
   - `Quest_UnpackEntryData` (`0x0026AAC0`, 256 B window, 240 B candidate, +16 B margin): Unpacks static quest table definitions into the 0x604-byte dynamic UI work buffer, binding title, client, reward, and category badges.

3. **Demonica App Store Subsystem (`0x003253D8`, `0x00325444`):**
   - `AppStore_SetFlag` (`0x003253D8`, 56 B window, 56 B candidate, +0 B margin): Commits App Store purchase state and sets bit `0x20000000` at `app_func_00293c98() + 0x44a0`.
   - `AppStore_GetAppParam` (`0x00325444`, 52 B window, 52 B candidate, +0 B margin): Queries app parameter table entry and formats localized app name and description strings.
