# Revisión independiente run002: `0x002B88C4` touch-region registration

## Dictamen

La corrección resuelve las dos diferencias de estado que detecté antes: el cuerpo compilado vuelve a cargar el global `work` y el count signed antes de la segunda comprobación, y emite las cuatro stores halfword en orden ascendente, igual que el ARM original. El runner ahora compara el trace de escrituras sin ordenarlo, además del estado final. Para los fixtures síncronos fijados, la promoción semántica acotada es defendible; conservar `non_matching` porque el cuerpo C++ difiere en bytes.

La corrección no crea una transacción atómica ni un lock. La fila sigue siendo cuatro stores de 16 bits, seguidos por el store de count; otros lectores aún podrían observar una fila parcial entre stores. `volatile` preserva las cargas/escrituras observables del cuerpo generado, pero no ofrece sincronización entre threads, mutual exclusion ni garantía de atomicidad de la fila. Tampoco están cubiertas mutaciones concurrentes de node/rect ni la vida natural de esos objetos. El servicio `0x002B0188` sigue interceptado en la composición final y runtime sigue sin probarse.

## Proveniencia congelada

Los 18 inputs de `run002/task.json` existen y todos sus SHA-256 coinciden. Imagen original: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. Hash del reporte JSON actual `build/agent-work/H2-semantic/h2-helper-002b88c4-touch-region-convert/run001/report.json`: `804effc881c9666b975f25d773462ea958922e76347a7a603526100cb94c3d8d`.

El reporte fija source SHA caller `f47e857eeba6f823046feb42821b0a2d85eb7cdac4073b6e0e456fdfefc58eb0`, helper `e43d6957e60b4ebd69931663eb530013fb40b4ed8132163c9730d086f73cea37`, cuerpo caller de 156 bytes `29878499d248b75307e6e982b421195e7752b0a601486ef41b0a6587bafa3a4a` (resuelto en dirección temporal, como hace el runner al generar `caller_body_sha256`) y cuerpo resolver final de 64 bytes `bfa847afec13e6e7ead326553668fea5094994d40137a928ade2cc449422b28a`. Verifiqué hashes de source contra los archivos y reextraje los cuerpos de los objetos preexistentes para comprobar tamaño, contenido con reloc resuelta y tipo/offset de relocation. No compilé, corrí el runner, construí el proyecto ni lancé emulador.

## Comparación con ARM original

El ARM original obtiene el work pointer por `0x0043DCB4`, llama `0x002BF6D0(group_id,node_id)`, carga count con signo de `work+0x64A` y retorna `-1` si `count >= 200`. Después selecciona la forma de registro según `node+0xC`: custom usa node `+8/+0xA` y rect `+0/+2`; inline usa node `+8/+0xA` y node flags `+4/+6` sin bit 15. Vuelve a cargar el puntero global y el count, hace la segunda comprobación, escribe el record de 8 bytes en `work+count*8+0xA`, incrementa count y retorna el valor anterior.

El cuerpo actual usa `volatile u32` para las dos lecturas del global en `0x0043DCB4`, `volatile s16` para ambas lecturas del count y la store final del count. El objeto existente muestra efectivamente las dos cargas de work y las dos cargas signed del count, con la segunda capacidad check antes de stores. Los cuatro stores son:

- node X a `record+0xA`
- node Y a `record+0xC`
- tercer halfword a `record+0xE`
- cuarto halfword a `record+0x10`

Luego almacena `count+1`. Esto coincide en orden con las dos rutas ARM. En la forma custom el tercer/cuarto halfword proviene de `rect+0/+2`; en la forma inline son los flags `node+4/+6` con el bit 15 enmascarado. El layout reserva 200 records de 8 bytes desde `work+0xA` hasta `work+0x649`, con count en `+0x64A`.

El limite y los offsets dependen de punteros válidos (work, cadena del manager, node y optional rect) y de conteos no negativos en los casos probados. Counts negativos siguen pasando el branch signed del original y pueden indexar antes del array; no están cubiertos. No se valida comportamiento de punteros null/ilegibles.

## Casos, ordered trace y mutations

El reporte incluye 58 casos: cinco conteos dirigidos (`0,1,37,199,200`) en ambas formas (10) y 48 conteos pseudoaleatorios en `[0,199]`, seed `20261102`. La inicialización aleatoria varía el array completo. Se comparan retorno, bytes de todos los records, count, registros callee-saved, SP, argumentos, faults, y trace ordenado de cada escritura externa. El runner ya no ordena/sort las escrituras antes de comparación: la tupla de writes conserva la secuencia capturada por Unicorn. El reporte registra coincidencia del trace original/candidato/perfil final para los 58 casos.

Ambos negative controls siguen presentes y reportados como detectados: capacidad `200 -> 199` en count 199 y quitar el mask de bit 15 con flags altos. No ejecuté esos casos; la conclusión se basa en el reporte fijado y en inspección de que los mutation anchors y comparaciones siguen en el runner.

## Relocations y perfil final

Los cuerpos caben en sus spans originales: caller 156/220 bytes, helper `0x002BF6D0` 64/64. Caller tiene un `R_ARM_CALL` tipo 28 en offset `0xC`, resuelto a `0x002BF6D0`; helper uno en offset `0x18`, resuelto a `0x002B0188`. Recalculé ARM `BL` con `target - (place + 8)`: el branch final de caller es `0xEB001B7E`, y el de helper `0xEBFFC2A6`, ambos hacia sus destinos reportados.

El perfil original y el caller temporal interceptan el resolver de la forma descrita por el runner. El perfil final instala los cuerpos C++ en `0x002B88C4` y `0x002BF6D0`; el resolver se ejecuta y el único boundary interceptado es `0x002B0188`, que retorna un manager de fixture. El reporte afirma que los tres perfiles coinciden para 58 casos; esta es composición offline con el helper compilado en su address final, no prueba del servicio real ni de un caller externo natural.

## Recomendación y límites

- Compilado/build: el reporte registra cuerpo dentro del slot y ARMv6K build 204/204; no lo repetí.
- ARM differential: el reporte afirma 58/58 casos con trace ordenado y ambos mutation controls detectados; no lo repetí.
- Caller: parcial. El caller-helper chain llega al cuerpo C++ final del resolver, pero el servicio `0x002B0188` está mockeado y no se ejecuta un caller de juego superior.
- Runtime: `not_run`.

Recomiendo la promoción semántica acotada como actualización final de la fila/count bajo los precondiciones documentadas: direcciones válidas, contexto que serializa el registro y consumo de la fila después de completar la llamada. La corrección restaura el orden de observación visible del ARM en el cuerpo medido, pero no establece lock, barrera ni atomicidad de fila frente a concurrencia; tampoco valida el manager service, scheduler real o aceptación H2.
