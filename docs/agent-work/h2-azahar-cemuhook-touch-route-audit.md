# H2 Azahar CemuHook UDP touch-route audit

## Disposition

**A CemuHook UDP server is a plausible way to provide touchscreen coordinates to Azahar without OS keyboard/mouse input.** The pinned 2126.2 frontend has a `cemuhookudp` touch-device factory, and its UDP client converts response `touch_1` coordinates/active state into Azahar's generic `Input::TouchDevice` status. This is only an emulator-side input route. It does not prove that SMT IV's H2 title-config widget recognizes those touches, identify the game-side event representation, or provide the game's logical button queries. No runtime attempt was made.

## Configuration and packet direction

The input profile carries `touch_device`, `udp_input_address`, `udp_input_port`, and `udp_pad_index`. Select `cemuhookudp` as the touch device and set the CemuHook **server** address, port, and pad index in that profile. The pinned defaults documented in Azahar's generated configuration are address `127.0.0.1`, port `26760`, and pad index `0` (Pad 1); the actual local profile was not inspected and may differ. The `touch_device` parameter package accepts `min_x`, `min_y`, `max_x`, and `max_y`; the factory defaults these to 100, 50, 1800, and 850 respectively. The source comment says these defaults work well for DS4 but may not suit other sources.

Direction matters: Azahar constructs an IPv4 UDP socket bound to local port `0` (OS-assigned ephemeral port), then sends requests to the configured server endpoint. It sends a PortInfo request and a PadData request for the selected pad every three seconds. Its asynchronous receive handler accepts/validates responses on that socket and dispatches PadData to the client. Thus the script to investigate is the CemuHook **server** responding to Azahar's requests, not a client that blindly sends to port 26760 and not an emulator listener bound at that port. The server needs to respond to the source address/ephemeral port of Azahar's query. No socket was bound, probed, or sent during this audit.

Azahar registers the shared UDP state under the `cemuhookudp` touch and motion factories. `UDPTouchDevice::GetStatus()` returns the client-maintained `(x,y,active)` tuple. Touch-device selection and UDP endpoint/pad settings are profile configuration, not CLI switches established by this source review. The H2 CLI contract's `--windowed` and `--gdbport` only describe the Qt runtime/debug port; they do not configure CemuHook UDP.

## Fields consumed from PadData

The response struct declares many controller fields, but `Client::OnPadData` uses only a limited subset:

- It first reads `packet_counter` as a freshness gate; stale or equal counters are discarded before updating status.
- For touch, it reads `touch_1.is_active`, `touch_1.x`, and `touch_1.y`. If active and touch calibration is present, each coordinate is converted to `u16`, clamped to its configured min/max, and normalized to a float in the 0..1 range. It stores `{x,y,is_active}` under a mutex. When inactive, the local x/y values remain zero and active is false.
- It does not use `touch_1.id`, `touch_2` fields, or `touch_hard_press`. The source has a TODO that distinguishes hard-press/click touch from ordinary tap, so no click distinction is exposed here.
- It does not consume `digital_button`, `home`, stick fields, or `analog_button` for controller buttons. The protocol's digital-button bitfield description is commented out with a note that this input is unused. A PadData packet can contain button values, but this client path does not translate them into Azahar button state.
- `accel` and `gyro` are consumed for motion status; they do not affect this touch/button conclusion.

Consequently, this provider can potentially feed a touch coordinate/contact, but it is not the route to synthesize H2's `camp_func_002C1830(id,mode)` logical button results. Keep physical button labels and logical ID mappings unresolved.

## H2 applicability and remaining gap

A later pinned-game-image audit identified the `IfTouch_Init` manager
initialization and `TOUCH CALC` callback that update `IfTouchWork+0x64E` and
`+0x08`; see [the reviewed producer report](h2-input-manager-touch-state-producer-audit.md).
That closes the static game-side writer question. It still does not prove that
Azahar's `touch_1` values reach this callback's hit-test inputs or establish the
runtime relation to H2's `-1` Calc arguments and registered regions.

The current H2 contracts establish two separate candidate event paths:

1. `UiTouch_GetRegionTouchState` (`0x0029D8FC`) compares a passed signed halfword against `IfTouchWork+0x64E`, then returns the opaque byte at `IfTouchWork+0x08` only on equality. The H2 title-config initializer fills `work+0x1C..+0x23` with `0xFF`; the three observed region registration returns are stored at `work+0x14,+0x16,+0x18`, not in the four halfwords Calc reads. The manager initializes its active index to `-1`; its update callback later writes an index and changes the opaque state byte. No evidence proves how Azahar's touch coordinates reach those update paths, whether the `-1` arguments match at useful H2 callback times, or whether any resulting byte equals Calc's tested values 1, 2, or 6.
2. `camp_func_002C1830(id,mode)` performs logical-input queries (including `(9,1)`, `(4,0)`, `(3,0)`, `(0,1)`, and `(1,1)` from Calc). The pinned table rows and masks for these IDs are now documented, but their physical meaning, full state-buffer producer, scheduling, and Azahar delivery remain unresolved. The UDP client ignores PadData button fields, so CemuHook touch alone does not answer these logical queries. See [the logical table audit](h2-logical-input-table-producer-audit.md).

A touch routed through the emulator may still be useful to test whether ordinary bottom-screen coordinate input naturally reaches the title UI. That is a hypothesis requiring observation, not evidence that the H2 service contract is satisfied. It also does not observe guest state by itself. Do not write game globals/work fields or infer a safe RSP address from the presence of this frontend input route.

The CemuHook path is distinct from the GDB/RPC guest-observation channel. It sends client requests to the configured UDP input server and receives input replies; it neither exposes a guest-memory observation API nor changes the separate Azahar GDB/RPC listener bind policy. The pinned RPC/GDB locality review still describes the GDB listener as wildcard-bound and loopback-permission as unresolved. This touch route does not bypass that gate.

## Bounded source evidence

Pinned Azahar revision: official `azahar-emu/azahar` commit `219d743a1e698101fe1ab8bef43e6563126c3c27` (the 2126.2 source target supplied by the task). Relevant source links:

- [`client.cpp`, socket construction, send/receive loop, and PadData consumer](https://github.com/azahar-emu/azahar/blob/219d743a1e698101fe1ab8bef43e6563126c3c27/src/input_common/udp/client.cpp#L819-L949) and [`OnPadData`/client startup](https://github.com/azahar-emu/azahar/blob/219d743a1e698101fe1ab8bef43e6563126c3c27/src/input_common/udp/client.cpp#L1030-L1111).
- [`protocol.h`, response PadData members and packet layout](https://github.com/azahar-emu/azahar/blob/219d743a1e698101fe1ab8bef43e6563126c3c27/src/input_common/udp/protocol.h#L923-L1047).
- [`udp.cpp`, touch-device status/factory and configuration wiring](https://github.com/azahar-emu/azahar/blob/219d743a1e698101fe1ab8bef43e6563126c3c27/src/input_common/udp/udp.cpp#L413-L538).
- [Generated Azahar config comments for touch provider and UDP endpoint defaults](https://github.com/azahar-emu/azahar/blob/219d743a1e698101fe1ab8bef43e6563126c3c27/src/android/app/src/main/jni/default_ini.h#L1483-L1509).
- H2's in-repository static contracts: [input seam](h2-input-seam-contract.md), [touch handle producer audit](h2-input-handle-producer-audit.md), [logical flag refresh audit](h2-input-logical-flag-refresh.md), [firewall/locality review](h2-azahar-firewall-locality-review.md), and [runtime CLI contract](h2-runtime-cli-contract.md).

The source inspection was static. The source pages show the requested commit in their GitHub breadcrumb, and the task pins that commit; no Azahar source checkout was present in the semantic worktree. No claim is made about a currently installed Azahar binary, current profile values, active server, firewall state, or runtime delivery.

## Next CLI-only experiment, if separately authorized

Prepare an offline CemuHook UDP server that waits for Azahar's PortInfo/PadData request and returns valid PadData responses with a monotonically increasing `packet_counter`; vary only `touch_1` active/x/y in directed cases while leaving all button fields zero. Configure a **disposable staged input profile** to select `cemuhookudp`, loopback server endpoint and pad 0, with explicit calibration bounds. Start the server via a CLI process, then invoke the staged Azahar executable through the documented Qt CLI with `--windowed` and the chosen game path. Do not use OS keyboard/mouse.

Because the current client issues requests every three seconds, first capture actual packet cadence and verify the server's response handling in this isolated runtime. For H2, a later separately assigned observer must sample guest-side touch status/region fields and the title-config work/callback at bounded breakpoints, plus the logical query results, to determine whether the coordinate input reaches Calc. The existing GDB/RPC policy gate and staged-user-path checks must be satisfied independently before attaching an observer. The existing Azahar GDB listener is wildcard-bound and its loopback firewall permission is unproven. Test inactive touch and out-of-range/calibration-boundary coordinates as controls. Until then, treat this route as a plausible UI touch source only, not deterministic H2 input or semantic validation.

## Evidence limits

No Azahar process, UDP listener, network probe, request, response, emulator configuration, profile, game state, OS input, build, or test was used or changed. Static provider behavior cannot establish actual packet compatibility, server software/availability, active profile selection, in-game touch coordinate mapping, game-side handler timing, H2 logical-query values, guest-state safety, or runtime equivalence.
