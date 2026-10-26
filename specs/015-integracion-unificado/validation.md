# Validación — 015 / Integración de `vigia-unificado` e iOS

Spec: [spec.md](spec.md). Tareas: [tasks.md](tasks.md).
Rama: `feature/015-integracion-unificado`. El detalle de cada tarea está en la tabla de ejecución de las tareas.

## Pruebas automáticas, 2026-10-26

| Suite | Antes (línea base) | Después |
|---|---|---|
| Django (`UsuarioApp homeApp PlanesApp CuidadosApp PrivacidadApp`) | 227 OK | 235 OK |
| Edge | 22 OK | 22 OK |
| Flutter | 39 OK | 43 OK; `flutter analyze` sin problemas |

`git diff` contra `develop` sin archivos de la lista B (RF-015-01).

## Navegador — T-015-06, 2026-10-26

Servidor demo (`core.mobile_demo_settings`) y Chrome sin interfaz. Login, catálogo público, descarga y portal muestran `vigia.svg` y el favicon, en claro y oscuro, en escritorio y móvil. En oscuro el logo tiene poco contraste (≈2,3:1), pero se distingue.

## Android físico — T-015-07, 2026-10-26

Teléfono ELI NX9, Android 16, por USB. APK debug de `feature/015-integracion-unificado` (`flutter build apk --debug --dart-define=API_URL=http://127.0.0.1:8000`, instalado con `adb install -r`). Servidor demo en `127.0.0.1:8000`, alcanzado con `adb reverse tcp:8000 tcp:8000`. Cuentas ficticias de `seed_mobile_demo`. El recorrido se manejó con `adb` (toques y capturas); el propietario desbloqueó el teléfono cuando hizo falta.

| Comprobación | RF | Resultado |
|---|---|---|
| Login `demo_premium` e inicio rediseñado: saludo, plan, tarjeta del paciente, acciones rápidas con «Unirme con un código», seis pestañas que caben en el ancho | 02 | OK |
| HU-03: «Marcar administrado» → «Confirmar». Medicinas pasa de 4 a 3; en la base, `medication · done · demo_premium` | 01, 02 | OK |
| HU-04: Guías → «Registrar cambio realizado» → «Ya realicé el cambio». El reloj vuelve a 120 min (01:59:42); en la base, `posture · done · demo_premium` | 01 | OK |
| Avisos: «Activar avisos en este teléfono» → «1 aviso(s) programado(s)». Con el reloj adelantado a +120 s en la base demo (y `generation` +1), la alarma quedó exacta (`exactAllowReason=permission`). Con el teléfono bloqueado (`Dozing`), llegó «VIGIA · Reloj de cuidados — Es momento de revisar un cuidado. Abre VIGIA.», sin datos clínicos | 01 | OK |
| Sin conexión (el túnel `adb reverse` se cortó al bloquear y desbloquear): la app informa «No se pudo actualizar los avisos. Revisa la conexión…» y no falla; al reconectar, se sincroniza | 01 | OK |
| Panel de plan (Premium): catálogo del servidor (Gratis, $4.990, Premium «PLAN ACTUAL»), vigencia; «Ver VIGIA Plus en la web» abre `/planes/` en Chrome | 04 | OK |
| Cerrar sesión con un aviso pendiente: vuelve al login y `dumpsys alarm` queda sin alarmas de la app | 01 | OK |
| Rol cuidador (`demo_free`): tarjeta «Paciente activo · Cuidador»; Rosa no cuenta en su cupo («1 activos · VIGIA Free»); la ficha dice «Accedes como cuidador», sin Historial, Monitoreo, edición ni gestión de accesos, y ofrece «Dejar de acompañar» | 02 | OK |
| Privacidad: cuenta ficticia temporal sin la política aceptada. Solo se ve el aviso «Acepta la política de privacidad», con «Cerrar sesión» debajo, que funciona. La cuenta se eliminó al terminar | 02 | OK |

Hallazgos de interfaz (no corregidos; para decidir):

- En el inicio, la acción rápida «Registrar medicamento» corta la palabra en dos líneas («medicament / o») con la letra al 100 %.
- Al cambiar de pestaña se conserva la posición de desplazamiento de la anterior: Posturas se abrió más abajo, con el título cortado.

No comprobado en el teléfono: consentimiento por paciente (D-066), rol familiar, plan Free/Plus en el panel, servidor por la red local y reinicio del teléfono.

Limpieza: se devolvió el ajuste «pantalla encendida con USB» a su valor (0), se quitó el `adb reverse` y se detuvo el servidor.

## Pendiente

- iOS (T-015-08..11): Sandra, en macOS, con autorización aparte.
- T-015-12..13: documentación de alcance e instalación, y cierre.

## Aceptación funcional

Pendiente del propietario.
