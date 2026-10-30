# Independent review: H2 manual final-image package

## Result

**Ready for user-controlled manual runtime comparison, with runtime evidence still not run.** The staged package is internally consistent with the reviewed final image and the pinned original, and its two user trees differ only by the intended IPS. It is appropriate for the user to launch the patched CLI profile for the Audio Settings scenario after reviewing the commands below. This review did not launch Azahar or provide host input.

## Package verification

I read the stage task packet and source/report artifacts, then independently hashed and inspected the external package at `E:\SMT4decomp\build\h2-manual-comparison\run-002`.

- Pinned original `code.bin`: SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558` (3,633,152 bytes).
- Reviewed final image: SHA-256 `cd095feb4c8034874a2ef4661356cb131e0e240cfc907f454f12b83d05c13bf4` (3,633,152 bytes).
- Staged standalone IPS: SHA-256 `bb9fc65956b2261468825a3732a2019cdd69226a6402309716bbeadfb26ac808` (6,439 bytes, 485 records per stage report). Applying the staged IPS to the pinned original reproduced the final image byte-for-byte and yielded the final image SHA-256 above.
- The actual staged CCI hash is `9cc760c2f37da9a4a3657e918e0eaebb3e8e80a91047e5c18f95aedf0242b4c2`. Both staged executables hash to the pinned Azahar SHA-256 `c248414eb5328cb8bb720775ace6959898e2f50a0a10221c3a1e7a14190183eb`.
- The original user tree contains exactly the shared `config/qt-config.ini` and the two approved seed files. The patched tree contains those same three files with identical hashes plus only `load/mods/00040000000E5C00/exefs/code.ips` with the staged IPS hash. The common config hash is `5272739c578aff2c815a2b42dc6c35fafe76d6148934cad5fd4355964fa28a8e`; it contains `use_gdbstub=false` and `enable_rpc_server=false` in both profiles.
- The seed files in both trees match the recorded allow-list: NAND config SHA-256 `03f9bb1edcc9f742774f1b66b66e6b10cc270eb8e7ae6881008ff9f876928f36` (32,768 bytes), and `sysdata/mac.txt` SHA-256 `5b265f2cee070908edef5a0a9561bfedf95dd9b88610cec5ae69c0f1d7287b1b` (17 bytes).
- The commands use each staged `original/app` or `patched/app` executable and set that profile's `app` directory as working directory; both use the one shared package-root `pinned-title.cci`. These roots are inside the portable staged trees, not the installed Azahar/user profile.

The recorded launch commands are:

```powershell
# Patched profile, from E:\SMT4decomp\build\h2-manual-comparison\run-002\patched\app
.\azahar.exe E:\SMT4decomp\build\h2-manual-comparison\run-002\pinned-title.cci
```

For the original control, use the same command with working directory `...\original\app` and executable `...\original\app\azahar.exe`. Keep the same CCI path.

## Source and evidence review

The staging tool resolves and constrains output to a new child of `E:\SMT4decomp\build\h2-manual-comparison`, validates the exact expected final-image hash, pins the integration-manifest identity and checks its declared changed spans against the final image, validates original image identity against the manifest and `config/game_info.json`, pins CCI and executable hashes, and performs the IPS round trip before and after staging. It snapshots the seed before staging and confirms it remains unchanged. It writes a new output directory only after input validation, creates fresh profile trees, compares profile manifests before patching, then requires the patched tree to equal the original manifest plus exactly the IPS. These guards support the claimed package identity.

The focused offline test source covers IPS round-trip splitting and the reserved EOF offset, image-size rejection, output-root rejection, and early rejection of wrong final-image and manifest hashes. The stage report records five focused tests passed; I inspected the test source but did not run it, per this review task's no-tests instruction.

The stage report also records an initial failed staging attempt because the seed source had extra files, followed by the allow-list implementation and successful staging. The saved report gives that first attempt exit code 1, but does not retain its stderr or the exact pre-fix source hash; the current CLI error handler exits 2 for caught staging errors. Treat the failure's stated cause as report evidence rather than independently reproduced evidence. The final package itself was independently verified here.

## Limits and next action

This establishes package construction and IPS identity only. It does not establish that Azahar recognizes the mod path, that the title boots, or that Audio Settings rendering, focus/navigation, audio behavior, or save persistence works. The integration report likewise marks runtime as `not_run` and includes modeled/HLE boundaries in some offline differential evidence.

The user may now launch the patched profile for a manual Audio Settings comparison, with the original profile as control. Record observations separately; do not treat a successful launch alone as whole-game equivalence.
