# Validación 011 — estado al 2026-10-22

Evidencia técnica en Windows 10 (Flutter 3.47.7 / Dart 3.13.5, `.venv` raíz con `core.test_settings`). No hay aceptación funcional del propietario ni pruebas en un Android físico. Las cifras del informe (≤ 10 s, < 100 ms, etc.) no se miden aquí.

## T-011-01/02 — reloj de un paciente sin eventos

**Reproducción.** El código anterior a la corrección nunca se versionó en git (entró ya modificado en `cb064b6`), así que el fallo original del panel móvil sin acción no se pudo reproducir con un checkout. Se reprodujo de dos formas:

1. Fallos reales que seguían presentes, detectados por los nuevos tests antes de corregirlos:
   - Web: el formulario «Configurar recordatorios» ofrecía pausar, reanudar y cambiar intervalo a un paciente **sin reloj**. Enviar esas acciones lanzaba `Http404` desde `configure_timer`, y la vista web no lo capturaba.
   - API: `POST /api/v1/patients/<id>/timer` con `pause`/`resume`/`interval` sin reloj respondía **404** («No se encontró este recurso») en vez de un rechazo explícito.
   - El panel «Mis cuidados» no tenía ningún enlace para crear el recordatorio de un paciente sin reloj.
   - Resultado antes de corregir: `test_empty_clock_only_offers_creation_and_never_404s` y `test_clock_actions_without_clock_are_rejected_not_missing` → **FAILED (failures=2)**.
2. Mutación del panel Flutter: al quitar temporalmente el botón «Crear recordatorio» del estado vacío de `ClockPanel`, `test/clock_panel_test.dart` falla (**+0 −2**). Restaurado, pasa.

**Corrección (commit `08e33f4`).**

- `configure_timer`: sin reloj, solo `start` es válido; el resto produce `ValidationError` («Aún no hay recordatorio. Crea uno primero.»). La API responde 400 y la web muestra el error en el formulario.
- `TimerForm(timer=…)` ofrece solo las acciones válidas: sin reloj, `start`; activo, `interval`/`pause`; pausado, `interval`/`resume`. El servidor vuelve a validar.
- El panel web enlaza «Crear recordatorio» para pacientes sin reloj (solo lista pacientes elegibles).
- `ClockPanel` recibe `enabled`: si el paciente está archivado, muestra el motivo y deshabilita las acciones.
- Crear el reloj no genera ningún `CareEvent` (verificado en Django y en Flutter: solo hay un POST a `/timer` y ninguno a `/posture`).

## T-011-03/04 — avisos locales Android

La implementación ya existía: `flutter_local_notifications` 22.3.2, `mobile/lib/notifications/local_reminders.dart`, un aviso por paciente (ID = paciente, payload con generación) y sincronización tras cada mutación, al volver a primer plano y al iniciar. No hizo falta cambiar código de producción. Se añadieron regresiones (commit `51d9728`):

| Disparador | Prueba | Resultado |
|---|---|---|
| Pausar desde el reloj → cancela; reanudar → reprograma | `reminder_lifecycle_test.dart` (UI real de `PatientScreen`) | OK |
| Archivar paciente desde la ficha → cancela | ídem | OK |
| Registrar postura → reemplaza el aviso del paciente, sin sumar otro | ídem (nivel `VigiaApi`) | OK |
| Cerrar sesión → borra todos; una sincronización tardía no los restaura | ídem | OK |
| `timer-schedule` cambia de generación y vencimiento tras una postura y queda vacío al archivar | `test_mobile.py::test_schedule_follows_posture_and_archive` | OK |

Mutación: al quitar `syncReminders()` de la recarga de la ficha y `reminders.clear()` de `forget()`, fallan las pruebas de pausar, archivar y cerrar sesión (**+1 −3**). La de postura sigue pasando porque llama a la sincronización directamente: valida el reemplazo, no el disparo.

**No verificado:** notificación real recibida en un Android físico con pantalla bloqueada, permiso permitido/denegado, alarmas exactas (Android 12+), reinicio del teléfono y ahorro de batería. Las pruebas usan un canal de plataforma simulado.

## Comandos ejecutados el 2026-10-22

- `manage.py check` y `makemigrations --check --dry-run` (`core.test_settings`): sin problemas, sin cambios.
- `manage.py test UsuarioApp homeApp PlanesApp CuidadosApp --settings=core.test_settings`: **176 OK** (antes 173; +3 regresiones).
- `flutter analyze`: sin problemas. `flutter test`: **19 OK** (antes 13; +6).
- APK debug arm64: compilado OK (sección siguiente).

## APK debug

Compilado en Windows sobre el commit `51d9728`, con el código de T-011-01..04:

```bash
cd mobile
flutter build apk --debug --target-platform android-arm64 --dart-define=API_URL=http://10.0.2.2:8000
```

- Resultado: `√ Built build/app/outputs/flutter-apk/app-debug.apk` (Gradle `assembleDebug` 200,2 s, exit 0). La primera compilación en esta máquina instaló CMake 3.22.1 en el Android SDK local.
- Artefacto: `mobile/build/app/outputs/flutter-apk/app-debug.apk`, 142 975 637 bytes, SHA-256 `d73424acb427f5479fffa6cef11fe506520f0f08ec69827ab66a2ce50b11d61e`. `mobile/build/` está ignorado por git: el APK no se versiona.
- Avisos no bloqueantes: `firebase_core` usa Kotlin Gradle Plugin (futuras versiones de Flutter lo rechazarán) y el SDK tiene una carpeta duplicada `platform-tools.backup`.
- `API_URL=10.0.2.2` solo sirve para el emulador. En un teléfono real, en modo debug, la dirección del servidor se cambia desde el login (`http://<IP-LAN>:8000`).
- No se instaló ni se ejecutó en ningún dispositivo.

## Android físico — 2026-10-25

Teléfono ELI NX9, Android 16 (API 36), conectado por USB. App en modo debug instalada con `flutter run --dart-define=API_URL=http://127.0.0.1:8000` sobre `feature/014-privacidad` (`0c0aa74`). Servidor demo (`core.mobile_demo_settings`, cuentas ficticias) escuchando solo en `127.0.0.1:8000`, alcanzado desde el teléfono con `adb reverse tcp:8000 tcp:8000`, no por la red local.

- **Instalación.** La app anterior en el teléfono estaba firmada con otra clave (`INSTALL_FAILED_UPDATE_INCOMPATIBLE`). Flutter la desinstaló y reinstaló; se perdieron sus datos locales.
- **T-011-09 — login.** `demo_premium` entra, ve su paciente ficticio y la agenda de Medicinas con datos del servidor. OK.
- **HU-03.** «Marcar realizado» → confirmar: pendientes 4 → 3. El historial de la ficha muestra «25/10 19:20 · demo_premium · Realizado». OK.
- **HU-04.** Guías → «Registrar cambio realizado» → «Ya realicé el cambio»: el reloj pasó de 00:20:04 a 01:59:46 (intervalo 120 min). OK.
- **T-011-03 — permisos.** Denegar → «Permiso denegado. Puedes habilitar notificaciones en los ajustes del teléfono.» Reintentar y permitir → la app abre «Alarmas y recordatorios». Sin alarmas exactas el estado dice «Horario aproximado: falta permiso de alarmas exactas»; al activarlas y volver a la app, se reprograma solo y el aviso queda exacto (`dumpsys alarm`: `RTC_WAKEUP … exactAllowReason=permission`). OK.
- **T-011-03 — pantalla bloqueada.** Para no esperar 120 min se adelantó `next_due_at` del reloj en la base demo a +150 s (y `generation` +1, como un cambio desde la web). Tras «Actualizar ficha» y bloquear el teléfono (estado `Dozing`), la notificación «VIGIA · Reloj de cuidados — Es momento de revisar un cuidado. Abre VIGIA.» llegó a la hora y se vio en la pantalla de bloqueo, sin datos clínicos (canal de importancia alta, visibilidad privada). OK.

- **T-011-04 — cerrar sesión.** Con un aviso ya disparado y el reloj vencido, cerrar sesión deja `dumpsys alarm` sin alarmas pendientes de la app (solo historial). OK.
- **T-011-05 — plan Plus (parcial).** `demo_plus` (Plus, 3 pacientes): con 1 activo crea 2 más desde la app («3 activos · VIGIA Plus»); el cuarto lo rechaza el servidor con «Alcanzaste el límite de pacientes activos. Archiva uno o cambia de plan.». Una ficha donde es cuidador no cuenta en su cupo. «Analizar postura» en Plus muestra «La detección de posición está incluida en Premium». OK. No probado: Free, Premium, reducción de cupo ni cambio de plan en la web reflejado en la app.

Hallazgos de interfaz (no corregidos):

- La barra inferior tiene 6 pestañas y «Perfil» queda casi fuera de pantalla (62 px visibles en un ancho de 1200 px).
- En la ficha, el selector «Cuidados / Guías / Reloj / Historial» se corta en «Histo».
- Con los avisos desactivados se muestran a la vez «Activar avisos en este teléfono» y «Desactivar avisos locales».
- En Plus, la pestaña Plan dice «Puedes analizar con la cámara de este teléfono o consultar un nodo fijo vinculado» y la ficha «Analiza y guarda una postura con el teléfono…», aunque la cámara es solo Premium. El bloqueo funciona; el texto lo contradice.
- Al llegar al límite de pacientes, la app deja llenar el formulario y dar el consentimiento antes de que el servidor rechace por cupo.

No verificado aquí: servidor por la red local (LAN), reinicio del teléfono y ahorro de batería con avisos pendientes.

## Pendiente

T-011-09/11: instalar el APK en un Android real con un servidor alcanzable (LAN `http://<IP>:8000` desde el login en modo debug), recibir un aviso con pantalla bloqueada y repetir pausar/postura/archivar/cerrar sesión en el teléfono. T-011-06 (estilo web) y T-011-10 (iOS) quedan fuera de esta entrega por indicación del propietario.
