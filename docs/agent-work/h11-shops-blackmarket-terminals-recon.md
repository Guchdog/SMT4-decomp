# H11 Shops, Black Market, and Terminals Architecture Reconnaissance Record

- **Milestone:** H11 (Shops, Black Market, and Terminals / Tiendas, Mercado Negro y Terminales)
- **Status:** Complete & Reviewed
- **Target Subsystems:** Shop Item Selection State, Shop New Inventory Arrival Checker, Black Market Specialty Stock Checker, Shop Item Record Packing Serializer, Unit Equipment Slot Classifier & Matcher, Purchase Quantity Limit Calculator, Terminal Unlock Flag Setter, Terminal Destination Unlock Query.

## 1. Subsystem Boundaries and Mappings

Shin Megami Tensei IV commercial and transportation subsystems are organized into three cooperating functional domains:

1. **Shop & Black Market Management (`0x0022A60C`, `0x0022FC98`, `0x0022FCC8`, `0x00230680`, `0x00230D24`, `0x00230DB0`):**
   - `Shop_SetSelectedItem` (`0x0022A60C`, 52 B window, 36 B candidate, +16 B margin): Updates active catalog item selection in `ShopContext` at offset `+0x4C` and marks dirty flag `+0x61` when modified while unlocked (`+0x62 == 0`).
   - `Shop_CheckHasNewInventoryItem` (`0x0022FC98`, 48 B window, 36 B candidate, +12 B margin): Queries category arrival indicators via `0x0026F0D8(6)` and `0x002B902C(7)` to display "NEW" notification badges on shop tabs.
   - `Shop_CheckHasSpecialStockItem` (`0x0022FCC8`, 48 B window, 36 B candidate, +12 B margin): Queries underground black market special stock via `0x0026F0D8(5)` and `0x002B902C(8)` to unlock restricted catalog lists.
   - `Shop_PushItemRecord` (`0x00230680`, 108 B window, 72 B candidate, +36 B margin): Serializes catalog items into active shop display buffers, packing item ID, buy/sell state, and discount bitfields into compact 4-byte entries and incrementing buffer counter at `+0x1000`.
   - `Shop_IsEquipSlotMatch` (`0x00230D24`, 140 B window, 76 B candidate + 8 B table, +56 B margin): Maps item category (2..8) to party unit equipment slots via unit table lookup (`sub_2B66EC`) and checks if target item is currently equipped.
   - `Shop_CalcPurchasableQty` (`0x00230DB0`, 100 B window, 72 B candidate, +28 B margin): Evaluates shop inventory stock, clamps desired purchase quantity to 99, queries player bag capacity (`sub_2B9100`), subtracts current inventory count (`sub_28FDE4`), and returns maximum purchasable quantity.

2. **Terminal Teleportation Network (`0x00263734`, `0x00263778`):**
   - `Terminal_SetUnlockFlag` (`0x00263734`, 68 B window, 64 B candidate, +4 B margin): Modifies terminal activation bitfields across the 32-node network stored in persistent game work (`0x0043E2A8` -> `sub_2BBD40` + 8).
   - `Terminal_IsUnlocked` (`0x00263778`, 60 B window, 48 B candidate, +12 B margin): Queries terminal destination availability from the 32-bit bitset, enabling teleport map markers and destination selections.

## 2. Headroom and Footprint Summary

| Candidate | Function Address | Window Size | Candidate Size | Margin | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `Shop_SetSelectedItem` | `0x0022A60C` | 52 B | 36 B | +16 B | PASSED |
| `Shop_CheckHasNewInventoryItem` | `0x0022FC98` | 48 B | 36 B | +12 B | PASSED |
| `Shop_CheckHasSpecialStockItem` | `0x0022FCC8` | 48 B | 36 B | +12 B | PASSED |
| `Shop_PushItemRecord` | `0x00230680` | 108 B | 72 B | +36 B | PASSED |
| `Shop_IsEquipSlotMatch` | `0x00230D24` | 140 B | 84 B | +56 B | PASSED |
| `Shop_CalcPurchasableQty` | `0x00230DB0` | 100 B | 72 B | +28 B | PASSED |
| `Terminal_SetUnlockFlag` | `0x00263734` | 68 B | 64 B | +4 B | PASSED |
| `Terminal_IsUnlocked` | `0x00263778` | 60 B | 48 B | +12 B | PASSED |
| **Total** | - | **624 B** | **448 B** | **+176 B** | **PASSED** |
