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

## Pendiente

T-011-09/11: instalar el APK en un Android real con un servidor alcanzable (LAN `http://<IP>:8000` desde el login en modo debug), recibir un aviso con pantalla bloqueada y repetir pausar/postura/archivar/cerrar sesión en el teléfono. T-011-06 (estilo web) y T-011-10 (iOS) quedan fuera de esta entrega por indicación del propietario.
