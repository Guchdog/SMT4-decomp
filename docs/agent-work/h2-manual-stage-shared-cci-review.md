# H2 manual stage shared-CCI review

The manual H2 stager opts into hard-link staging; the shared helper and other
callers retain copy-by-default behavior. Focused tests cover shared file
identity/content, default copy behavior, and explicit hard-link failure. The
run-012 manifest snapshot pins the reviewed image, IPS, CCI, stock executable,
and separate profile inventories. Both saved preflights are `ok: true`, and
planned capture/launch outputs remain absent.

Review report:
`build/agent-work/H2-semantic/h2-manual-stage-shared-cci-review/run-002/report.md`.

This is staging readiness only; no profile content was opened or changed, and
no emulator launch or runtime equivalence was established.
