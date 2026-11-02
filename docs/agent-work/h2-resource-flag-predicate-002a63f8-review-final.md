# H2 `0x002A63F8` final narrow review (run005)

The run005 packet’s 25 pinned input hashes all match. The semantic ledger row is `0x002a63f8,24,non_matching,...`, matching the classification and the staged report’s differing final bytes.

The regenerated report SHA-256 is `901c2da3e7681ab3c122ee48c5c734310c9a51f1b1539ada670d21752af68010`; the staged manifest SHA-256 is `2df226682e405c6a2ece308342865794c145d13197091bd1a86f8606950aee0b`. Reported null-fault observations list the same Unicorn unmapped-read exception and instruction offset `8` for `original`, `temporary`, `final-vma`, and `staged`.

The runner now checks every non-original null observation against the original (`for result in null_results[1:]`) and emits the per-profile offsets. This closes the specific staged-null comparison gap identified in run004. The staged manifest continues to classify the replacement `non_matching`, fit it in the 24-byte function slot, and mark the changed range as only that function slot.

This is a narrow static artifact review; I did not rerun the differential, compile, build, or launch the emulator. Runtime remains unverified.
