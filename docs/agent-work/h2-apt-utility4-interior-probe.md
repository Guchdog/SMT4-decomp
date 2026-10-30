# H2: sondeo de la entrada APT command 4

El runner especializado reutiliza el aislamiento, los límites y la limpieza del sondeo revisado, pero instrumenta la entrada ARM `0x002C0EFC`. Antes de lanzar, verifica en la imagen original fijada tres llamadas ARM `BL` directas y cuatro saltos ARM `B` sin enlace. Un LR correspondiente a una llamada directa es evidencia compatible con ese callsite; un LR distinto queda sin atribuir y puede proceder de un salto de cola o una ruta indirecta. Las rutas Thumb e indirectas no están enumeradas.

El sondeo usa `Z0`: la implementación fijada de Azahar modifica temporalmente instrucciones guest y debe restaurarlas al retirar el breakpoint. No envía paquetes de escritura explícitos `M`, `P` o `X` ni inyecta entradas lógicas. Las 45 pruebas offline del runner base y el especializado pasaron. No se ha lanzado Azahar para este cambio; se requiere revisión independiente, un packet runtime propio y nuevas puertas offline.
