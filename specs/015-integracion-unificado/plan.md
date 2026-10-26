# Plan técnico — 015 / Integración de `vigia-unificado` e iOS

Spec: [spec.md](spec.md). Estado: propuesta; sin código.
Autorización de implementación: pendiente.

## Inspección de la base

- Comparación hecha el 2026-10-26 sobre un clon temporal de `vigia-unificado` (fuera del repositorio), con `develop` en `ab9eab8`. El punto de separación es `cb064b6`. La diferencia `cb064b6..b4368e3` sin cambios de fin de línea (`git diff --ignore-cr-at-eol`) es de 66 archivos, con +2.089 y −669 líneas. Excluyendo evidencias y `.work-025`, son 48 archivos.
- Este repositorio, desde `cb064b6`: 53 commits, 148 archivos, specs 011–014.
- iOS en este repositorio: `mobile/ios/` completo (iOS 15.0, `cl.vigia.vigiaMobile`, ATS `NSAllowsLocalNetworking`, `UIBackgroundModes` `remote-notification`, permisos de cámara y red local en español). El plugin `mobile/plugins/vigia_pose/ios/` usa `PoseLandmarker` con `MediaPipeTasksVision` 0.10.21. `mobile/lib/notifications/local_reminders.dart` ya configura `DarwinInitializationSettings` y pide permisos en iOS. `care_home.dart` y `phone_pose_native.dart` ya informan `platform: ios`. No hay `Podfile.lock` y nunca se compiló iOS en Windows.
- Los widgets nuevos de `vigia-unificado` (`vigia_design.dart`, `home_overview.dart`, `care_agenda_card.dart`, `patient_summary_card.dart`) son de presentación: solo importan `flutter/material.dart`, `shared/care_widgets.dart` y `vigia_design.dart`. No usan `own_patient`, que se eliminó en la 013.

## Diseño propuesto

Un cambio transversal sin app nueva. Cada pieza de la lista A se trae como parche puntual desde un remoto de solo lectura. No se usa `git merge`, porque arrastraría la lista B y unos 230 archivos con diferencias solo de fin de línea:

```bash
git remote add unificado https://github.com/Sndrpaola/vigia-unificado.git   # solo lectura
git fetch unificado
git checkout -b feature/015-integracion-unificado develop
# archivos nuevos:   git checkout unificado/main -- <ruta>   y normalizar con .gitattributes / dos2unix si aplica
# archivos en ambos: git diff --ignore-cr-at-eol cb064b6 unificado/main -- <ruta>  → aplicar a mano sobre la versión local
```

El remoto `unificado` se quita al cerrar la spec.

## Mapa por requisito

| RF | Archivos | Cambio previsto | Evidencia prevista |
|---|---|---|---|
| RF-015-01 | Todos los de la lista A | Parches por tarea. Comprobar que no entra nada de la lista B | `git diff --stat develop` revisado; las tres suites |
| RF-015-02 | Nuevos: `shared/vigia_design.dart`, `shared/care_agenda_card.dart`, `features/home/home_overview.dart`, `features/patients/patient_summary_card.dart`. Existentes: `features/home/care_home.dart`, `app/vigia_app.dart`, `features/posture/posture_hub.dart` | Traer los widgets e integrarlos en `care_home.dart` manteniendo las ramas por rol (013), `privacy.dart` y `access.dart` (014/013) y las correcciones T-011-12..14 | `patient_roles_test`, `privacy_test`, `login_consent_test`, `clock_panel_test`, `interface_details_test` siguen pasando. Nueva prueba de widget del inicio por rol |
| RF-015-03 | `web/PlanesApp/entitlements.py`, `web/CuidadosApp/api/views.py`, `web/CuidadosApp/test_mobile.py` | Agregar `mobile_catalog()` y `mobile_capabilities()`; usarlas en `MeView` y `CapabilitiesView` | Prueba portada `test_mobile_catalog_matches_web_and_read_does_not_change_subscription` y una prueba de 401 sin sesión |
| RF-015-04 | `features/subscription/subscription_panel.dart`, `test/subscription_test.dart` | Versión de `vigia-unificado` más la corrección de `b035678` | `subscription_test.dart` |
| RF-015-05 | `web/core/mobile_demo_urls.py`, `web/templates/mobile_demo_download.html`, `mobile/tool/build_android.sh`, `.gitignore` | `android_artifact()`, `apk_available` y el script; ignorar `/artifacts/` y `.tooling/` | Prueba Django de la página con y sin APK (404) |
| RF-015-06 | `web/static/img/vigia.svg` y las 6 plantillas de A9 | Cambiar `logo.svg` por `vigia.svg` | Las plantillas compilan; revisión en navegador |
| RF-015-07 | `docs/INSTALACION_CELULAR.md` (nuevo) | Guía Android (Windows con Git Bash o macOS) e iPhone (macOS), con marcadores `<IP-del-servidor>` y la cuenta demo indicada solo como «ver `seed_mobile_demo`» | Revisión de enlaces |
| RF-015-08 | `CLAUDE.md`, `AGENTS.md`, `README.md`, `mobile/README.md`, `docs/PROYECTO.md`, `docs/MOVIL_DESARROLLO.md`, `docs/ENTORNO_Y_VERIFICACION.md`, `specs/README.md`, `specs/011/tasks.md` (nota fechada en T-011-10) | Texto de alcance según D-068 | `rg -n "iOS fuera de alcance"` solo en antecedentes |
| RF-015-09 | `mobile/pubspec.yaml`, `mobile/ios/Podfile.lock`, `project.pbxproj`, `contents.xcworkspacedata`, `AppDelegate.swift` | Regenerar en macOS con `flutter pub get` y `pod install` sobre el `pubspec` actual. Los archivos de `vigia-unificado` sirven de referencia, no se copian a ciegas | Registro de `flutter build ios --simulator --debug` |
| RF-015-10 | Firma en Xcode (equipo de P-015-01); sin cambio de código previsto | Instalar con `flutter run --release` o desde Xcode en el iPhone | Registro con modelo, versión de iOS y fecha |
| RF-015-11 | `mobile/lib/notifications/local_reminders.dart` (revisar, sin cambio previsto) | Comprobar permisos, el límite de 60 pendientes y la cancelación en iOS | Prueba física. Las pruebas de `reminders_test.dart` y `reminder_lifecycle_test.dart` siguen pasando |
| RF-015-12 | `plugins/vigia_pose/ios/`, `features/detection/phone_pose_native.dart` | Comprobar el modelo `.task` en el bundle de iOS y la inferencia | Prueba física y observación con `platform: "ios"` en la base de prueba |
| RF-015-13 | Opción B: capacidad Push Notifications, clave APNs en Firebase, `GoogleService-Info.plist` fuera del repositorio. Opción A: mensaje en la app | Según P-015-01 | Push recibido con tiempo medido (B), o mensaje visible (A) |

## Datos y contratos

- `GET /api/v1/me` → `capabilities` y `GET /api/v1/capabilities` agregan `plans: [{code, name, description, price_clp, currency, max_active_patients, benefits[]}]` y `change_plan_path`. Solo se agregan campos: la app instalada los ignora y el nodo Edge no usa estos endpoints.
- `mobile_catalog()` usa `prefetch_related("benefits")` para no generar N+1 consultas (el mismo problema que QA-2026-10-22-19 en el listado de usuarios).
- Sin modelos, formularios ni migraciones nuevas.

## Permisos e interfaz

- Los endpoints mantienen `MobileView`: sesión, puerta de consentimiento (014) y 401 sin sesión.
- La interfaz móvil respeta la matriz de la 013 en cada widget nuevo: el cuidador no ve el historial completo, la gestión de accesos ni los nodos.
- Plantillas web: solo cambia el recurso de imagen; no se cambian bloques ni bases.

## Migraciones y reversión

Ninguna migración. Para revertir, basta revertir los commits de la rama; un commit por tarea permite revertir piezas sueltas (por ejemplo, solo el rediseño).

## Plan de pruebas

- Windows, en cada tarea: `manage.py check`, `makemigrations --check --dry-run`, `manage.py test UsuarioApp homeApp PlanesApp CuidadosApp PrivacidadApp --settings=core.test_settings`; `flutter analyze` y `flutter test` desde `mobile/`; `python -m unittest edge.test_posture edge.test_fall edge.test_run`.
- Pruebas nuevas: catálogo móvil (Django), página de descarga con y sin APK (Django), panel de plan (Flutter), inicio por rol con el nuevo diseño (Flutter).
- Navegador: login, catálogo público, portal y `/descargar/` con la marca nueva, en claro y oscuro.
- Android físico: repetir el recorrido del 2026-10-25 con el diseño nuevo.
- macOS e iPhone: RF-015-09..13 según P-015-01/02.

## Riesgos, alternativas y dependencias

- **Conflicto en `care_home.dart`.** Es el más delicado: el rediseño reescribió unas 500 líneas que la 013 y la 014 también cambiaron. Mitigación: partir de la versión local e insertar los widgets nuevos, no al revés; las pruebas de rol y privacidad protegen el resultado.
- **Diferencias de fin de línea.** Se normalizan al traer cada archivo. Un `.gitattributes` con `* text=auto` evitaría que se repita, pero es un cambio transversal que queda fuera de esta spec y se propone aparte.
- **iOS solo en macOS.** Windows no compila iOS. Sin P-015-02 resuelta, T-015-08..11 quedan bloqueadas y el resto de la spec puede avanzar.
- **MediaPipe en simulador.** Ver el supuesto de la spec; la prueba de cámara se hace en un iPhone físico.
- **Espacio en el Mac.** El build iOS falló por falta de espacio el 2026-10-22; se necesitan de 8 a 10 GB libres.
- **Alternativa descartada:** adoptar `vigia-unificado` como base. Perdería 012–014 y reabriría decisiones cerradas.

## Documentos afectados

`specs/README.md` (índice), `docs/DECISIONES.md` (D-068 y respuestas P-015), `docs/ESTADO_PROYECTO.md`, `docs/TRAZABILIDAD.md`, los de RF-015-08, la nueva `docs/INSTALACION_CELULAR.md` y `specs/015-integracion-unificado/validation.md` (al validar).

## Decisiones para implementar

P-015-01..04 de la spec. Las tareas sin iOS (T-015-01..07) solo dependen de P-015-03 (diseño) y P-015-04 (repositorio único). Esta fase termina antes del código.
