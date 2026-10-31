# Milestone H11: Shops, Black Market, and Terminals

- **Milestone Code:** H11
- **Status:** Completed & Closed (2026-10-30)
- **Scope:** Commercial and transportation subsystems: buy/sell mechanics (`src/shop/`), black market specialty stock verification, equipment compatibility checks, inventory purchase limit clamping, and persistent Terminal network teleport activation bitfields.
- **Base Image:** `code.h10-final.bin` (`8233530ba0df84acc66bf6196153403d257e8bbfa1aca1537fafcabc51bdc4e3`)
- **Composed Binary:** `code.h11-final.bin` (`0520e88c5fb70e16e8c5071d097fb6d3de3c9c55e57aaef8d59fbbe998a9d843`)
- **LayeredFS IPS Mod:** `code.h11-final.ips` (29,414 bytes, `d3c581632f3bb90fd25d0626927f4efc539f87dc1629c9ab7254b8a467df09ed`)
- **Total Headroom Margin:** +176 bytes across 8 candidates (448 B compiled / 624 B allocated window).

## 1. Reconstructed Subsystem Candidates

1. `Shop_SetSelectedItem` (`0x0022A60C`, 52 B window, 36 B candidate, +16 B margin):
   Updates active catalog item selection in `ShopContext` at offset `+0x4C` and marks dirty flag `+0x61` when modified while unlocked (`+0x62 == 0`).
2. `Shop_CheckHasNewInventoryItem` (`0x0022FC98`, 48 B window, 36 B candidate, +12 B margin):
   Queries category arrival indicators via `0x0026F0D8(6)` and `0x002B902C(7)` to display "NEW" notification badges on shop tabs.
3. `Shop_CheckHasSpecialStockItem` (`0x0022FCC8`, 48 B window, 36 B candidate, +12 B margin):
   Queries underground black market special stock via `0x0026F0D8(5)` and `0x002B902C(8)` to unlock restricted catalog lists.
4. `Shop_PushItemRecord` (`0x00230680`, 108 B window, 72 B candidate, +36 B margin):
   Serializes catalog items into active shop display buffers, packing item ID, buy/sell state, and discount bitfields into compact 4-byte entries and incrementing buffer counter at `+0x1000`.
5. `Shop_IsEquipSlotMatch` (`0x00230D24`, 140 B window, 84 B candidate, +56 B margin):
   Maps item category (2..8) to party unit equipment slots via unit table lookup (`sub_2B66EC`) and checks if target item is currently equipped.
6. `Shop_CalcPurchasableQty` (`0x00230DB0`, 100 B window, 72 B candidate, +28 B margin):
   Evaluates shop inventory stock, clamps desired purchase quantity to 99, queries player bag capacity (`sub_2B9100`), subtracts current inventory count (`sub_28FDE4`), and returns maximum purchasable quantity.
7. `Terminal_SetUnlockFlag` (`0x00263734`, 68 B window, 64 B candidate, +4 B margin):
   Modifies terminal activation bitfields across the 32-node network stored in persistent game work (`0x0043E2A8` -> `sub_2BBD40` + 8).
8. `Terminal_IsUnlocked` (`0x00263778`, 60 B window, 48 B candidate, +12 B margin):
   Queries terminal destination availability from the 32-bit bitset, enabling teleport map markers and destination selections.

## 2. Validation and Equivalence Proof

- **Offline-First Differential Suite:** 8/8 Unicorn test harnesses passed with 100% register and memory equivalence against original code in `code.bin`. Mutation sensitivity confirmed for every candidate.
- **Caller Composition & ABI:** Preserved ARM ATPCS calling conventions, register assignments, and stack frame alignment across all calling paths.
- **Autonomous Paired Runtime Verification:** 0 register or context differences in Azahar paired execution across Title, Save Load, 250 Field scene ticks, and commercial / teleport callbacks.
- **Workflow Board Integrity:** All 89 planned tasks in `config/agent-workflows/h11.json` are accepted and independently reviewed.
