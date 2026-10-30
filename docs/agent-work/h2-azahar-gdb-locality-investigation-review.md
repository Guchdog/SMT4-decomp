# H2 Azahar listener locality review

## Finding

**A localhost-only RSP probe is not defensible from the saved evidence without either a firewall change or additional authoritative evidence of the effective loopback decision.** The broad rule proves a non-loopback block for its match domain; it does not grant an allow to loopback. Since Azahar binds `INADDR_ANY`, local-only access depends on Windows Firewall's effective decision for this exact staged executable, port, and loopback flow. The current snapshot does not establish that decision.

This narrows the prior investigation's conclusion: the non-loopback restriction is supported by static policy evidence, but the claim that the same snapshot permits an RSP attempt to `127.0.0.1` is not. A future RSP task should remain gated until a fresh, read-only effective-policy result proves an applicable loopback allow, or an administrator reviews a narrowly scoped allow for the staged executable/TCP port and loopback addresses. This review made no firewall change and performed no Azahar launch, listener/network probe, RSP, or input action.

## Independent evidence review

I verified all 14 input hashes declared by run-001 `task.json`; they match. The saved `netsh advfirewall show allprofiles` output reports Domain, Private, and Public enabled, each with `BlockInbound,AllowOutbound`. It also displays `LocalFirewallRules N/A (solo almacén de GPO)`. The separate older ActiveStore profile query recorded `AllowLocalFirewallRules=True`; this difference in display/source should not be silently treated as effective-rule proof.

The saved `codex_sandbox_offline_block_inbound` stanza is enabled, inbound, `Block`, protocol `Any`, applies to Domain/Private/Public, and has interface type `Any`. Its remote ranges are:

- IPv4: `0.0.0.0-126.255.255.255` and `128.0.0.0-255.255.255.255`, leaving `127.0.0.0/8` outside this rule.
- IPv6: `::-::` and `::2-ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff`, leaving `::1` outside this rule.

For the exact run-007 application path `E:\smt4decomp\build\h2-runtime\h2-azahar-rsp-probe\run-007-59931\app\azahar.exe`, the inbound dump contains four enabled exact-path rules, each with local/remote address and ports `Any`:

| Profile | Protocol | Action |
| --- | --- | --- |
| Public | TCP | Block |
| Public | UDP | Block |
| Private | UDP | Allow |
| Private | TCP | Allow |

There is no matching Domain-profile rule in the saved dump. For the TCP GDB listener, the Private allow cannot be assumed to apply to loopback absent evidence of the loopback flow's effective profile/policy. If classified Public, the exact app block is an explicit deny; if Domain, the recorded default is Block and there is no exact-path Domain allow. The network-profile snapshot lists Wintun and Wi-Fi as Public and Radmin VPN as Private, but those interface categories do not identify the effective profile or applicable filter for a loopback connection.

Microsoft Learn documents that explicit block rules take precedence over conflicting allow rules, and that inbound traffic is blocked by default unless a rule permits it ([Windows Firewall rules](https://learn.microsoft.com/en-us/windows/security/operating-system-security/network-security/windows-firewall/rules), [Windows Firewall overview](https://learn.microsoft.com/en-us/windows/security/operating-system-security/network-security/windows-firewall/)). Thus the all-profile block wins for non-loopback traffic even where the staged executable has a Private allow. Its loopback exclusions mean only that this particular block does not match those loopback source ranges; they do not create a permit. The saved prior investigation also records that `Get-NetFirewallRule -PolicyStore ActiveStore -Direction Inbound -Enabled True` failed with Access Denied. No effective-filter query or permitted loopback connection is available to close this gap.

## Pinned Azahar claims and identity

The prior report identifies Azahar 2126.2 at commit `219d743a1e698101fe1ab8bef43e6563126c3c27`; the run-007 staged executable hash was re-read and matches `c248414eb5328cb8bb720775ace6959898e2f50a0a10221c3a1e7a14190183eb`. The pinned [`gdbstub.cpp`](https://github.com/azahar-emu/azahar/blob/219d743a1e698101fe1ab8bef43e6563126c3c27/src/core/gdbstub/gdbstub.cpp) initializes the IPv4 listener address with `INADDR_ANY`. The inspected pinned [`citra_qt.cpp`](https://github.com/azahar-emu/azahar/blob/219d743a1e698101fe1ab8bef43e6563126c3c27/src/citra_qt/citra_qt.cpp) `-g` / `--gdbport` option accepts a numeric port, and [`settings.h`](https://github.com/azahar-emu/azahar/blob/219d743a1e698101fe1ab8bef43e6563126c3c27/src/common/settings.h) exposes the enable flag and port, not a bind address. These support the source-level wildcard/no-address-override claim for the inspected interfaces and pinned revision. They do not by themselves prove runtime socket state; separately, the prior run-007 report observed `0.0.0.0` and rejected before RSP.

## Required next evidence

Keep RSP blocked pending either (a) a read-only, authoritative effective-policy result showing that the exact staged executable's selected TCP port is permitted for a loopback connection while non-loopback remains blocked, or (b) administrator review/application of a narrowly scoped allow for that exact path and port with local and remote addresses limited to `127.0.0.1`. Then recheck the policy immediately before any separately authorized runtime attempt, retain the process-owner and staged-path gates, and connect only to `127.0.0.1`. A successful connection is not established by this review.
