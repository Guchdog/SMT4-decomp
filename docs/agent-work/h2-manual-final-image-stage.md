# H2 final-image manual runtime package

`tools/h2_manual_final_image_stage.py` stages the independently reviewed run-004
final `code.bin` into a fresh, task-specific directory under
`E:\SMT4decomp\build\h2-manual-comparison`. It verifies the supplied image
against the caller-provided SHA-256, the pinned original and
`config/game_info.json`, and the exact reviewed integration-manifest identity.
Manifest-declared patch spans must match the final image and all changed bytes
must fall inside those spans. A standalone IPS is generated from the pinned
original and replayed before and after staging.

The package contains separate `original/app` and `patched/app` portable runtime
trees with matching fresh user profiles made from the approved pristine seed.
The single root-level `pinned-title.cci` is a same-volume hard link to the
approved pinned CCI source, so fresh stages do not allocate another 1.75 GiB
copy. Both the link target and staged path are hash-checked. The only
user-profile difference is
`load/mods/00040000000E5C00/exefs/code.ips` in the patched profile. Both have
GDB and RPC disabled. `pinned-title.cci` is a single shared image in the package.
The staged Azahar executable is the pinned binary. The tool never starts it and
does not use host input.

Example command from the semantic checkout:

```powershell
python tools/h2_manual_final_image_stage.py `
  --image build/agent-work/H2-semantic/h2-thumb-reintegrate-final-image/run-004/combined-build-final/code.combined.bin `
  --expected-image-sha256 cd095feb4c8034874a2ef4661356cb131e0e240cfc907f454f12b83d05c13bf4 `
  --manifest build/agent-work/H2-semantic/h2-thumb-reintegrate-final-image/run-004/combined-build-final/manifest.json `
  --output E:\SMT4decomp\build\h2-manual-comparison\run-002
```

The staging report records input, output, seed, profile, executable, CCI, and
IPS hashes plus launch argument arrays and working directories. Run either
profile by using its listed executable and the shared `pinned-title.cci` path;
set that profile's `app` directory as the process working directory. Runtime
behavior, Audio Settings rendering/navigation, and save persistence remain
unverified until the user performs the manual scenario.
