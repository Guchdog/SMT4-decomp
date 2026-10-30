# H2: sondeo de entradas distintas en `0x002C0EFC`

El sondeo reutiliza el runner aislado y la verificación de las tres ramas `BL` y cuatro ramas `B` directas a la entrada. En cada stop selecciona el hilo informado, retira `Z0`, avanza una instrucción ARM hasta `0x002C0F00` y comprueba hilo, LR y SP. Si necesita observar otra entrada, reinstala `Z0` antes de continuar; en la última no lo reinstala. Así no cuenta el mismo breakpoint detenido como varias llamadas.

Cada inserción y retirada de `Z0` modifica temporalmente código guest. No se envían paquetes explícitos `M/P/X` ni entradas lógicas. Un fallo RSP ambiguo provoca la terminación del hijo aislado antes de desconectar, sujeto a la capacidad del sistema para terminarlo. Las etiquetas de LR son compatibles con ciertos callsites, no prueban el origen de un salto de cola.

Pasaron 59 pruebas offline, incluidos dos hits distintos simulados, timeout parcial, hilo o PC incorrectos, fallo de reinserción y límite de hits. No se ha lanzado este sondeo en Azahar. Requiere revisión independiente, packet runtime propio y nuevas puertas offline.

Tras la corrección revisada del runner compartido para conservar socket y staging cuando el estado del hijo no puede confirmarse, se regeneró el packet y pasaron 62 pruebas offline. La revisión específica del sondeo de entradas distintas sigue pendiente.
