# H3 — Carga de partida desde el título

Estado: cerrado para el recorrido delimitado de carga de una partida conocida; la revisión independiente de la composición final pasó. El comportamiento posterior al fallo de lectura queda registrado como evidencia parcial, no como contrato reconstruido.

## Objetivo y criterios

Desde un arranque reproducible, seleccionar una partida conocida y llegar a una escena con el estado esperado, comparando original y reemplazo integrado. Identificar una copia de prueba de la partida y los campos observables antes de ejecutar el recorrido. Cubrir cancelación, ranuras vacías y errores dentro del contrato delimitado. La lectura original puede mantenerse como dependencia explícita; H6 cubre guardar y recargar.

## Contrato y evidencia

En el título, el estado 7 prepara la transición y llama `SaveLoad_BeginFromTitle` (`0x0030A9A4`), después pasa al estado 8. El estado 8 espera `SaveLoad_IsBusy` (`0x00282DF8`); cuando deja de estar ocupado, el flag del manager determina si pasa al estado 12 o reinicia el título. Véase `src/ui/ui_runtime2.cpp` y la ficha H1.

`src/ui/save_load.cpp` conserva cuerpos originales para la interfaz y el proceso de E/S. Los nombres y comentarios de las estructuras existentes son hipótesis hasta contrastarse con los llamadores y el binario. En particular, `saveLoadUI_Init_Decompiled` no debe tratarse como equivalente: su asignación condicional y limpieza completa difieren del cuerpo ARM conservado.

La ruta runtime original/parcheada reconoció el slot 0 (`Flynn`), leyó la partida por el proceso original, mostró `Load complete` y llegó a `Map_Field3DManager` (`0x00208CE8`). Tras 250 ciclos de campo, ambas capturas muestran la entrada de Shinjuku Station — Underground y el mismo mapa inferior. Una ranura vacía no inició el proceso de lectura y la cancelación desde el slot poblado devolvió ambas interfaces al título. La evidencia reproducible y sus límites están en [`h3-runtime-comparison.md`](../agent-work/h3-runtime-comparison.md).

La copia fuente y los perfiles aislados conservaron el SHA-256 `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9` antes y después. La lectura y validación del guardado siguen siendo dependencias originales explícitas. El stub GDB no permitió leer el argumento de contexto del manager, así que no se afirman coordenadas u orientación del jugador. En la composición final, el control con guardado conocido llegó al acuse y al field manager en ambas ejecuciones y completó 250 callbacks de campo con semántica de escena concordante.

## Cierre y límites

- **Fallo al abrir (caso previo):** se retiró solo la copia de perfil antes de confirmar. En `0x002D8E60` se observó `r0=0`; una captura separada registró el marcador interno de estado 7. Esto no prueba fallo durante la lectura de bytes ni error visible. Véase [`h3-read-error-classification-review.md`](../agent-work/h3-read-error-classification-review.md).
- **Fallo después de abrir (composición final H2+H3):** tras `r0=1` en apertura, se truncó a cero bytes solo la copia perfilada. El original y el parche solicitaron `0x24E30` bytes; `AsdSave_Read` devolvió `r0=0` en `0x00210478`, mientras el control intacto devolvió `r0=1`. Después, el validador devolvió `r0=1` y el lector tenía `r0=6` en el punto de limpiar su flag. No se capturó marcador final de estado, acuse de éxito, entrada al field manager ni mensaje de error visible en esta ruta. No se atribuye aquí el estado 7 del caso distinto de fallo al abrir. La revisión independiente confirmó los hashes y la interpretación acotada; véase [`h3-final-composite-independent-review.md`](../agent-work/h3-final-composite-independent-review.md).
- La traza cruda difiere únicamente en `r2` del setter (`0x2A1` original, `0x2A0` parcheado); su significado no está establecido. Los valores de apertura, byte de resultado, progreso y resultado de escena coinciden. La igualdad byte a byte de la traza completa no se afirma.
- Recorrido integrado validado: sí para la ruta feliz en la composición final H2+H3, y en ejecuciones emparejadas anteriores para slot vacío y cancelación. La lógica C++ editable cubre el handoff/inicializador de título (`0x0030A9A4`); parser, E/S y validación permanecen originales. La respuesta al retorno fallido de lectura no se considera reconstruida. Esto no prueba equivalencia de todo el juego.
- Composición final: imagen H2+H3 SHA-256 `81c1c6ae72d88b689cde3e9982439c8f8c4a6e8773887547f4cb85b86cd34a20`, IPS SHA-256 `95846920df9ceb0e6395b6fb7e5358c99b83dd14e5861ffcfa80d8e64208eda5`. El H3 cambia solo `[0x0030A9A4,0x0030AA1C)` sobre el H2 final. La regresión H2 pasó 12/12 checkpoints y el caller composition pasó sobre la combinación. Reportes y review: `build/agent-work/H3-semantic/h3-final-composite/evidence-run-001/` y [`revisión independiente`](../agent-work/h3-final-composite-independent-review.md); los artefactos runtime fuente permanecen en el build privado de `E:\SMT4decomp`.

Fixture proporcionado por el usuario: `sdds4game1.sav` (151088 bytes, SHA-256 `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`), copiado sin cambios a `build/h3-fixture/source/`. La cabecera `DDS4GAME` declara tamaño `0x24DB0`; el juego lo reconoció como slot 0 y mostró el nombre `Flynn`.
