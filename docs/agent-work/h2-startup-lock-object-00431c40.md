# H2 startup lock object `0x00431C40`

Auditoría estática de xrefs, inicialización, wait/signal y limpieza para la dirección `0x00431C40`. El único literal directo está en `0x00129A20` y lo carga `0x001299A0`; un consumidor carga el puntero publicado en `0x00471A70+0x1C` y llega a `0x0013AD64`. La ruta estática incluye un wait en base `+0x64`, señalización de la base al liberar y una ruta de cleanup. Run-028 no se vincula estáticamente con State 2; los argumentos del sitio de SVC más obvio ya están resumidos en Run-016. No recomiendo otro inicio genérico ni una sonda repetida.

El informe y hashes están en [`run-001/static-audit.md`](../../build/agent-work/H2-semantic/h2-startup-lock-object-00431c40/run-001/static-audit.md) y [`run-001/static-audit-evidence.json`](../../build/agent-work/H2-semantic/h2-startup-lock-object-00431c40/run-001/static-audit-evidence.json). No se inspeccionó la carpeta cruda de Run-028.
