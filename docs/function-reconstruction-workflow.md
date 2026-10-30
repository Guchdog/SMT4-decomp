# Procedimiento de reconstrucción y validación por función

Este es el procedimiento para continuar después del experimento ARM. Su objetivo
es conservar C++ útil con evidencia reproducible, aunque el compilador elija
instrucciones distintas. Las comprobaciones por función son rápidas; la regresión
general se ejecuta al cerrar un lote. El [informe del piloto](../experiments/semantic_equivalence/README.md)
describe lo ya comprobado y sus límites.

El [plan de hitos funcionales](reconstruction-milestones.md) define cómo elegir
los lotes por área y comportamiento, sus criterios de cierre y la coordinación
entre subagentes. Este procedimiento define cómo validar cada función del lote.

**Estado de partida (2026-10-24):** el experimento contiene catorce helpers con
pruebas ARM y once ventanas de caller. Batch 4 se cargó en Azahar, llegó al
título, abrió Audio Settings y volvió al título; se observaron entradas de dos
reemplazos. No se comparó el mismo escenario entre juego original y parche, así
que esto es una comprobación de carga/recorrido corto, no de equivalencia del
menú. No presentar pruebas ARM aisladas ni esos dos hits como una comprobación
de todo SMT IV. Ver el [registro H0](milestones/H0-reproducible-test-base.md)
y el [plan por hitos](reconstruction-milestones.md).

## 1. Preparar el trabajo y consultar los intentos anteriores

Trabajar en una rama/worktree experimental desde un commit conocido. Anotar
`git status --short --branch` y conservar cualquier cambio previo del usuario.
Mantener intactos el dump original, las claves y los archivos extraídos. Objetos,
informes completos, imágenes y parches generados se guardan en `build/`, ignorado
por Git. Nunca introducir el contenido del juego en un commit.

Antes de elegir una dirección, buscarla en las fichas y en los planes históricos:

```powershell
rg -n -i '00128f34' docs/function-records docs/superpowers/plans MODLOG.md
python tools/find_candidates.py --limit 30
python tools/find_candidates.py --include-existing-candidates --limit 30
```

El buscador ordena candidatos, pero **no excluye automáticamente los intentos
fallidos anteriores**. Revisar especialmente los lotes históricos 6 y 7. Una
función ya diferida solo se reabre con evidencia nueva: tipos corregidos, ABI
confirmada, una estrategia de validación distinta o un cambio de compilador
registrado. Reordenar otra vez la misma expresión no es evidencia nueva.

Crear `docs/function-records/0xDIRECCION.md` a partir de la
[plantilla](templates/function-reconstruction.md). Usar una ficha por dirección,
actualizada en cada intento. La [ficha de ejemplo](function-records/0x00394614.md)
corresponde a una función del piloto.

## 2. Confirmar qué bytes y qué función se están estudiando

Localizar la fila de `config/functions.csv`, su marcador `DECOMP_FUNC`, fuente,
tamaño y modo ARM/Thumb. Inspeccionar el desensamblado, literales, ramas y límites:

```powershell
python tools/split_asm.py --addr 0x00128f34
rg -n -i '00128f34' src include config/functions.csv
```

No asumir que una fila es una función independiente si contiene relleno,
literales, caída a otro bloque o saltos a etiquetas interiores compartidas.
Comprobar llamadores y referencias; las declaraciones existentes son evidencia
que debe contrastarse, no una garantía de firma correcta.

Para ARM, un barrido de instrucciones `BL` alineadas puede encontrar referencias
que el desensamblado lineal pierde al atravesar datos. Confirmar cada resultado
en un bloque de código y su contexto; una palabra de datos puede parecer un BL.
Ese método no encuentra por sí solo llamadas indirectas, punteros en tablas,
Thumb/BLX ni entradas a mitad de función. Anotar esas limitaciones.

Priorizar familias con operaciones conocidas y tipos respaldados por llamadores.
Estudiar juntos los hermanos de una familia, pero conservar resultados por
dirección. Una función más corta no es necesariamente más fácil de compilar.

## 3. Escribir el contrato antes del C++

Registrar en la ficha:

- Argumentos y retorno: registros enteros, registros VFP, argumentos en stack,
  signo, anchura, paso de structs y retorno oculto cuando corresponda.
- Memoria: campos/offsets, tamaños, alineación, almacenamiento accesible, estado
  global, aliasing permitido y efectos laterales.
- Dominio válido: nulos permitidos, rangos, objetos inicializados, capacidad,
  longitudes y condiciones previas.
- Comportamiento observable: retorno, memoria, llamadas, errores y registros
  que la ABI exige conservar; indicar si algún caller consume flags o registros
  adicionales del original.
- Evidencia y dudas: direcciones de llamadores, layouts existentes y decisiones
  inferidas. Si el retorno es incierto, conservar provisionalmente el `r0`
  original; no ignorarlo solo porque la declaración diga `void`.

Separar las reglas de memoria RAM ordinaria de MMIO, hilos y observadores
concurrentes. Reordenar escrituras a campos independientes puede ser válido en
RAM y cambiar el comportamiento de un dispositivo. El piloto no verifica esto
último. No inventar una precondición para excluir un contraejemplo válido.

## 4. Reconstruir con tipos y operaciones definidos

Guardar primero la propuesta fuera de los wrappers de `src/`, en el área
experimental. En el piloto, los símbolos son `candidate_DIRECCION` en
`experiments/semantic_equivalence/candidates.cpp`.

Describir la operación con C++ claro. Revisar desbordamiento de enteros con signo,
desplazamientos, límites de punteros/arrays, representación de objetos, aliasing,
alineación y vida útil. En particular, no usar una escritura `u64*` a una
dirección alineada solo a cuatro bytes para conseguir un opcode deseado.
No añadir `volatile` únicamente para forzar registros u orden del compilador:
su uso debe estar justificado por el contrato.

No contar como reconstrucción semántica un cuerpo nuevo de ensamblador,
`.incbin` o bytes crudos. Los controles negativos pueden contener ensamblador
deliberadamente incorrecto si está identificado como fixture de prueba.

Compilar con el toolchain ARMv6K canónico. Registrar versión, flags y hashes.
No cambiar opciones globales para facilitar un candidato sin tratarlo como un
cambio separado que necesita su propia regresión.

## 5. Priorizar equivalencia semántica

La aceptación principal es C++ legible cuyo comportamiento esté respaldado por
contratos, pruebas diferenciales y callers. No se exige que tamaño, registros
temporales u opcodes coincidan. No buscar variantes de código sólo para mejorar
el byte matching ni diferir una propuesta correcta por esa diferencia.

Compilar y ejecutar la propuesta con su runner específico. El comando
`asm_diff.py` compara la definición registrada en el ledger, no una propuesta
situada sólo en `experiments/`; es un diagnóstico opcional o una comprobación
necesaria cuando se quiere conservar explícitamente la etiqueta `matching`.
Su salida no es el criterio de aceptación de una propuesta semántica.

Conservar el original como referencia reproducible. No llamar `matching` al C++
que produce bytes diferentes. En experimentos, registrar el avance semántico por
separado. Al promover una reconstrucción no idéntica a `src/`, usar una
clasificación soportada como `non_matching` y su ficha de evidencia; esa etiqueta
sólo clasifica cobertura compilada y no sustituye las pruebas de comportamiento.
No inventar un estado CSV que el tooling no admita. La referencia histórica
exacta sigue recuperable en Git; mantener 100% matching no es una obligación de
las implementaciones semánticas futuras.

## 6. Preparar las pruebas específicas de esa función

Ejecutar el ARM original y el ARM recompilado desde el mismo estado, en instancias
independientes. El original es la referencia; una reescritura Python de la misma
hipótesis no lo sustituye.

Para cada función incluir:

- Casos límite derivados de sus comparaciones, signo, anchura y capacidad.
- Entradas aleatorias válidas con al menos dos semillas registradas.
- Memoria y registros iniciales variados para evitar depender de ceros casuales.
- Aliasing y alineación válidos cuando el contrato los permita.
- Cobertura de las ramas y efectos observables que motivan la reconstrucción.
- Al menos un control negativo dirigido: cambiar un límite, offset, stride,
  orden sensible a aliasing, bit o condición. Debe fallar por el motivo esperado.

Para un dominio pequeño, preferir enumerarlo: por ejemplo, los 256 valores de
un byte. No hay un número de casos aleatorios que demuestre equivalencia general.
La amplitud se justifica por el contrato; alcanzar una cifra grande no sustituye
cubrir ramas y límites. Un millón de entradas que no cruza el umbral sigue siendo
una prueba incompleta.

Comparar retorno y efectos de memoria; verificar la ABI contra el estado inicial,
no solo entre ambas ejecuciones. El piloto comprueba `r4-r11`, `SP` y `d8-d15`,
memoria de prueba, stack vivo y conjuntos de bytes leídos/escritos. En una ventana
de caller que incluye instrucciones propias de una función mayor, `r4-r11`, `SP`
y `d8-d15` pueden cambiar legítimamente dentro de la ventana: comparar esos
estados entre original y parche al mismo punto de parada. En una invocación
aislada, seguir comparándolos contra el estado inicial para validar el ABI.

La ventana debe declarar observables según el contrato comprobado, no comparar
por defecto todos los registros caller-saved o NZCV. Comparar `r0` solo cuando el
calle devuelve un valor consumido por el caller (o al probarlo aislado); en un
setter `void` no rechazar cambios de `r0` no consumido. Comparar NZCV solo cuando
el caller realmente consume esos flags tras la llamada. Continuación, estado
callee-saved/SP entre ambas ejecuciones, memoria y huella de accesos siguen
siendo observables de la ventana. Añadir un test del runner con implementaciones
que difieran solo en `r0`/NZCV no consumidos y verificar que no genera falso
rechazo, además de comprobar que sí detecta un valor/flag cuando es consumido.

Los temporales caller-saved, flags de una hoja y scratch de stack pueden diferir
si el contrato permite esas diferencias.

Fallos de memoria, instrucciones no soportadas, ausencia de retorno o agotamiento
del presupuesto invalidan la ejecución. Dos ejecuciones que fallan igual no
constituyen una aprobación. Guardar el primer contraejemplo reproducible y
revisar si falla la propuesta, el contrato, la preparación de memoria o el runner.

## 7. Adaptar el piloto actual sin atribuirle funciones que no tiene

`tools/semantic_experiment.py` está especializado para sus ejemplos registrados.
**No existe una opción `--addr`, un filtro de fallos históricos ni un registro
genérico que construya escenarios por sí solo.** Para una función adicional:

1. Añadir su C++ y su `Candidate` en `CANDIDATES`.
2. Extender `cases()` con memoria, entradas y precondiciones específicas.
3. Añadir su control negativo a `experiment()`, con el error esperado.
4. Si se añade una ventana de caller, adaptar tanto su referencia BL y puntos
   de parada como la preparación de registros/stack de `caller_windows()`.
   Agregar únicamente una tupla no generaliza la lógica actual de los dos callers.
5. Ajustar el texto/alcance del informe y añadir pruebas del runner cuando la
   nueva función necesite capacidades distintas.

El piloto solo acepta hojas ARM enteras que terminan en `bx lr`, sin llamadas,
relocaciones, operandos relativos a PC, VFP ni servicios del sistema. Su RAM
de prueba es limitada y el resto de la imagen se mapea como código de solo
lectura/ejecución; no es un entorno completo de globales, heap o hardware 3DS.
Una función fuera de ese alcance queda diferida hasta implementar y probar el
soporte adecuado. No quitar los rechazos para conseguir un resultado verde.

Usar directorios nuevos por lote/corrida para distinguir resultados y evitar
confundir un artefacto anterior con la salida de una ejecución fallida:

```powershell
python -m unittest tests.test_semantic_experiment -v
if ($LASTEXITCODE -ne 0) { throw 'Fallo del verificador diferencial' }
python tools/semantic_experiment.py --code E:/SMT4decomp/extracted/exefs/code.bin --samples 16384 --seed 20261024 --output build/semantic-equivalence/batch-001/seed-20261024
if ($LASTEXITCODE -ne 0) { throw 'Fallo en la primera corrida' }
python tools/semantic_experiment.py --code E:/SMT4decomp/extracted/exefs/code.bin --samples 4096 --seed 7 --output build/semantic-equivalence/batch-001/seed-7
if ($LASTEXITCODE -ne 0) { throw 'Fallo en la segunda corrida' }
```

Usar la ruta real del dump privado y un identificador nuevo al repetir el lote.
La CLI ejecuta el conjunto configurado completo, incluidos los controles y los
callers registrados. Comprobar `passed`, los resultados de la función y controles,
hashes, semillas, casos y límites en `report.json`; la existencia de un IPS no
basta. Si cambia fuente, contrato, compilador o flags, invalidar la evidencia
afectada y repetirla.

## 8. Probar la integración en niveles separados

Primero ejecutar fragmentos reales de callers con la misma imagen parcheada que
se va a evaluar. Cubrir ambas continuaciones de las condiciones relevantes y
comparar flags cuando las consuma el caller. No sustituir este paso por invocar
solo la función desde un wrapper sintético.

El patcher actual coloca C++ sin relocaciones en relleno cero de páginas de
`.text` y genera saltos de entrada e IPS. La capacidad observada es 2.524 bytes
para esta revisión; no es espacio ilimitado ni una estrategia para todo el juego.
Debe rechazar capacidad insuficiente, límites inválidos y relleno ocupado.
Mantener tamaño/offsets y comprobar que aplicar el IPS reproduce exactamente la
imagen que se ejecutó. Revisar referencias que entren a mitad de las funciones,
pues cambiar solo la entrada no las intercepta.

Después, para aprobar integración real:

- Probar original y parche en entornos separados con copias del mismo save y
  estado inicial. Registrar revisión del juego, versión/configuración del
  emulador o consola, parche y semillas/entradas cuando corresponda.
- Confirmar que el loader conserva y ejecuta la zona de código añadida.
- Demostrar que la función se ejecutó mediante breakpoint, traza o contador;
  llegar al menú inicial no prueba una función de batalla o guardado.
- Repetir escenarios que cubran sus efectos y límites y contrastar estados,
  resultados, trazas y errores. Comparar únicamente capturas no valida la lógica.
- Guardar evidencia local y anotar lo no ejercitado. Arranque correcto no implica
  equivalencia de todo el programa, estabilidad general o un port terminado.

Este nivel tiene evidencia de ejecución de entrada para dos de los diez
reemplazos del piloto, pero no comparación original/parche de escenarios ni
validación conductual de juego. No instalar ni publicar el parche como
equivalente basándose solo en el runner ARM o en los hits de entrada.

## 9. Registrar el estado y cerrar lotes

Usar las siguientes etiquetas en la ficha, separadas del CSV existente:

| Etiqueta documental | Evidencia mínima |
|---|---|
| `investigada` | Límites, contrato, evidencia y dudas registrados |
| `reconstruida` | C++ compila; todavía sin aprobación de comportamiento |
| `probada_arm` | Casos diferenciales válidos y controles negativos pasan |
| `probada_llamador` | Además pasan ventanas reales de callers identificadas |
| `probada_juego` | Además se ejecutó la función en escenarios reales documentados |
| `diferida` | Bloqueo o soporte faltante explícitos; evitar repetir sin evidencia nueva |
| `fallida` | Contraejemplo válido reproducible; propuesta no aceptada |

Estas etiquetas no son una prueba formal. Registrar `matching` por separado y
solo con comparación exacta real. Contar direcciones únicas y bytes originales
por nivel, evitando sumar etapas superpuestas o contar wrappers como C++ recuperado.

Por función: compilar, comparar y actualizar su ficha. Al cerrar un lote coherente
(orientativamente 10–30 funciones, o un hito útil menor), ejecutar la regresión
general una vez desde fuentes estables:

```powershell
python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Fallo de regresion' }
git diff --check
```

Ejecutar `verify_decomp.py` al cambiar claims exactos, el ledger de referencia
o su verificador. Esa auditoría comprueba la veracidad de las etiquetas exactas;
no decide la aprobación semántica de propuestas con instrucciones distintas.

Para cambios de tooling/flags/build, completar también las comprobaciones de
[desarrollo](development.md), incluida compilación ARM forzada y CMake. Repetir
pruebas cuando haya cambios o fallos nuevos que lo justifiquen, no una suite
global de seis minutos por cada getter aceptado. Los cambios de headers/ABI
requieren comprobar todos los consumidores afectados.

Antes del commit revisar el diff y el staging; restaurar completamente los
intentos rechazados, incluidas firmas, atributos `naked`, headers y marcadores.
En staging incluir solo código/documentación del lote, nunca cambios previos del
usuario ni archivos privados. Mantener los commits experimentales separados de
los cambios que siguen siendo exactos. Push/publicación solo cuando se solicite.

La ficha final debe permitir que otra persona reproduzca el resultado sin esta
conversación: estado, evidencia, dominio, comandos, hashes, conteos, semillas,
controles, contraejemplos, límites y siguiente paso. Al pausar, anotar el commit,
los cambios pendientes y el siguiente bloqueo; detener las pruebas y agentes.
