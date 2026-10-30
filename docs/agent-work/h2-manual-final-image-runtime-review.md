# Review — H2 corrected final-image runtime record

## Recommendation

The runtime report is acceptable as partial manual evidence and H2 correctly
remains open. The prior review identified a seed-provenance wording issue. The
updated report now says the NAND config hash matches the seed and both final
profiles, while the title custom-config hash
`1c6e8b89795e80a5976540da8a9d45be8c03759bf903b537a15b7dd76b046f7c` matches
only the two post-run profiles and is absent from the pristine seed manifest.
This correction is accurate; no remaining correction is needed for the
bounded runtime claims.

## Independent identity checks

I hashed the staged files directly. Both portable `azahar.exe` files are
38,274,048 bytes and SHA-256
`c248414eb5328cb8bb720775ace6959898e2f50a0a10221c3a1e7a14190183eb`. The
shared CCI is 1,878,011,904 bytes and SHA-256
`9cc760c2f37da9a4a3657e918e0eaebb3e8e80a91047e5c18f95aedf0242b4c2`. The
patched profile's IPS is 6,439 bytes and SHA-256
`bb9fc65956b2261468825a3732a2019cdd69226a6402309711bbeadfb26ac808`. These
match the staging manifest and runtime launch records. The manifest identifies
the final patched image as
`cd095feb4c8034874a2ef4661356cb131e0e240cfc907f454f12b83d05c13bf4` and
records that the standalone IPS is built from the pinned original. The launch
records consistently point at the staged profile executable, that profile's
`app` working directory, and the shared CCI.

The launch records, staged configs and logs all report GDB/RPC disabled. The
patched final-session log explicitly reports the staged `code.ips` patching
`code.bin`; the original log has no patch-application event. The post-run
inventory shows the same NAND config and custom-config hashes in both profiles
and the intended IPS only in patched. The stage seed manifest contains the
NAND config and `sysdata/mac.txt`, but not the title custom-config file. Logs,
shader caches and Azahar runtime metadata differ, which the report notes
separately.

## Runtime claim audit

The user-reported observations are separated from process/log evidence. The
five recorded launch PIDs and timestamps are consistent with the task summary:
patched 14284, 14728, 20212; original 24164, 1836. The final logs are hash-pinned
and the final Windows Application event query found no Azahar crash event in
the queried window. The current process query also found no live Azahar
process. There are no captured process exit codes, so “closed/no longer
running” is supported; a clean exit status is not claimed.

The runtime document accurately limits human observations to what was
reported: Audio Settings stays open in the corrected image; initial slider
positions looked the same; patched BGM cancel restored value and sound; A OK
kept BGM, SE and Voice changes on re-entry for the running session; patched
BGM returned to its starting position after restart, matching the earlier
original BGM observation; and all sliders clamped at both ends in both
profiles. It explicitly says exact values, matching input timings, guest
`g_ConfigBytes[0..2]`, and SE/Voice restart persistence were not recorded.
These statements do not imply that every button sequence was repeated in both
profiles.

The older original runtime report agrees with the BGM cancel, in-session
confirm and restart statements. The corrected final image report appropriately
supersedes the earlier patched-close observation only for the tested final
image; it does not assert which individual code change caused the prior crash
to stop. The milestone now describes runtime as partial and retains its open
status. Offline callback scheduling and HLE boundaries also remain open, as
the milestone and integrated-image report state.

This is an artifact and claim review only. I did not run Azahar, tests, a
debugger or profile changes. The runtime document and report hashes match the
corrected handoff. The runtime record is acceptable as partial evidence; this
does not close H2.
