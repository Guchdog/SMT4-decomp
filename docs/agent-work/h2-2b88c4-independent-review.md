# Revisión independiente: `0x002B88C4` touch-region registration

## Dictamen

Los 58 casos estáticos respaldan el resultado final del helper para el fixture documentado: grupo `0x1D`, nodo `0x572`, punteros válidos, conteos no negativos y sin interleaving durante la llamada. También se verifica el perfil final con cuerpos compilados para `0x002B88C4` y `0x002BF6D0`, y con el servicio `0x002B0188` interceptado. No encontré diferencias de bytes finales en los registros de región/count dentro de ese dominio.

La aceptación debe conservar límites explícitos. El candidato almacena los cuatro halfwords en orden temporal inverso, y el comparador ordena las escrituras antes de compararlas. El original además vuelve a leer el puntero global y el count antes de confirmar escrituras; el cuerpo C++ compilado reutiliza ambos valores capturados antes. Por tanto, no es equivalente si un observador lee el registro a mitad de llamada, o si otro contexto cambia el global/count durante el trabajo. Promovería solo el comportamiento de llamada síncrona/serial sin tales interleavings, manteniendo `non_matching`; el packet no prueba esa exclusión para el runtime real.

## Identidad y hashes

Los 17 inputs de `run001/task.json` existen y coinciden con sus SHA-256. La imagen fijada es `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. Extraje los 220 bytes originales desde `0x002B88C4`; SHA-256 `7a35859373194f6f2362c5a58158173d77885e85ae781191728604b7d72df27c`.

El reporte `build/agent-work/H2-semantic/h2-helper-002b88c4-touch-region-convert/run001/report.json` es JSON válido y su SHA-256 es `305ac8693661f0bb95d1e2d3e6e2c7342fc617e687268f5b0e4a3ef5120c8a3d`. Los hashes de source del reporte coinciden con los TUs actuales y congelados: caller `5f0327c90d92bdde3fdd7980043444a4e96b84a643906773f43221411ea34224`, resolver `e43d6957e60b4ebd69931663eb530013fb40b4ed8132163c9730d086f73cea37`. Verifiqué de los objetos preexistentes los cuerpos de 140 y 64 bytes, sus relocations únicas, y los hashes de cuerpo reubicado del reporte: caller temporal `e69edefa39aeb47f1bbb3cce0c03d94ec98df5bc42028f1239267d3143c54122`, resolver final `bfa847afec13e6e7ead326553668fea5094994d40137a928ade2cc449422b28a`. No ejecuté compilador, runner, build ni emulador.

## ARM original y contrato

La lectura del ARM fijado confirma el siguiente flujo:

1. Carga el puntero global desde el literal `0x0043DCB0`, lee `work = *(u32*)(0x0043DCB0 + 4)` —equivalente al global fijado `0x0043DCB4`— y llama al resolver `0x002BF6D0(group_id, node_id)`.
2. Lee el `s16` de count en `work+0x64A`. Si el count firmado es `>= 200`, retorna `-1` sin modificar la tabla.
3. Lee `node+0xC`. Si es distinto de cero, el registro toma `node+8/+0xA` seguido de `rect+0/+2`. Si es cero, toma `node+8/+0xA` seguido de `node+4/+6` con el bit 15 quitado.
4. Vuelve a leer el global en `0x0043DCB4`, vuelve a leer count desde `work+0x64A`, y si ahora es `>= 200` retorna `-1`. En las rutas que continúan, escribe cuatro halfwords desde `work + count*8 + 0xA`, incrementa count y retorna el count anterior.

El array de 200 registros de 8 bytes va de `work+0xA` a `work+0x649`, inmediatamente antes del count en `+0x64A`. La fuente C++ refleja ambas formas de registro, el límite, la carga del global, el retorno y el incremento. Los conteos negativos pasan la comparación signed y pueden direccionar antes del array; no aparecen en el fixture y no deben incluirse en el dominio validado. Los punteros manager/nodo/rect/work deben ser válidos y legibles/escribibles.

## Reubicación y perfil final

El cuerpo C++ de touch-region mide 140 bytes frente al span original de 220; el resolver mide 64 bytes frente al slot de 64. El caller tiene una `R_ARM_CALL` (tipo 28) en offset `0xC` hacia `0x002BF6D0`; el resolver, una en offset `0x18` hacia `0x002B0188`. Recalculé los `BL` finales usando `target - (place+8)`: en la dirección final, el caller usa `0xEB001B7E` para llegar al resolver; el resolver usa `0xEBFFC2A6` para llegar al servicio. Ambos objetivos quedan dentro del rango ARM.

El runner compara tres perfiles: ARM original; candidato de 140 bytes en dirección temporal con `0x002BF6D0` interceptado y respuesta calculada por el stub; y perfil final con caller y resolver compilados en sus direcciones finales, dejando el stub solo para `0x002B0188`. En el perfil final el hook registra la entrada al resolver, deja ejecutarse su cuerpo y captura el grupo cuando este llama al servicio. Es composición offline del helper con el resolver final, no la ejecución de un caller de juego externo ni del servicio real.

## Cobertura, stores y límites

El reporte declara 58 casos: conteos dirigidos `0, 1, 37, 199, 200` con las dos formas (10 fixtures), más 48 fixtures seeded con conteos `[0,199]`; seed `20261102`. Se inicializa la tabla completa con datos variados, por lo que cotejar el array resultante también detecta escrituras fuera del slot esperado. Se comparan retorno, conteo, bytes finales del array, registros preservados, SP, argumentos de helper, fallos y conjunto de escrituras de dirección/tamaño/valor. Los controles compilados detectan bajar capacidad de 200 a 199 en count 199 y quitar el mask de bit 15 con flags de bit alto.

El ARM escribe los cuatro halfwords en orden ascendente de dirección (`+0xA`, `+0xC`, `+0xE`, `+0x10`). El cuerpo compilado extraído los escribe al revés (`+0x10`, `+0xE`, `+0xC`, `+0xA`). El comparador ordena `external_writes`, de modo que verifica el conjunto de escrituras y el estado final, no el orden temporal. Sin otro lector entre esas stores, el resultado final coincide; con un lector concurrente o interrupt que inspeccione la tabla durante la ejecución, puede observar prefijos distintos.

También verifiqué que el cuerpo compilado usa una sola carga de count y la reutiliza para escribir/incrementar, mientras el original efectúa dos cargas con una nueva comprobación de capacidad. El original vuelve a cargar el puntero de `work` antes de leer count/almacenar; el C++ compilado mantiene el valor cargado antes del resolver. Un mutador concurrente/reentrante ofrece un contraejemplo concreto: si count pasa a 200 después de la primera lectura, el ARM retorna `-1` sin stores; el candidato puede escribir en el slot del count viejo e incrementarlo. Si el global cambia, el ARM puede escribir al work apuntado por el global actualizado mientras el candidato conserva el anterior. Estas diferencias no se ejercitan en los 58 casos y requieren serialización/estabilidad como precondición.

## Evidencia y recomendación

- Compilación y tamaños: el reporte documenta build ARMv6K de 204/204 TUs y cuerpos dentro de los slots; no lo repetí.
- Diferencial: reporte `passed` para los 58 casos, final-address profile y dos mutation controls; no ejecuté el runner.
- Caller composition externa: no ejecutada. La propia llamada interna al resolver sí se instala en el perfil final.
- Runtime: `not_run`; servicio `0x002B0188`, lifecycle touch/scheduler y ausencia de lectores concurrentes no están acreditados.

Recomiendo aceptar únicamente el estado final del helper bajo una operación serial, con count y global estables durante la llamada, punteros válidos y finalización antes de que consumidores observen el nuevo registro. Mantener `non_matching`. No elevar esta evidencia a equivalencia temporal concurrente ni a aceptación runtime/H2.
