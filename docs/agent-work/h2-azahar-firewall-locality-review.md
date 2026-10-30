# H2 Azahar firewall locality review

## Result

The pinned Azahar GDB stub binds `INADDR_ANY` (IPv4 wildcard). The pinned command line and configuration expose a port and an enable flag, but no bind-address setting. A unique staged executable therefore cannot make this binary listen on loopback only by choosing another supported CLI, INI, or build option.

All three active Windows Firewall profiles are enabled with default inbound `Block` and outbound `Allow`. The active rules include `codex_sandbox_offline_block_inbound`, which applies to Domain, Private, and Public profiles and blocks inbound traffic from non-loopback IPv4/IPv6 source ranges, while excluding IPv4 127/8 and IPv6 ::1. Existing Azahar exceptions are path-specific. They do not match a newly staged executable path. This strongly supports blocking non-loopback inbound access under the current policy, but is not a proof of the effective decision for every interface and policy combination.

**Disposition: loopback permission remains unproven.** The custom block rule excludes loopback, but the profiles still default to blocking inbound connections. Static rule inspection cannot establish whether Windows Firewall permits a fresh 127.0.0.1 connection to the wildcard-bound listener without a matching allow rule. The direct `Get-NetFirewallRule` query was denied by access control, and no listener/network probe was allowed. Require an administrator to review or create an explicit inbound allow scoped to the staged executable, selected TCP port, and local/remote address 127.0.0.1 before a runtime attempt. Do not weaken the PID-owner or staged-path gates. A source rebuild that binds specifically to 127.0.0.1 is another possible route, but it is not an option supported by the pinned binary/build configuration inspected here.

## Pinned Azahar source facts

The staged executable identity recorded by the prior stage audit is Azahar 2126.2, commit `219d743a1e698101fe1ab8bef43e6563126c3c27`, SHA-256 `c248414eb5328cb8bb720775ace6959898e2f50a0a10221c3a1e7a14190183eb`.

- [`gdbstub.cpp` at the pinned commit](https://github.com/azahar-emu/azahar/blob/219d743a1e698101fe1ab8bef43e6563126c3c27/src/core/gdbstub/gdbstub.cpp#L1976-L1999) zero-initializes `sockaddr_in`, sets `AF_INET`, the configured port and `sin_addr.s_addr = INADDR_ANY`, then calls `socket`, `bind`, and `listen`.
- [`citra_qt.cpp` at the pinned commit](https://github.com/azahar-emu/azahar/blob/219d743a1e698101fe1ab8bef43e6563126c3c27/src/citra_qt/citra_qt.cpp#L280-L286) handles `-g` / `--gdbport` as a port argument. There is no address argument in this option handling.
- [`core.cpp` at the pinned commit](https://github.com/azahar-emu/azahar/blob/219d743a1e698101fe1ab8bef43e6563126c3c27/src/core/core.cpp#L787-L795) applies the override port and enables the server, or otherwise uses the GDB port and enable setting from configuration.
- [`settings.h` at the pinned commit](https://github.com/azahar-emu/azahar/blob/219d743a1e698101fe1ab8bef43e6563126c3c27/src/common/settings.h#L609-L616) defines `use_gdbstub` and `gdbstub_port`; no host or bind-address setting is present.
- [`configure_debug.ui` at the pinned commit](https://github.com/azahar-emu/azahar/blob/219d743a1e698101fe1ab8bef43e6563126c3c27/src/citra_qt/configuration/configure_debug.ui#L16-L56) exposes the enable toggle and numeric port only.
- The pinned [`CMakeLists.txt`](https://github.com/azahar-emu/azahar/blob/219d743a1e698101fe1ab8bef43e6563126c3c27/CMakeLists.txt#L118) has `ENABLE_GDBSTUB`; inspection found no listener-interface option. This is a compile-time support switch, not a loopback-bind setting.

These source facts are limited to the pinned revision and inspected files. They establish source behavior and absence of an address option in those interfaces; they do not establish any runtime socket state.

## Read-only Windows firewall evidence

Commands issued from PowerShell; all were read-only.

| Query | Result |
| --- | --- |
| `Get-NetFirewallProfile -PolicyStore ActiveStore` selecting profile, enabled state, default actions, local-rule policy, and listen notifications | Exit 0. Domain, Private, Public enabled; inbound default `Block`, outbound `Allow`; `AllowInboundRules=True`, `AllowLocalFirewallRules=True`, `NotifyOnListen=True`. |
| `Get-NetConnectionProfile` selecting interface aliases and categories | Exit 0. Wintun Public, Radmin VPN Private, Wi-Fi Public. |
| `netsh advfirewall show allprofiles` | Exit 0. All profiles on; `BlockInbound,AllowOutbound`. Netsh displayed `LocalFirewallRules N/A (solo almacén de GPO)`; the separate PowerShell profile query reported local firewall rules allowed. |
| `netsh advfirewall firewall show rule name=all dir=in verbose` | Exit 0; 766 inbound rule stanzas parsed from the output. Found the global non-loopback block described above and exact-path Azahar rules below. |
| `Get-NetFirewallRule -PolicyStore ActiveStore -Direction Inbound -Enabled True` | Exit 1, `Acceso denegado` (Access denied). No elevated retry was attempted. |

Existing TCP exceptions found by executable path:

- `E:\smt4decomp\build\h2-runtime\h2-azahar-rsp-probe\run-007-59931\app\azahar.exe`: Public Block, Private Allow.
- `E:\smt4decomp\build\h2-runtime\h2-azahar-rsp-probe\run-006-59566\app\azahar.exe`: Public Block, Private Allow.
- `E:\emulador3ds\azahar.exe`: Public Block, Private Allow.

These entries use Any for local/remote addresses and Any local port in the inspected netsh output. They are exact-path rules, so they do not apply to a fresh unique staged executable. The universal custom block is the applicable rule that covers non-loopback sources independent of executable path/port. Its exclusion of loopback is evidence only that this specific block rule does not match loopback; default inbound Block remains in force absent a matching allow or other applicable policy.

The selected port in the query review was hypothetical TCP 62497. It was not reserved, probed, or used. The static output did not reveal a port-specific rule for it. The rule query and parser cannot rule out every policy interaction: the structured PowerShell query was access denied, netsh includes package-scoped entries with blank program fields, and firewall policy can change after this snapshot. No conclusion here is a live socket test.

Microsoft describes Windows Defender Firewall's default inbound behavior as blocking unsolicited incoming traffic unless a rule permits it: [Windows Firewall overview](https://learn.microsoft.com/en-us/windows/security/operating-system-security/network-security/windows-firewall/). This corroborates the conservative interpretation of default Block; it does not resolve this machine's effective loopback exception behavior for a desktop process.

## Runtime gate recommendation

Keep the existing process-owner PID equality check and staged profile/game-path log checks, and keep RSP unreachable until both pass. Add a preflight that records the active firewall profile/default-action snapshot and verifies the global non-loopback block remains enabled. For a wildcard-bound Azahar, the reviewed host-side allow must be limited to the exact staged executable and selected TCP port, with local and remote addresses restricted to `127.0.0.1`; leave other inbound traffic blocked. Have an administrator review/apply that policy before the next authorized runtime stage. If such a narrowly scoped allow cannot be confirmed, stop before launching or connecting and report the firewall policy as the blocker. This review made no policy change and did not launch Azahar, open a listener, probe a port, connect RSP, or use keyboard/mouse.
