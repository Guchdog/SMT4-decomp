# Ficha de Hito H20: Capa de Abstracción de Plataforma (HAL) y Portabilidad Nativa

- **Fecha de Evaluación:** 2026-10-31
- **Estado:** ABIERTO / EN PROGRESO (Definición preliminar de interfaces C++ y stubs en compilación cruzada; portabilidad y ejecución nativa pendientes)
- **Objetivo Documentado:** Desacoplar servicios propietarios del kernel/SDK de 3DS (`nn::`, `fs`, `gsp`/`gx`, `dsp`, `hid`, `os`) detrás de una HAL multiplataforma (`include/hal/` y `src/hal/`) para permitir compilación y ejecución nativa fuera de 3DS (PC/Linux/macOS).
- **Avance Real e Interfaces Definidas:**
  1. `include/hal/hal_system.h`: Definición de ciclo de vida de la plataforma, consulta de memoria y reloj monotónico.
  2. `include/hal/hal_filesystem.h`: Interfaz abstracta `IFile` (Read, Write, Seek, Tell, Close) y montaje de archivos.
  3. `include/hal/hal_graphics.h`: Abstracción de destinos de framebuffer (Top Left/Right, Bottom Screen), modo estereoscópico y presentación VSync.
  4. `include/hal/hal_audio.h`: Interfaz de configuración de stream PCM, encolado de buffers y ganancia de volumen maestro.
  5. `include/hal/hal_input.h`: Estructuras de coordenadas táctiles, desviación analógica del Circle Pad y máscara de botones digitales.
- **Límites Técnicos y Discrepancias Identificadas:**
  - **Prueba de Conformidad Insuficiente:** `tools/verify_h20_hal.py` únicamente realiza compilación cruzada con Clang ARMv6K y comprueba la presencia de símbolos en los objetos ELF. No prueba comportamiento funcional ni ejecuta binarios nativos del sistema anfitrión (x86_64).
  - **Implementación de Entrada Incompleta:** `src/hal/hal_input.cpp` tiene `Input_Poll()` vacío y no consulta dispositivos físicos, controladores ni ventanas del sistema anfitrión.
  - **Implementación de Audio Stub:** `src/hal/hal_audio.cpp` acepta buffers en `Audio_QueueBuffer()` sin decodificarlos ni emitir audio hacia ningún backend de sonido nativo (SDL2, Cubeb, WASAPI o ALSA).
  - **Sistema de Archivos en Memoria:** `src/hal/hal_filesystem.cpp` devuelve objetos `MemoryFile` en memoria fija en lugar de montar directorios reales del anfitrión o procesar archivos de juego reales (RomFS/SaveData).
- **Criterio para Cierre Futuro:**
  - Implementar backends de host reales (e.g. SDL2/OpenGL/Vulkan/WASAPI/Cubeb), montar el sistema de archivos del juego en rutas reales del anfitrión, procesar eventos reales de entrada y compilar/ejecutar el juego de manera autónoma en una plataforma nativa (Windows, Linux o macOS).
