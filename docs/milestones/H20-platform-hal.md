# Ficha de Hito H20: Capa de Abstracción de Plataforma (HAL) y Portabilidad Nativa

- **Fecha de Cierre:** 2026-10-31
- **Estado:** CERRADO (100% implementado, compilado y verificado)
- **Objetivo:** Desacoplar servicios propietarios del kernel/SDK de 3DS (`nn::`, `fs`, `gsp`/`gx`, `dsp`, `hid`, `os`) detrás de una HAL multiplataforma (`include/hal/` y `src/hal/`) para permitir compilación y ejecución nativa fuera de 3DS (PC/Linux/macOS).
- **Módulos HAL Implementados:**
  1. `hal_system`: Ciclo de vida de la plataforma, consulta de memoria del sistema y reloj monotónico de alta resolución.
  2. `hal_filesystem`: Montaje de archivos virtuales (`RomFS`, `SaveFS`, `SDMC`) y abstracción de flujo de archivos unificado (`IFile`: Read, Write, Seek, Tell, Close).
  3. `hal_graphics`: Destinos de visualización (Top Left/Right, Bottom Screen), conmutación de modo estereoscópico 3D y sincronización vertical (VSync).
  4. `hal_audio`: Inicialización de flujo de audio PCM multicanal, encolado de muestras de sonido y control de ganancia de volumen maestro.
  5. `hal_input`: Estado táctil analógico de pantalla inferior, desviación de ejes del Circle Pad y máscara de botones digitales.
- **Verificación:**
  - Compilación limpia con Clang ARMv6K para todos los módulos HAL (`tools/build_h20_all.py`).
  - Suite de pruebas de conformidad HAL ejecutada con 100% de éxito (`tools/verify_h20_hal.py`).
