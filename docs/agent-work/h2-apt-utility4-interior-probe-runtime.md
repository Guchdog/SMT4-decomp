# H2: captura en la entrada APT `0x002C0EFC`

La ejecución original aislada alcanzó `0x002C0EFC` después de pasar las puertas offline y el preflight. El listener GDB estaba en loopback y pertenecía al proceso hijo. El runner registró cuatro stops con PC `0x002C0EFC`, LR `0x00103E84` y registros idénticos. Entre stops envió `continue` sin un paso explícito sobre el breakpoint, por lo que estos registros pueden corresponder a una misma entrada; **no acreditan cuatro llamadas distintas**. El LR se clasificó como no resuelto por el runner.

Como pista estática, `0x00103E80` hace `BL 0x002C5624`; esa rutina contiene un salto condicional de cola en `0x002C5638` a `0x002C0EFC`. El LR observado coincide con la instrucción posterior al `BL`, pero el registro de LR por sí solo no demuestra que ese salto de cola haya sido la ruta ejecutada. Requiere revisión independiente y, si se necesita atribución inequívoca, observación adicional.

El breakpoint `Z0` modificó temporalmente instrucciones guest y se retiró; el debugger se separó, el hijo terminó, el listener se liberó y el staging se eliminó. No hubo paquetes explícitos `M/P/X` ni entradas lógicas. Los hashes del CCI, ejecutable, semillas, dependencias y fixture permanecieron estables; la copia de save preparada no cambió. El save fuente no se accedió. El nombre del CCI no se comprobó en el log: se verificaron el archivo preparado, su alias y el argv; el log registró el ID del título.

Reporte `build/agent-work/H2-semantic/h2-apt-utility4-interior-probe-runtime/run-001/capture-8be131c932384ae7b108ddca451be235.json`, SHA-256 `712e97a9c0108d395402dda2e6c865c7c3f120bfea17d3520b115ba79bd749f2`. Log preservado SHA-256 `fad6f05ac207c2f136b1b49322da0884d8a5f098d0ab097afe6852f5f9acb309`. La evidencia es parcial y no completa H2.
