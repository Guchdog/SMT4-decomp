# H2: entradas distintas en `0x002C0EFC`

En una ejecución original aislada, con las puertas offline y el preflight aprobados (cuatro avisos de identidad de fuentes), el sondeo registró dos entradas antes del timeout de ocho segundos. En ambas retiró `Z0`, avanzó la instrucción de `0x002C0EFC` a `0x002C0F00` en el mismo hilo conservando LR y SP, y reinstaló el breakpoint antes de continuar. Esas operaciones evitan contar repetidamente el mismo stop sin avance.

La primera entrada tenía LR `0x00103E84`, compatible con la ruta de cola `0x002C5638` observada en una corrida separada. La segunda tenía LR `0x002C1264`, compatible con el `BL` directo en `0x002C1260`. El LR no prueba por sí solo todo el historial de llamadas ni atribuye la ráfaga de Run-028. La captura terminó como `captured_partial` por timeout, con dos entradas; no cierra H2.

El listener de loopback pertenecía al hijo; el reporte registra breakpoint retirado, detach, proceso terminado y confirmado, puerto liberado y staging eliminado. `Z0/z0` modificaron temporalmente instrucciones guest; no se enviaron paquetes explícitos `M/P/X` ni entradas lógicas. El CCI, ejecutable, semillas, dependencias y fixture no cambiaron; tampoco cambió el save preparado. El save fuente no se accedió.

Reporte `build/agent-work/H2-semantic/h2-apt-utility4-distinct-entry-probe-runtime/run-001/capture-4245ef9a67e34d8c9865136971a28dfb.json`, SHA-256 `f197da2ccdc662db7307986aac304f16891583946b0cf2cde7e1daf42e01d517`. Log preservado SHA-256 `942ef72e159c157c917a571e689c6364d5ff103969dea2667bff234c9f7d4beb`. Falta la auditoría independiente de esta captura; el caso de fallo de reinserción aún no tiene prueba integrada específica hasta `execute`.
