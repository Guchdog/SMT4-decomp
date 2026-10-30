# Independent review: localized Azahar listener header parser

## Disposition

Accept the parser correction for the bounded host-query contract. It fixes the prior false-empty case by requiring one complete supported header and retains fail-closed behavior for malformed output. The evidence does not establish Azahar ownership or any RSP/runtime result; the existing runtime task must preserve its PID and staged-path gates.

## Parser and test review

On Windows, `_netstat_output_encoding()` obtains the active OEM code page through `GetOEMCP()` and uses strict decoding for the `netstat.exe -ano -p tcp` subprocess output. Decode, lookup, OS, timeout, and nonzero-exit failures become `ProbeError`s. This is consistent with the implementation report's observed Spanish labels in OEM CP850 and avoids guessing from a partial field.

Header normalization applies case folding and Unicode NFKD accent removal. The parser accepts precisely the complete supported English fields (`Proto Local Address Foreign Address State PID`) or Spanish fields (`Proto Dirección local Dirección remota Estado PID`) after whitespace splitting and normalization. A bare `Proto`, missing PID, wrong address label, duplicate header, TCP row before a header, or wrong-width TCP row is rejected. A complete header without TCP rows remains the distinct valid empty-table result. Unknown localized header layouts fail closed pending characterization.

TCP rows require five fields, a recognized state token, and an ASCII decimal PID. Endpoints require numeric IP literals and bounded ports, including bracketed IPv6. Only `LISTENING` rows are collected. The owner query matches the selected local port exactly, requires every matching address to be loopback, and rejects matches spanning multiple PIDs. Multiple loopback addresses with the same PID resolve to one owner. Tests cover IPv4 and IPv6 rows, malformed addresses/rows, owner ambiguity, wildcard binding, timeout, a free port, and the live host process PID.

The recorded final suite reports 17 passing tests and successful `py_compile`; the evidence report attributes the earlier two live-query failures to strict English-only parsing and says the localized rerun passed. I did not rerun those tests or make any host query during this review.

## Runtime gate order

Static inspection confirms `_run()` stages and hashes the executable/game before launch, launches only the staged executable with the staged game path and `shell=False`, and then checks `process.poll()` during readiness polling. After readiness it re-queries the selected port and requires the sole listener owner to equal `process.pid`. It next requires staged logs to confirm both the staged profile root and game path; only after that does it call `connect_and_probe()`. An unrelated listener, ambiguous owner, non-loopback bind, process exit, or missing staged-path evidence therefore cannot reach the RSP probe through this sequence.

## Identity and limits

The producer handoff and run report identify probe SHA-256 `6e956551d9e7793a86f49cc0c6bf8ad79c198f709aaedb3ce8f3bd0f64e4e4f0`, test SHA-256 `0cb26ff2a7d7b3fd0dc44fa606eef6965aa5e0bc879eaf3b11a598c48bf17400`, and evidence report SHA-256 `93fe1e99f6e02c9d7e708e690e3e04bd655ec1f5296fe887d4bbfbb3b4374346`. I verified these file hashes against the checked-in/current files. Runtime ownership evidence is still limited to a live test listener owned by the Python process; it does not establish an Azahar-owned socket, a staged Azahar launch, profile/game log gates in a live run, or RSP behavior. No Azahar, RSP, profile/game write, or keyboard/mouse operation occurred in this review.

## Next action

Keep this correction in the offline probe. A future runtime attempt requires a fresh assigned runtime packet and must retain the process-owner equality check followed by staged profile/game path verification before any RSP connection.
