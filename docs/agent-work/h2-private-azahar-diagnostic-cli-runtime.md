# H2 private Azahar live runtime comparison

This is a coordinator report of paired user-controlled CLI runs against the reviewed final composed image. H2 remains open pending independent review and the missing machine-recorded input-query trace.

## Result

The original and patched runs reached Audio Settings. The user reported identical initial sliders, B-cancel restoration, A-confirm retention within a session for BGM/SE/Voice, and Min/Max clamping for all three. After restart, the user reported that all three sliders returned to their starting values in both profiles.

The live observer captured exact `g_ConfigBytes` and all 344 bytes of `TitleConfigWork` at manual checkpoints. For the confirmed BGM, SE, and Voice changes, original and patched guest state matches byte-for-byte. Both restart snapshots also match and contain the initial config value. See [the detailed report](../../build/agent-work/H2-semantic/h2-private-azahar-diagnostic-cli-runtime/run-005/runtime-report.md), [comparison JSON](../../build/agent-work/H2-semantic/h2-private-azahar-diagnostic-cli-runtime/run-005/runtime-comparison.json), and [manual action notes](../../build/agent-work/H2-semantic/h2-private-azahar-diagnostic-cli-runtime/run-005/manual-action-notes.md).

## Limits

The observer produced zero `logical_query_return` events. The user performed the same documented sequence in both runs, but the logs do not electronically establish input order, query results, or action timing. The snapshot counts differ. The cancel and boundary behavior is human-reported only. Therefore this is partial runtime evidence, not proof of the complete runtime criterion or whole-game equivalence.

Azahar binary/image/IPS/CCI pins, stage manifests, PIDs, exits, capture hashes, and preservation details are recorded in the run-005 packet. No emulator remains open. An independent reviewer must assess the exact byte comparison and the remaining trace gap before H2 status changes.
