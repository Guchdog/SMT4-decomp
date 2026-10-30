# Revisión independiente: paquete IPS APT Utility-4

## Resultado

La imagen empaquetada y el IPS reproducen exactamente la misma salida desde el `code.bin` original fijado. Verifiqué todos los 20 hashes del packet y repetí el parseo/replay IPS en memoria con un parser independiente. Los 533 registros heredados y sus hashes coinciden con el manifiesto H2; se añaden seis registros, todos dentro del body APT de 40 bytes, con 29 bytes distintos respecto a la base H2. No encontré bytes no autorizados, cambios de tamaño ni solapamiento con los rangos heredados.

La revisión acepta la reproducibilidad binaria delimitada del paquete. No implica equivalencia semántica ni ejecución runtime. Queda una salvedad de procedencia visible en el manifiesto base: cuatro entradas `source_identity_mismatches`; el paquete fija su hash, pero no copia esas advertencias a su propio manifiesto.

No modifiqué imágenes, IPS, manifiestos de entrada, fuentes compartidas, ledger ni board. No usé emulador, saves o perfiles.

## Identidad y lineage

| Artefacto | SHA-256 |
| --- | --- |
| Original `code.bin` | `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558` |
| Base H2 compuesta | `acd8b2f35df08f225ca65b0fbf8aeef2dbbaa71171904e31c301e8bff6a51446` |
| Manifiesto base H2 | `577c89588e031dc3eb1878d474cade85d5fe62f1f41c27816c4d7e92cd304d27` |
| Imagen APT final | `788530a1b1ad7d4f361228cbd0e4b87885b37606a8f3485c52e5390ae3223179` |
| IPS original-based | `9c4f38fbdefc9c52bc745e4cbb1e6425d5822db7c2ed2267331d582c5a841c88` |
| Manifiesto del paquete | `af055478109dcb439f814dc4737a2e6306fc41286252afe41a29ab17640ceea9` |

Las tres imágenes miden `0x377000` bytes. El manifiesto base declara el hash original correcto, su `patched_sha256` coincide con la base H2 y el manifiesto del paquete fija los hashes exactos de esa imagen y ese manifiesto. El SHA actual de la fuente candidata también coincide con el registrado (`1f7228e30cfdb3c14497f96fdce3bc65845ad65bb4b3b5491c5ab2b382742e06`). No recompilé el candidato en esta revisión; la identidad del objeto compilado es la consignada por el manifiesto del paquete.

El manifiesto base informa cuatro diferencias entre identidad fuente esperada y observada: mapper en `0x0021F39C`, `0x002CAB70` y `0x002E0AF4`, y FillPair `camp_func_0027edf8`. Los detalles completos están en `checks/independent-ips-audit.json`. No invalidan el replay byte a byte porque imagen y manifiesto están fijados y todos los intervalos se verifican, pero sí impiden describir los componentes heredados como source-clean. El manifiesto del paquete enlaza el manifiesto base por hash pero no replica ese campo de advertencias.

## Replay y registros IPS

Mi parser independiente comprobó header `PATCH`, offsets de 24 bits, registros no vacíos, orden/ausencia de solapamiento, límites de imagen, `EOF` final y ausencia de datos de truncación tras `EOF`. El IPS no usa registros RLE. Aplicado en memoria al original, reconstruye byte por byte el archivo `code.h2-apt-utility4-inplace.bin`, con el mismo tamaño y SHA-256. Cada registro IPS coincide con su fila del manifiesto del paquete, payload final y SHA declarado.

| Comparación | Registros/bytes | Resultado |
| --- | ---: | --- |
| Original → base H2 | 533 registros; 4.218 bytes | Cada registro verifica su SHA en la base; cada diferencia original-relativa queda dentro de esos intervalos |
| Original → paquete | 539 registros; 4.247 bytes | Replay IPS exacto; cada diferencia está autorizada por el manifiesto base o el body APT |
| Base H2 → paquete | 29 bytes nuevos | Todos dentro del body APT; seis nuevas runs IPS |

Las seis runs nuevas son offsets de archivo `0x1C0EFD` (11 bytes), `0x1C0F0A` (4), `0x1C0F0F` (3), `0x1C0F13` (1), `0x1C0F15` (7) y `0x1C0F21` (3): total 29 bytes. La entrada VMA es `0x002C0EFC`, el body mide 40 bytes y su intervalo de archivo es `[0x1C0EFC,0x1C0F24)`. Los cuatro bytes restantes de la función original hasta `0x1C0F28` permanecen intactos. No hay intervalo base que intersecte la entrada original completa de 44 bytes. La lista `authorized_ranges` del paquete equivale exactamente a los 533 intervalos heredados más el body APT de 40 bytes.

El body del manifiesto tiene 40 bytes y su hash coincide. La llamada ARM en offset 32 se registra como `R_ARM_CALL` a `0x002B5A1C`; el word `0xEBFFD2BE` decodifica al destino declarado. Este chequeo identifica los bytes empaquetados; no ejecuta el wrapper.

## Guardas y límites

El constructor del paquete verifica hashes de original/base/manifiesto, filas heredadas, entrada intacta en la base, solapamiento, tamaño fijo, relocación, rango autorizado, round-trip y hash final esperado. Las tres pruebas focalizadas pasan: una valida que `delta_is_authorized` rechaza un byte fuera de rango, otra que los diffs se separan en runs contiguas y otra que `overlaps` detecta intersección parcial. Las pruebas ejercitan helpers, no el constructor de paquete completo ni errores IPS mutados end-to-end; mi replay independiente cubre el artefacto producido.

El paquete es un IPS **basado en el original** que incorpora primero los cambios H2 heredados y luego el body APT. No debe confundirse con un IPS destinado a parchear directamente la base H2. La salida está marcada experimental/offline. No verifica el wrapper/servicio real, callers Thumb/indirectos, permisos ejecutables ni runtime; no cierra H2 ni promueve el ledger.

## Recomendación

Aceptar la identidad, round-trip y autorización de bytes de este paquete experimental. Mantener visible junto a él la advertencia de las cuatro discrepancias fuente heredadas. Antes de cualquier uso de producción hacen falta los gates semánticos y runtime ya pendientes; esta auditoría no autoriza instalar ni promocionar la imagen.
