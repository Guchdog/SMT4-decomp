# Independent review: ComWin final-address study

The private runner compiled the candidate at the final callback address, verified the 148-byte slot, replayed the IPS and compared unchanged bytes outside the subentry. A coordinator rerun passed, captured the callback pointer 0x0011b094 and task name from original ComWin_Init at the AsdTask_CreateCalc boundary, and compared the original and staged entry for post-init state 0 and a state-1 widget fixture. It observed 128 changed bytes within the slot and IPS roundtrip success.

Allocation, task-manager registration and widget calls use explicit models; invocation through the captured pointer is synthetic, not a scheduled runtime call. The candidate still overlaps the InfoWin_DrawUp ledger/source span, and the experiment has not modified production source, ledger or an installed patch. Real scheduler, widget behavior and paired runtime remain open.
