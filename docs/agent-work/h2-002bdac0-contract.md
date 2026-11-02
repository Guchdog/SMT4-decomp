# 0x002BDAC0: table-selected position setup

## Contract and ABI

Pinned ARM function 0x002BDAC0..0x002BDB2B is 108 bytes, a leaf without literals or calls. Incoming r0 is object pointer, r1 is the complete 32-bit table index, r2 is a 32-bit selection value. It first reads a 32-bit table pointer at object+0x4C. If that pointer is zero it returns immediately without writes or any table read; object itself must be readable even for the null-table branch. It returns the original r0 in all normal paths; existing callers generally declare/use it as void, so any typed interface must preserve the machine ABI and avoid assuming a meaningful high-level pointer return. No SP, callee-saved or VFP registers are touched; r1-r3/r12 and CPSR are clobbered.

If table is nonzero, operations occur in this exact order: halfword store low 16 bits of r1 at object+0x50; halfword zero at +0x52; byte zero at +0x86 then +0x8A; calculate table + (12*r1 modulo 2^32); byte store low 8 bits of r2 at +0x54. If full r2 is zero, load signed 16-bit values from entry+0 and entry+2; otherwise load signed halfwords from entry+4 and entry+6. After each load, multiply its sign-extended 32-bit representation by 4096 modulo 2^32 and write as a 32-bit word to object+0x0C then +0x10, respectively. The second load occurs after the first output store, which matters when object and table alias. Full-width r2 is tested, so r2=0x100 stores byte zero but selects the nonzero offsets. Full-width index is used for addressing even though its stored representation is truncated. Avoid C++ signed left shift of negative values.

Stride 12 and four signed halfword fields at offsets 0,2,4,6 follow directly from ARM. The remaining four entry bytes are not read by this function; no valid element count or index maximum can be inferred from the stride. There is no bounds check. All derived table addresses must be valid/readable and suitably aligned under the execution domain; table may alias object unless a narrower domain is explicitly justified. Overlap can alter subsequent reads due to the precise stores above. No VFP, floating conversion, direct global access, or other non-stack writes occur. Faults, unaligned access behavior, concurrent changes and arbitrary wrapped address mapping remain unverified.

## TitleConfig callers and table origin

`TitleConfig_Calc` (0x001EA928) loads `work` from global and dispatches on work+8. In state 1, the cancel/input path after 0x002C1830(1,1) returns nonzero invokes 0x001EAF38 with r0=work+0x5C, r1=1, r2=0, then restores config and sets state 3. In state 2, after 0x0019DFBC(work[0x154]) returns 2 and 0x00297674 returns 0, 0x001EAFD4 invokes the same arguments, sets config[4]=1 and state 3. The other state-2 result 1 sets state 1 without this call. `titleConfig_func_002f4ca0` calls at 0x002F4D98 with r0=work+0x5C, index=0 and selector=0, immediately after 0x002BDB2C initializes that subobject. In pinned 0x002BDB2C at 0x002BDB7C..80, object+0x4C receives word [its r3+0x0C]; here r3=work+0x3C. This traces a pointer source, not a proven resource array size or validity; index 0 and 1 are observed call arguments, not proof that two entries exist in every runtime state. Resource construction/loading and runtime values remain unverified.

## Direct callers in the pinned image

The following exhaustive word-aligned raw ARM branch-immediate scan identifies candidate direct sites; conditional B is included. Literal/data false positives, Thumb, register-indirect and dynamic calls are outside this scan. Nearby function names come from the frozen ledger and are not proof that bytes represent reachable code. No exact aligned pointer to this address was found.

| Branch | Containing ledger function | PCs |
| --- | --- | --- |
| B | `camp_func_001f5db4` / `0x001F5DB4` | `0x001F5DCC` |
| B | `camp_func_00206874` / `0x00206874` | `0x00206A10` |
| B | `func_00218aa0` / `0x00218AA0` | `0x00218ADC` |
| B | `shop_func_002333d4` / `0x002333D4` | `0x0023340C`, `0x0023341C`, `0x0023342C`, `0x0023343C`, `0x00233458`, `0x00233468`, `0x00233478` |
| B | `camp_func_0026a800` / `0x0026A800` | `0x0026A864` |
| B | `camp_func_0028c0a8` / `0x0028C0A8` | `0x0028C0B4` |
| B | `camp_func_0028c0b8` / `0x0028C0B8` | `0x0028C0E4` |
| B | `camp_func_0028c204` / `0x0028C204` | `0x0028C210` |
| B | `camp_func_0028c214` / `0x0028C214` | `0x0028C244` |
| B | `camp_func_0028c24c` / `0x0028C24C` | `0x0028C288` |
| B | `script_vm_func_00295e48` / `0x00295E48` | `0x00295E6C` |
| B | `camp_func_0039779c` / `0x0039779C` | `0x00397AF4` |
| B | `engine_func_00399594` / `0x00399594` | `0x0039981C` |
| B | `shop_func_0039be44` / `0x0039BE44` | `0x0039BF10` |
| B | `ui_func_0039c4f0` / `0x0039C4F0` | `0x0039C558` |
| B | `ui_func_0039cb84` / `0x0039CB84` | `0x0039CBE4` |
| BL | `InfoWin_Init` / `0x0010AF84` | `0x0010B0B8`, `0x0010B0E4` |
| BL | `InfoWin_Calc` / `0x0011B1BC` | `0x0011B230`, `0x0011B32C` |
| BL | `camp_func_00138940` / `0x00138940` | `0x0013897C` |
| BL | `Camp_MainProc` / `0x0017FE9C` | `0x001802B0`, `0x001803B8`, `0x00180540`, `0x001808D4`, `0x00181084`, `0x001812FC`, `0x00181A48`, `0x00181AB0`, `0x00182500`, `0x0018254C`, `0x0018535C`, `0x0018538C`, `0x001863D8`, `0x0018682C`, `0x0018685C`, `0x00186904` |
| BL | `engine_func_0018844c` / `0x0018844C` | `0x00189378` |
| BL | `camp_func_0018a2e0` / `0x0018A2E0` | `0x0018A3EC`, `0x0018A5E4`, `0x0018A618`, `0x0018A870`, `0x0018AB14` |
| BL | `Result_Calc` / `0x0018BFEC` | `0x0018D5C8`, `0x0018D5E8`, `0x0018EEC4`, `0x0018F068` |
| BL | `Status_CalcTaskCallback` / `0x0018F560` | `0x0018FCF4`, `0x0018FDD0`, `0x0018FDE0`, `0x001904AC` |
| BL | `PlayLog_func_00194dbc` / `0x00194DBC` | `0x00194EB4` |
| BL | `camp_func_00195044` / `0x00195044` | `0x00195334` |
| BL | `FlowScript_EventVmExecute` / `0x001955BC` | `0x00195A08`, `0x00195A40`, `0x00196184`, `0x00196414`, `0x00196684`, `0x00196698`, `0x0019688C`, `0x00196928`, `0x00196988`, `0x001969D8`, `0x00196B54`, `0x00196BB4`, `0x00196C1C` |
| BL | `battle_func_00199a94` / `0x00199A94` | `0x00199D50`, `0x00199E70` |
| BL | `Camp_DrawStereoViews` / `0x0019A3EC` | `0x0019CB80` |
| BL | `script_vm_func_001afb08` / `0x001AFB08` | `0x001AFB74`, `0x001AFDAC`, `0x001AFE20`, `0x001B022C` |
| BL | `FlowScript_EvalStateControl` / `0x001C3ED4` | `0x001C405C`, `0x001C4078`, `0x001C40B4`, `0x001C40D0`, `0x001C436C`, `0x001C43A8`, `0x001C5B24`, `0x001C5B40`, `0x001C625C`, `0x001C67E4`, `0x001C6800`, `0x001C71B0`, `0x001C71D8`, `0x001C71F0`, `0x001C73A4`, `0x001C73CC`, `0x001C73E4`, `0x001C86B0`, `0x001C86D8`, `0x001C8714`, `0x001C873C`, `0x001C8758` |
| BL | `func_001c8d28` / `0x001C8D28` | `0x001C9530`, `0x001C9540`, `0x001C9550`, `0x001CA2CC`, `0x001CA2DC`, `0x001CA2EC` |
| BL | `StatusDown_CalcTaskCallback` / `0x001CA648` | `0x001CA850`, `0x001CA8B8`, `0x001CAC50`, `0x001CB0F4`, `0x001CB318`, `0x001CC004`, `0x001CC338` |
| BL | `Ui_StatusScreenSkills` / `0x001CE98C` | `0x001CEB30`, `0x001CFC24` |
| BL | `camp_func_001d0650` / `0x001D0650` | `0x001D07AC`, `0x001D0870`, `0x001D0950`, `0x001D0AE8`, `0x001D0EDC`, `0x001D0F58` |
| BL | `StatusDown_OpenDefaultView` / `0x001DDAB4` | `0x001DDACC` |
| BL | `camp_func_001e1000` / `0x001E1000` | `0x001E1090`, `0x001E1100` |
| BL | `script_vm_func_001ea928` / `0x001EA928` | `0x001EAF38`, `0x001EAFD4` |
| BL | `camp_func_001ee99c` / `0x001EE99C` | `0x001EEC84` |
| BL | `Unite_Setup` / `0x001F2F58` | `0x001F32E4`, `0x001F33C0`, `0x001F33EC` |
| BL | `saveLoadUI_Calc` / `0x00202950` | `0x00202CB4`, `0x00202CC4`, `0x00202CD4` |
| BL | `camp_func_002034dc` / `0x002034DC` | `0x00203504` |
| BL | `script_vm_func_002041f4` / `0x002041F4` | `0x002042A8`, `0x00204D0C` |
| BL | `camp_func_0020610c` / `0x0020610C` | `0x00206124` |
| BL | `camp_func_00212024` / `0x00212024` | `0x002120C0`, `0x00212108` |
| BL | `script_vm_func_00215bd8` / `0x00215BD8` | `0x00215C1C` |
| BL | `camp_func_002178a0` / `0x002178A0` | `0x0021795C`, `0x00217B14`, `0x00217D10`, `0x00217D40`, `0x00217FAC`, `0x00217FDC` |
| BL | `script_vm_func_00223c00` / `0x00223C00` | `0x00223C5C`, `0x00223C84` |
| BL | `engine_func_002306ec` / `0x002306EC` | `0x00230734`, `0x00230768` |
| BL | `unite_func_00233600` / `0x00233600` | `0x002336E4`, `0x00233710` |
| BL | `script_vm_func_00235614` / `0x00235614` | `0x00235684`, `0x002356AC` |
| BL | `camp_func_002488a8` / `0x002488A8` | `0x002488FC`, `0x00248BC4` |
| BL | `engine_func_00253538` / `0x00253538` | `0x002535F8` |
| BL | `UIQuest_func_0026a02c` / `0x0026A02C` | `0x0026A2E0`, `0x0026A334`, `0x0026A51C`, `0x0026A564` |
| BL | `camp_func_0026a800` / `0x0026A800` | `0x0026A81C`, `0x0026A840` |
| BL | `camp_func_0026d810` / `0x0026D810` | `0x0026D858`, `0x0026D878` |
| BL | `camp_func_0026d910` / `0x0026D910` | `0x0026D95C`, `0x0026D970` |
| BL | `script_vm_func_0027e9e4` / `0x0027E9E4` | `0x0027EA08` |
| BL | `script_vm_func_0027ea24` / `0x0027EA24` | `0x0027EA9C` |
| BL | `script_vm_func_00289f00` / `0x00289F00` | `0x00289FAC` |
| BL | `camp_func_0028a5d0` / `0x0028A5D0` | `0x0028A614`, `0x0028A640`, `0x0028A65C` |
| BL | `Camp_Init` / `0x0028A688` | `0x0028A84C`, `0x0028A880`, `0x0028A8AC`, `0x0028A910`, `0x0028A954` |
| BL | `Camp_Calc` / `0x0028AB8C` | `0x0028B970`, `0x0028BA08` |
| BL | `PartyPanel_DrawAndCalc` / `0x0028BA60` | `0x0028BD40`, `0x0028BDA4`, `0x0028BDF0`, `0x0028BEA4` |
| BL | `Status_Init` / `0x0028C2A8` | `0x0028C4B0`, `0x0028C56C`, `0x0028C5B0`, `0x0028C5E4`, `0x0028C61C`, `0x0028C7D8`, `0x0028C80C` |
| BL | `script_vm_func_00290544` / `0x00290544` | `0x00290588`, `0x00290628` |
| BL | `StatusDown_SetDisplayMode` / `0x00292F44` | `0x00292F80`, `0x00292FA8` |
| BL | `script_vm_func_0029350c` / `0x0029350C` | `0x00293530` |
| BL | `script_vm_func_0029357c` / `0x0029357C` | `0x002935A0` |
| BL | `StatusDown_Close` / `0x0029BFEC` | `0x0029C010` |
| BL | `script_vm_func_0029ccf8` / `0x0029CCF8` | `0x0029CDF0`, `0x0029CE30`, `0x0029CE44`, `0x0029CE58`, `0x0029CE88`, `0x0029CE9C` |
| BL | `camp_func_0029d924` / `0x0029D924` | `0x0029D98C` |
| BL | `SortMenu_Init` / `0x0029E63C` | `0x0029E7DC` |
| BL | `camp_func_0029ea28` / `0x0029EA28` | `0x0029EA80`, `0x0029EA94` |
| BL | `camp_func_0029feac` / `0x0029FEAC` | `0x002A028C` |
| BL | `camp_func_002ae874` / `0x002AE874` | `0x002AEA14` |
| BL | `ui_func_002b85bc` / `0x002B85BC` | `0x002B8718` |
| BL | `ui_func_002bf9f0` / `0x002BF9F0` | `0x002BFB48`, `0x002BFB78` |
| BL | `script_vm_func_002cf6d4` / `0x002CF6D4` | `0x002CF72C` |
| BL | `StatusDown_Init` / `0x002D931C` | `0x002D9440`, `0x002D94BC`, `0x002D94E8`, `0x002D9514` |
| BL | `GauntletAppMenu_Init` / `0x002E2454` | `0x002E25F4`, `0x002E2648` |
| BL | `camp_func_002e42f8` / `0x002E42F8` | `0x002E4310` |
| BL | `camp_func_002eff60` / `0x002EFF60` | `0x002F0024`, `0x002F00D4` |
| BL | `titleConfig_func_002f4ca0` / `0x002F4CA0` | `0x002F4D98` |
| BL | `script_vm_func_002fec44` / `0x002FEC44` | `0x002FEC8C` |
| BL | `StatusDown_OpenCategorySelect` / `0x00311494` | `0x00311548` |
| BL | `script_vm_func_00311618` / `0x00311618` | `0x003116D8`, `0x003116EC` |
| BL | `camp_func_00318da8` / `0x00318DA8` | `0x00318DD0` |
| BL | `Camp_SubModeProcess` / `0x0032CB08` | `0x0032D12C`, `0x0032D400`, `0x0032D414`, `0x0032D438`, `0x0032D470`, `0x0032D484`, `0x0032D4A8`, `0x0032D964`, `0x0032D988`, `0x0032D9A8`, `0x0032DB88`, `0x0032DBC0`, `0x0032DC88`, `0x0032DE90`, `0x0032DFE4`, `0x0032E110`, `0x0032E328`, `0x0032E34C`, `0x0032E468`, `0x0032E49C`, `0x0032E7C8`, `0x0032E7EC`, `0x0032E938`, `0x0032EE40`, `0x0032EE50`, `0x0032EE74`, `0x0032F128`, `0x0032F14C`, `0x0032F410`, `0x0032F47C`, `0x0032F81C`, `0x0032F840`, `0x0032F860`, `0x0032F8D8`, `0x0032F8FC`, `0x0032F91C`, `0x0032FA08`, `0x0032FA2C` |
| BL | `camp_func_0033138c` / `0x0033138C` | `0x003314F8`, `0x00331584` |
| BL | `Camp_WhisperSkillTransfer` / `0x00332100` | `0x0033288C`, `0x003328A0`, `0x003328C4`, `0x00332A68`, `0x00332A7C`, `0x00332AA0`, `0x00332B38`, `0x00332B4C`, `0x00332B70` |
| BL | `script_vm_func_003986c8` / `0x003986C8` | `0x003989C4` |
| BL | `ui_func_00398a90` / `0x00398A90` | `0x00398B28` |
| BL | `engine_func_00399594` / `0x00399594` | `0x003996A0`, `0x003997D0` |
| BL | `shop_func_0039be44` / `0x0039BE44` | `0x0039BED0` |
| BL | `script_vm_func_003b7d78` / `0x003B7D78` | `0x003B7F8C`, `0x003B7FC8`, `0x003B8028`, `0x003B805C`, `0x003B8090` |

## Conversion and testing recommendation

This is a useful bounded H2 slice if its typed interface, register-visible return and broad caller interactions are reviewed. Preserve original behavior for null table and ordering; do not assume that a nonzero selector byte is equivalent to a nonzero selector word. Differential tests should include null and valid tables, both selector paths including 0x100 and high bits, indices 0/1 and other safely mapped slots, low-16 truncation, signed halfword extremes and negatives, canary memory, preserved registers/SP, and exact ordered reads/writes. Include object/table overlap affecting later table reads, or explicitly constrain and justify disjointness and leave aliasing unsupported. Negative controls should mutate stride, selector comparison, sign extension, output offsets and store order. Compare original/candidate caller compositions for both TitleConfig_Calc states and initialization with identical valid memory; verify original target address, ARM interworking and slot size, affected consumers, independent review and integrated runtime. No compilation, ARM execution or runtime was performed here.

## Provenance

Pinned image SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; `src/engine/leaf_batch46_b.cpp` SHA-256 `c76ab50c12589404ca81e35373c8b136c50c91eb63c5af805bf05cc44c6081c7`. The source `src/engine/leaf_batch13_c.cpp` changed during run001 and was restored. Fresh run002 verification confirms all declared input hashes match, including this source at `03dfaa0570f5dd9fcd6e9de0f76fdb3d0d66909ab639f9d21ce285e1a35a659c`. Original code facts above derive from the unchanged pinned image. Read-only Capstone disassembly, branch scans and input hash verification exited 0.
