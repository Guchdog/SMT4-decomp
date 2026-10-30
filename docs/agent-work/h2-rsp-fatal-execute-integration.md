# H2: integración de limpieza ante respuesta RSP perdida

Una prueba offline usa `execute` y `capture_session` reales con un proceso, socket, entradas, perfil y save sintéticos. Al simular una respuesta perdida de `Z0`, comprueba que el callback conectado por `execute` termina el hijo antes de cerrar el socket, que no se envía `D`, que se elimina el staging propio y que el fixture y el archivo de juego sintéticos no cambian. La prueba pasó.

La prueba no inicia Azahar ni usa el perfil o el save reales. Es una comprobación de la ruta de error simulada; no demuestra que Windows pueda terminar un proceso en todos los fallos posibles ni sustituye la revisión independiente antes de promoción.
