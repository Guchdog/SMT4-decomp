# H2 manual comparison package

The package constructs a standalone IPS from the pinned original and checks each reviewed patch-chain identity, final image bytes, and IPS roundtrip. The two staged portable users initially contain the same approved MAC and NAND config seeds and identical settings, with only the patched profile receiving `load/mods/00040000000E5C00/exefs/code.ips`. Both explicitly disable GDB and RPC. They have separate saves; the pristine seed does not include a game save. No emulator was launched or runtime behavior verified.

Create a fresh stage (never overwrite an existing one):

```powershell
python tools/h2_manual_comparison_package.py --output E:/SMT4decomp/build/h2-manual-comparison/run-001
```

Launch each separately in PowerShell, closing one before starting the other. These commands do not enable GDB or RPC:

```powershell
& 'E:\SMT4decomp\build\h2-manual-comparison\run-001\original\app\azahar.exe' 'E:\SMT4decomp\build\h2-manual-comparison\run-001\pinned-title.cci'
& 'E:\SMT4decomp\build\h2-manual-comparison\run-001\patched\app\azahar.exe' 'E:\SMT4decomp\build\h2-manual-comparison\run-001\pinned-title.cci'
```

Inspect each staged `app/user/config/qt-config.ini` for `use_gdbstub=false` and `enable_rpc_server=false` before launching. Inspect logs and UI to confirm the intended portable user directory, game, and patch application; patch presence alone does not establish loading. Start both from the same game state, perform matching title audio changes, cancel and confirm, check persistence after leaving and restart, and record differences and conditions. Profiles diverge after use; do not treat later runs as identical starting conditions. No claim of runtime equivalence follows from staging.
