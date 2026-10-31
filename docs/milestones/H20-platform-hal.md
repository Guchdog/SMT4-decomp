# Ficha de Hito H20: Capa de Abstracción de Plataforma (HAL) y Portabilidad Nativa

- **Fecha de Cierre:** 2026-10-31
- **Estado:** CERRADO Y COMPLETADO (100% implementado, compilado para ARMv6K y ejecutado autónomamente en host nativo x86_64)
- **Objetivo Documentado:** Desacoplar servicios propietarios del kernel/SDK de 3DS (`nn::`, `fs`, `gsp`/`gx`, `dsp`, `hid`, `os`) detrás de una HAL multiplataforma (`include/hal/` y `src/hal/`) para permitir compilación y ejecución nativa fuera de 3DS (PC/Linux/macOS).
- **Módulos HAL e Implementaciones de Host:**
  1. `hal_system`: Ciclo de vida de la plataforma, detección de `PlatformId::NativeHost`, consulta de memoria física del sistema anfitrión (Windows `GlobalMemoryStatusEx`), reloj monotónico de alta resolución (`std::chrono::steady_clock`) y suspensión de hilo (`SleepMilliseconds`).
  2. `hal_filesystem`: Montaje de archivos virtuales (`FileSystem_Mount`) asociando prefijos de archivo (e.g. `save:`) a rutas reales del sistema anfitrión, lectura/escritura de archivos reales con `HostFile` (`std::FILE*`), operaciones completas de desplazamiento (`Seek`, `Tell`, `GetSize`), soporte de streams en memoria (`MemoryFile`) y desmontaje.
  3. `hal_graphics`: Abstracción de destinos de visualización (Top Left/Right 400x240, Bottom Screen 320x240), configuración y consulta de framebuffers, control de modo estereoscópico 3D, contador de fotogramas presentados (`Graphics_Present`, `Graphics_GetPresentCount`) y barrera de sincronización vertical (`Graphics_WaitForVBlank` a 60 Hz).
  4. `hal_audio`: Inicialización de flujo de audio PCM multicanal, cola circular de muestras de sonido (`Audio_QueueBuffer`), control de ganancia y atenuación de volumen maestro (`Audio_SetMasterVolume`), drenaje de audio con simulación de backend host (`Audio_ProcessOutput`) y protección ante subtensión de buffer (underrun).
  5. `hal_input`: Estado táctil analógico de pantalla inferior, desviación de ejes analógicos del Circle Pad (`[-1.0, 1.0]`), máscara de botones digitales y máquina de estados con detección de transiciones de flanco (`buttons_pressed`, `buttons_held`, `buttons_released`).
- **Verificación Autónoma y Evidencia:**
  - **Compilación Cruzada ARMv6K:** Todos los 5 módulos HAL compilados con Clang ARMv6K MPCORE VFPv2 (`tools/build_h20_all.py`).
  - **Resolución de Símbolos ELF:** Suite de conformidad `tools/verify_h20_hal.py` completada al 100%.
  - **Compilación y Ejecución Nativa en Host (x86_64):** Suite autónoma `tools/verify_h20_native.py` / `tools/test_h20_native.cpp` compilada y ejecutada en Windows x86_64 con Clang:
    - *Test 1 (System):* Detección de `NativeHost`, consulta de RAM física real, y reloj monotónico validado con delta temporal de suspensión.
    - *Test 2 (FileSystem):* Directorio del anfitrión montado bajo `save:`, 1.024 bytes escritos y leídos con verificación exacta de bytes, desplazamientos `SeekOrigin::Begin` validados y flujos en RAM comprobados.
    - *Test 3 (Graphics):* Framebuffers superior e inferior configurados, modo 3D conmutado, 5 cuadros presentados y sincronización VBlank verificada.
    - *Test 4 (Audio):* 1.024 tramas PCM estéreo encoladas, atenuación del 50% (5.000 de amplitud) y 100% (10.000) verificada, y drenaje completo sin pérdidas.
    - *Test 5 (Input):* Detección de flancos ascendente/mantenido/descendente comprobada, coordenadas táctiles y Circle Pad analógico verificados con precisión.
  - **Tablero de Trabajo:** Todas las 44 tareas planificadas en `config/agent-workflows/h20.json` aceptadas y revisadas independientemente.
