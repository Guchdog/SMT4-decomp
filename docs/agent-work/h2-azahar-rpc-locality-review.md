# H2 Azahar RPC locality review

## Result

Azahar's bundled RPC client is a possible CLI automation interface for guest
memory reads/writes and screenshots, but it is not a loopback-only workaround
for the GDB listener gate. At the pinned Azahar 2126.2 commit
`219d743a1e698101fe1ab8bef43e6563126c3c27`, the UDP server constructs its
socket with an IPv4 endpoint on port `45987` without a specific address. This
binds the wildcard address. The Python client defaults to sending packets to
`127.0.0.1:45987`; that client destination does not constrain the server's
bind address.

The RPC server is disabled by default in the inspected settings. When enabled,
its protocol supports process listing/selection, guest-memory reads/writes,
screenshots, and performance statistics. It does not expose breakpoints,
register access, execution control, or controller input. Thus, it cannot by
itself run the H2 original-versus-patched scenarios or replace the unresolved
logical input seam.

The default 2126.2 build uses asynchronous memory reads/writes unless built with
`ENABLE_SCRIPTING_SYNC`. The pinned source explicitly warns that reads can be
unsafe for some regions when asynchronous, and writes can likewise race with
emulation. No RPC packet was sent and no emulator was launched in this review.

**Disposition:** do not use RPC as a substitute for the reviewed GDB route. If
RPC is later used for bounded snapshots, retain the executable, port, process,
and loopback firewall gates; verify the exact build's scripting-sync setting
and avoid framebuffer/VRAM reads. RPC writes should remain out of the H2 input
path until an event-state producer and safe synchronization point are
established. No keyboard or mouse control is part of this route.

## Pinned source evidence

- [`udp_server.cpp` at the pinned commit](https://github.com/azahar-emu/azahar/blob/219d743a1e698101fe1ab8bef43e6563126c3c27/src/core/rpc/udp_server.cpp#L439-L446) constructs `boost::asio::ip::udp::endpoint(boost::asio::ip::udp::v4(), 45987)`.
- [`AzaharRPC.py` at the pinned commit](https://github.com/azahar-emu/azahar/blob/219d743a1e698101fe1ab8bef43e6563126c3c27/dist/scripting/AzaharRPC.py#L14-L44) declares memory read/write packet types and defaults its client to `127.0.0.1:45987`.
- [`configure_debug.ui` at the pinned commit](https://github.com/azahar-emu/azahar/blob/219d743a1e698101fe1ab8bef43e6563126c3c27/src/citra_qt/configuration/configure_debug.ui#L44-L56) describes the opt-in RPC server and remote guest-memory access.
- [`rpc_server.cpp` at the pinned commit](https://github.com/azahar-emu/azahar/blob/219d743a1e698101fe1ab8bef43e6563126c3c27/src/core/rpc/rpc_server.cpp#L1092-L1109) selects asynchronous handling unless compiled with `ENABLE_SCRIPTING_SYNC`.
- [`rpc_server.cpp` read/write handlers](https://github.com/azahar-emu/azahar/blob/219d743a1e698101fe1ab8bef43e6563126c3c27/src/core/rpc/rpc_server.cpp#L1138-L1216) document asynchronous access risks and write cache invalidation behavior.
- [`rpc_server.cpp` request dispatch](https://github.com/azahar-emu/azahar/blob/219d743a1e698101fe1ab8bef43e6563126c3c27/src/core/rpc/rpc_server.cpp#L1556-L1609) lists the supported request types; the client protocol has no breakpoint or controller-input request.

These are source facts for the pinned revision. Runtime support, active setting,
effective listener address, and firewall behavior remain untested.
