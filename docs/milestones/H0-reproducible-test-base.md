# H0 — Base de prueba reproducible

Estado: cerrado (2026-10-24)
Responsable de integración: Codex
Revisión base: codex/semantic-equivalence-experiment, basada en 31b76e1

## Resultado esperado

Identificar el patch experimental, comprobar que Azahar lo aplica al juego
correcto y registrar un recorrido reproducible con hits y límites explícitos.

## Alcance y exclusiones

Se comprobó el arranque del CCI US de Shin Megami Tensei IV hasta el título,
la entrada y salida de Audio Settings, la aplicación del IPS batch 4 y la
observación de entradas reemplazadas. No se validó toda la lógica del menú,
una partida, ni equivalencia completa del juego.

## Dependencias

- Título: 00040000000E5C00, US v0.1.0.
- Referencia code.bin del experimento: SHA-256
  1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558.
- IPS batch 4: SHA-256
  9b5f7c8f261743a2805d356153232f445c02f00c2f7938e7550505bc4b6317f9.
- Build de Azahar: 2126.2; GDB stub en 127.0.0.1:24689.
- Monitor: experiments/semantic_equivalence/azahar_hit_flag.py --batch 4.

## Prueba de aceptación ejecutada

1. Se comprobó el SHA-256 del IPS nuevo y del instalado antes del reemplazo.
   El patch anterior se conservó en
   build/azahar-mod-batch2-backup/00040000000E5C00/exefs/code.ips.
2. Se instaló el IPS batch 4 en el perfil de Azahar y se abrió el CCI US
   desencriptado. El registro de Azahar confirmó que code.ips parchó code.bin
   y la inicialización del stub GDB en el puerto configurado.
3. La captura build/azahar-batch4-boot.png muestra el título principal.
4. Con el monitor conectado al proceso emulado 11, se seleccionó Audio Settings,
   se entró usando la tecla A configurada y se volvió al título con B. La captura
   build/azahar-batch4-audio-settings.png registra la pantalla;
   build/azahar-batch4-after-cancel.png registra el retorno al título.
5. El monitor observó estas entradas del parche:
   - state_flags: original 0x0037C46C, cave 0x003FE694.
   - two_word_copy: original 0x002ADB40, cave 0x003FE70C.
6. El depurador se desconectó normalmente, Azahar siguió abierto y el juego volvió
   al título. La carpeta de datos de guardado del título no contenía archivos al
   terminar. No se cambiaron valores de Audio Settings.

## Evidencia y límites

El log de Azahar en %APPDATA%/Azahar/log/azahar_log.txt confirma la aplicación
del patch y el inicio del stub. La pantalla confirma que el juego llegó al título
y regresó de Audio Settings. Cada FLAG confirma únicamente que se alcanzó esa
entrada; no demuestra que la función sea correcta en todos los estados.

Se observaron dos de las catorce entradas armadas durante esta sesión. Las doce
restantes no dieron hit en este recorrido; esto no prueba que no se ejecuten en
otras rutas. No se detectaron cambios en los archivos de guardado enumerados.
El CCI no se modificó. Los reportes ARM diferenciales siguen siendo evidencia
separada de la observación en Azahar.

## Cierre

- Patch identificado y aplicado: sí.
- Recorrido título → Audio Settings → título: sí.
- Entradas de reemplazo observadas: dos, enumeradas arriba.
- Equivalencia funcional del menú completo: no establecida.
- Recorrido integrado validado: sí, para el alcance corto descrito.
- Lógica de un hito de área reconstruida: no; esto sólo cierra infraestructura.

## Próxima acción

Continuar H1 desde el [mapa ya documentado](H1-main-menu-flow.md): resolver el
origen del estado inicial y los IDs físicos, comparar payload/subtabla TBB en
los assets extraídos y preparar una ventana segura de caller. Los dos getters
tienen propuestas semánticas comparadas contra ARM en fixtures sintéticos; aún
no integrarlas ni presentar el menú como reconstruido.
