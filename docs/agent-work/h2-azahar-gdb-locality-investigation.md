# H2 Azahar GDB listener locality investigation — run 002

## Result

The pinned Azahar GDB listener is wildcard-bound and has no inspected CLI or
configuration address override. The fresh host-policy snapshot nevertheless
shows an effective local-only inbound boundary for the already staged run-007
executable, without any firewall edits: an enabled explicit block rule covers
every non-loopback IPv4/IPv6 remote source on all firewall profiles, and
Microsoft documents that explicit block rules override conflicting allows. The
matching staged-app rule allows TCP on Private and blocks TCP on Public. The
global block leaves only loopback source ranges (`127.0.0.0/8` and `::1`) out of
its scope. A continuation can therefore use only `127.0.0.1` and abort before
RSP if the policy snapshot or exact app rule differs.

This is a policy-based restriction, not a listener bind restriction. No Azahar
launch, listener probe, RSP connection, firewall change, profile/game write, or
keyboard/mouse action occurred in this investigation. The currently running
installed Azahar process (`E:\emulador3ds\azahar.exe`, PID 14948) was only
listed; it was not connected to or controlled.

## Pinned source

The inspected executable is Azahar 2126.2, commit
`219d743a1e698101fe1ab8bef43e6563126c3c27`, SHA-256
`c248414eb5328cb8bb720775ace6959898e2f50a0a10221c3a1e7a14190183eb`. The
matching source initializes the GDB listener address to `INADDR_ANY`; the Qt
`-g` / `--gdbport` argument parses only a numeric port, and the settings expose
only an enable flag plus port. No listener address setting is present in the
inspected source/configuration.

Pinned source links: [GDB stub](https://github.com/azahar-emu/azahar/blob/219d743a1e698101fe1ab8bef43e6563126c3c27/src/core/gdbstub/gdbstub.cpp),
[Qt command-line parser](https://github.com/azahar-emu/azahar/blob/219d743a1e698101fe1ab8bef43e6563126c3c27/src/citra_qt/citra_qt.cpp),
[debug settings](https://github.com/azahar-emu/azahar/blob/219d743a1e698101fe1ab8bef43e6563126c3c27/src/common/settings.h).

## Current host policy evidence

Read-only commands and outputs are saved under
`build/agent-work/H2-semantic/h2-azahar-gdb-locality-investigation/run-002/checks/`.
`netsh advfirewall show allprofiles` reports Domain, Private, and Public
profiles enabled with inbound default `Block`. The enabled
`codex_sandbox_offline_block_inbound` rule applies to all three profiles and
has:

- Direction: inbound; protocol: any; interface type: any; action: block.
- IPv4 remote ranges `0.0.0.0-126.255.255.255` and
  `128.0.0.0-255.255.255.255`, excluding `127.0.0.0/8`.
- IPv6 remote ranges `::-::` and `::2-ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff`,
  excluding `::1`.

For the exact previously staged application
`E:\smt4decomp\build\h2-runtime\h2-azahar-rsp-probe\run-007-59931\app\azahar.exe`,
the current inbound rules include TCP `Allow` on Private and TCP `Block` on
Public, each for any local/remote address and port. The broad Private allow is
therefore constrained against non-loopback sources by the all-profile explicit
block rule. Microsoft Learn states that explicit block rules take precedence
over conflicting allow rules ([Windows Firewall rule precedence](https://learn.microsoft.com/en-us/windows/security/operating-system-security/network-security/windows-firewall/rules)).

The network profile query currently shows Wintun and Wi-Fi as Public and Radmin
VPN as Private. That does not change the boundary: the non-loopback block is
enabled for every profile. The source and host facts support a defensible
loopback-only connection under this snapshot; they do not prove a successful
loopback socket connection. That can be tested only after rechecking the rules
immediately before launch and enforcing `127.0.0.1` in the client.

## Continuation constraints

The next runtime packet may reuse the exact run-007 executable path so its
existing app rule remains applicable. Before launch it must verify the pinned
executable/CCI hashes, selected port is unused, all profiles remain enabled
with inbound default Block, the global rule remains enabled with exactly the
loopback exclusions above, and the staged app's Private TCP allow/Public TCP
block still match. It must then verify the launched PID owns the listener and
the log resolves both game and user data inside the stage. The client may
connect only to `127.0.0.1`; it must never try the machine's non-loopback IPs.
Any changed, missing, ambiguous, or unparsable policy/rule evidence stops the
attempt before RSP. If localhost connection is blocked, stop and preserve the
partial report; do not add a firewall rule or retry a different address.

This resolves the locality research question only for the observed host policy
and exact staged app path. It does not establish RSP packet support, guest
input delivery, or H2 behavior. No firewall state is changed by this task.
