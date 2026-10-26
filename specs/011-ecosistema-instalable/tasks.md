# Tareas — 011

Creadas pendientes en fase documental22/10/2026; implementación autorizada después (ver final). Estados reconciliados con el código real el 2026-10-22 (sección «Reconciliación»). La aceptación visual de010 no autoriza por sí sola el código nuevo de011.

Leyenda: [x] hecho con evidencia técnica · [~] parcial (código presente, falta prueba real o parte del alcance) · [ ] pendiente · [—] fuera de alcance.

| Estado | ID / RF | Trabajo | Dependencia / terminado |
|---|---|---|---|
| [x] | T-011-01 /02 | Regresión del reloj vacío y contrato de inicio sin evento | Autorización; reproducir con paciente nuevo y documentar conducta |
| [x] | T-011-02 /02,04 | Inicio, intervalo, pausa/reanudación y conflictos en servicio/API/UI |01; pruebas propiedad, tokens, generación y reintentos |
| [x] | T-011-03 /03 | Seleccionar dependencia y programar avisos locales en ambos SO |02; permisos, estados y prueba real de notificación |
| [~] | T-011-04 /03,04 | Cancelación/reconciliación y coordinación con push |03; logout/archivo/otra cuenta/cambio web sin duplicados; migración si procede |
| [ ] | T-011-05 /04 | Ensayo cuenta y plan web/app con backend único |02; Free/Plus/Premium y reducción de cupo verificadas |
| [~] | T-011-06 /05 | Tokens y componentes web con estilo aprobado |Autorización; claro/oscuro/contraste/teclado/móvil y Tailwind |
| [x] | T-011-07 /06 | Inventario de rutas y manifiesto de traslado |Autorización; DB/secretos/entornos fuera del traslado automático |
| [x] | T-011-08 /06 | Separar web/ y modularizar Flutter por función |07; imports, comandos, assets, enlaces y pruebas sin regresión |
| [~] | T-011-09 /01 | Preparar APK y conexión desde Android real |02–08; instalación y login con servidor accesible |
| [—] | T-011-10 /01 | Build iOS y prueba en iPhone firmado |Fuera de alcance desde 2026-10-22: iOS excluido por el propietario (ver Reconciliación). **2026-10-26: vuelve al alcance por D-068; el trabajo sigue en T-015-08..11** |
| [ ] | T-011-11 /01–06 | Validación integrada y guía de entrega |09; alarmas con pantalla bloqueada, cámara dual sin regresión y límites honestos |

Bloqueos externos: destino remoto no definido; dispositivo Android real no verificado. Documentar evidencia por plataforma, no marcar tareas terminadas con pruebas sintéticas solamente.


## Autorización22/10/2026
El usuario indica «perfecto ahora modificalo»: implementación completa011 autorizada. Los estados documentales anteriores son antecedentes; no autorización de producción/tiendas ni migración real.


## Reconciliación con el código — 2026-10-22

Revisión estática del código y ejecución en Windows; sin cambios de código. Evidencia previa en `.work-011/` (macOS, misma fecha) citada como antecedente, no repetida salvo donde se indica.

| Tarea | Evidencia en el código | Falta |
|---|---|---|
| T-011-01/02 | `web/CuidadosApp/services.py` `configure_timer` acción `start` sin CareEvent; `web/CuidadosApp/api/views.py` TimerView/TimerScheduleView; `mobile/lib/features/posture/clock_panel.dart` («Crear recordatorio», pausar/reanudar). Pruebas `CuidadosApp/test_mobile.py` (`test_start_clock_without_fabricating_care_and_reject_replay`, `test_clock_invalid_interval_rolls_back…`) y `tests.py` (pausa/reanudación/generación); `mobile/test/reminders_test.dart` (reloj vacío) | — |
| T-011-03 | `mobile/lib/notifications/local_reminders.dart`; `flutter_local_notifications` 22.3.2 y `timezone` en `pubspec.yaml`; receptores y permisos en `android/app/src/main/AndroidManifest.xml`; `reminders_test.dart` | Notificación real recibida en Android con pantalla bloqueada y permiso permitido/denegado |
| T-011-04 | Migración `CuidadosApp/migrations/0006_mobiledevice_local_posture_reminders.py`; `send_mobile_reminders` omite `posture:` si el dispositivo usa avisos locales; prueba de logout en `reminders_test.dart` | Push Firebase real sin configurar; reconciliación tras cambio web no probada en dispositivo. 0006 aplicada solo a `.mobile-demo` |
| T-011-05 | `PlanesApp/entitlements.py`, `CuidadosApp/capacity.py` heredados de 010 | Ensayo registrado web↔app con Free/Plus/Premium y reducción de cupo |
| T-011-06 | `web/static/css/tokens.css` con `#5057a0`/`#f6f7fc`, caché `?v=011` | Comparación visual claro/oscuro, teclado y móvil; build Tailwind en Windows |
| T-011-07 | `specs/011-ecosistema-instalable/traslado.json` (manifiesto origen→destino) | — |
| T-011-08 | `web/` con todas las apps Django; `manage.py` raíz delega en `web/manage.py`; `@source` actualizado en `web/theme/static_src/src/styles.css`; `mobile/lib/{app,core,features/{auth,detection,home,medications,patients,posture,profile,subscription},notifications,shared}`. Quedan reexportaciones de compatibilidad de una línea en `mobile/lib/` (`api.dart`, `care.dart`, `phone_pose*.dart`, `pose_classifier.dart`) | Retirar reexportaciones cuando no haya consumidores (opcional) |
| T-011-09 | APK debug compilado en macOS (`.work-011/apk.txt`) | Instalación en Android real y login contra servidor alcanzable |
| T-011-10 | Build iOS iniciado en macOS sin terminar (`.work-011/ios-build.txt`) | Fuera de alcance |

Ejecutado en Windows el 2026-10-22:

- `manage.py check` y `makemigrations --check --dry-run` con `core.test_settings`: sin problemas ni cambios. También `check` desde el `manage.py` de la raíz.
- `manage.py test UsuarioApp homeApp PlanesApp CuidadosApp --settings=core.test_settings`: **173 OK** (28,3 s), en `.venv` nuevo con lock `--require-hashes`.
- `python -m unittest edge.test_posture`: **5 OK** (sintéticas). `edge.smoke` no ejecutado: falta el modelo `.task` en esta máquina.
- Flutter, primer intento: no ejecutó porque el SDK local era 3.47.1 (Dart 3.13.1) y `pubspec.yaml` exige `sdk: ^3.13.5`. Con autorización del propietario se fijó el SDK en la etiqueta **3.47.7** (Dart 3.13.5), sin tocar `pubspec.yaml`. Resultados: `flutter pub get` OK (lock sin cambios), `flutter analyze` sin problemas y `flutter test` **13 OK**. No hizo falta corregir código.

Cambio de alcance indicado por el propietario el 2026-10-22: entorno Windows, Android primero e iOS fuera de alcance. Registrado en [D-011-02](../../docs/DECISIONES.md) y en la [spec](spec.md#decisión-de-alcance--2026-10-22).

Siguiente paso: T-011-09, instalar el APK en un Android real con un servidor alcanzable.


## Implementación en Windows — 2026-10-22 (segunda pasada)

Pedido del propietario: priorizar T-011-01/02 y T-011-03/04 con regresiones, APK debug nuevo y commits por tarea; T-011-06 y T-011-10 quedan para después. Evidencia en [validation.md](validation.md).

| Tarea | Estado | Cambio |
|---|---|---|
| T-011-01/02 | [x] | Fallo del estado vacío todavía presente en web/API, reproducido con tests antes de corregir: la web ofrecía pausar/reanudar/cambiar intervalo sin reloj y respondía 404; la API también daba 404. Corregido en `configure_timer`, `TimerForm(timer=…)`, panel web («Crear recordatorio») y `ClockPanel` (deshabilitado si el paciente está archivado). Commit `08e33f4` |
| T-011-03 | [x] | Sin cambios de código: implementación existente verificada con pruebas. Notificación real con pantalla bloqueada y permiso denegado/permitido comprobados en Android físico el 2026-10-25 ([validación](validation.md#android-físico--2026-10-25)) |
| T-011-04 | [~] | Regresiones de cancelación/reemplazo al pausar, registrar postura, archivar y cerrar sesión (Flutter y Django). Commit `51d9728`. Falta verificación en dispositivo y reconciliación tras cambio web con la app cerrada |
| T-011-09 | [~] | APK debug regenerado en Windows (ver validación). Falta instalación y login en un Android real |

Siguiente paso: T-011-09/11 en un teléfono Android con servidor LAN.

## Tareas fechadas 2026-10-25 — detalles de interfaz hallados en Android

Autorización: «acepta el merge y arregla los detalles de interfaz» (propietario, 2026-10-25). Rama `feature/011-detalles-interfaz` desde `develop`. Origen: [validación en Android físico](validation.md#android-físico--2026-10-25).

- [x] T-011-12 — Navegación que cabe en pantallas angostas (sin RF propio: usabilidad de la app de la 010). Componente: mobile.
  - Fallo: la barra inferior se fuerza a 420 dp y en un teléfono de ~369 dp «Perfil» queda fuera; el selector de la ficha se desplaza y corta «Historial».
  - Archivos: `features/home/care_home.dart`, `features/patients/patient_screen.dart`.
  - Hecho cuando: a 360 dp las seis pestañas y todas las secciones de la ficha se ven y se pulsan sin desplazamiento horizontal ni desbordes; prueba de widget.
  - Hecho: la barra ocupa el ancho real (etiquetas de 11 sp bajo 420 dp) y el selector de la ficha usa chips que pasan a una segunda fila. `test/interface_details_test.dart`: antes «Perfil» llegaba a x=420 y las secciones a x=472 sobre 360; después todo dentro. En el teléfono (~369 dp): seis pestañas de 200 px y secciones en dos filas.
- [x] T-011-13 — Botones de avisos y textos según el plan (RF-011-03, RF-011-04). Componente: mobile.
  - Fallo: con avisos desactivados se ven «Activar» y «Desactivar» a la vez; en Plus, la pestaña Plan y la ficha invitan a usar la cámara, que es Premium, y la ficha muestra el título «Cámara fija» sin contenido.
  - Archivos: `features/posture/clock_panel.dart`, `features/subscription/subscription_panel.dart`, `features/patients/patient_screen.dart`.
  - Hecho cuando: el reloj muestra solo la acción que corresponde al estado de los avisos; sin detección por plan, ningún texto ofrece la cámara; pruebas de widget.
  - Hecho: un solo botón según `remindersEnabled`; textos de Plan y Monitoreo según `posture_detection`; «Cámara fija» solo con nodos o con opción de vincular. Pruebas antes −2, después +2. En el teléfono (Free): «Activar» ↔ «Desactivar» alternan; Plan y Monitoreo sin mención de la cámara.
- [x] T-011-14 — Alta de paciente sin perder lo escrito (RF-011-04). Componente: mobile.
  - Fallo: si el servidor rechaza el alta (fecha inválida, cupo lleno), el formulario ya se cerró y hay que reescribirlo y repetir el consentimiento; con el cupo lleno, el aviso llega recién al final.
  - Archivos: `features/home/care_home.dart`.
  - Hecho cuando: ante un rechazo el formulario vuelve con los datos y el consentimiento dado se reutiliza; con el cupo lleno se avisa antes de abrir el formulario (el servidor sigue validando); prueba de widget.
  - Hecho: `newPatient` comprueba `capacity.limit`/`count` y repite el formulario con lo escrito hasta que el servidor acepta o se cancela. Pruebas antes −2, después +2. En el teléfono: Free lleno avisa sin abrir el formulario; con Premium, fecha inválida → formulario de vuelta con los datos → fecha corregida → creado sin repetir el consentimiento (`PatientConsent` guardado).
