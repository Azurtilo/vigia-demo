# Tareas — 015 / Integración de `vigia-unificado` e iOS

Spec: [spec.md](spec.md). Plan: [plan.md](plan.md).
Estado: en implementación. Implementación autorizada: T-015-01..07 (2026-10-26).
No ejecutar tareas de código por el hecho de aparecer aquí. Rama prevista: `feature/015-integracion-unificado`, un commit por tarea (D-059).

## Integración (Windows)

- [x] T-015-01 — Preparar la rama y el remoto de solo lectura.
  - RF: RF-015-01. Componente: repositorio.
  - Depende de: autorización y P-015-04.
  - Hecho cuando: existe la rama desde `develop`, el remoto `unificado` está descargado y las tres suites pasan sin cambios como línea base registrada.
- [x] T-015-02 — Catálogo de planes en la API (A7).
  - RF: RF-015-03. Componente: web.
  - Depende de: T-015-01.
  - Archivos previstos: `web/PlanesApp/entitlements.py`, `web/CuidadosApp/api/views.py`, `web/CuidadosApp/test_mobile.py`.
  - Hecho cuando: pasan la prueba portada del catálogo y la de 401 sin sesión; las suites de 013/014 siguen pasando.
- [x] T-015-03 — Panel de plan en la app (A6).
  - RF: RF-015-04. Componente: mobile.
  - Depende de: T-015-02.
  - Archivos previstos: `mobile/lib/features/subscription/subscription_panel.dart`, `mobile/test/subscription_test.dart`.
  - Hecho cuando: la versión de `vigia-unificado` queda con la corrección de `b035678` aplicada y `subscription_test.dart` y `flutter analyze` pasan.
- [x] T-015-04 — Rediseño de la app (A1–A5) integrado con roles y privacidad.
  - RF: RF-015-02. Componente: mobile.
  - Depende de: T-015-01 y P-015-03.
  - Archivos previstos: `mobile/lib/shared/vigia_design.dart`, `mobile/lib/shared/care_agenda_card.dart`, `mobile/lib/features/home/home_overview.dart`, `mobile/lib/features/patients/patient_summary_card.dart`, `mobile/lib/features/home/care_home.dart`, `mobile/lib/app/vigia_app.dart`, `mobile/lib/features/posture/posture_hub.dart`, una prueba nueva de inicio por rol.
  - Hecho cuando: todas las pruebas Flutter pasan, incluidas `patient_roles_test`, `privacy_test`, `login_consent_test` e `interface_details_test`, y la prueba nueva comprueba lo que ve cada rol.
- [x] T-015-05 — Descarga estable del APK (A8).
  - RF: RF-015-05. Componente: web y mobile.
  - Depende de: T-015-01.
  - Archivos previstos: `web/core/mobile_demo_urls.py`, `web/templates/mobile_demo_download.html`, `mobile/tool/build_android.sh`, `.gitignore`, una prueba Django.
  - Hecho cuando: la página indica si hay APK, la descarga responde 404 sin APK, el script corre en Git Bash de Windows y `artifacts/` queda ignorado.
- [x] T-015-06 — Marca VIGIA en la web (A9).
  - RF: RF-015-06. Componente: web.
  - Depende de: T-015-01.
  - Archivos previstos: `web/static/img/vigia.svg` y las plantillas de A9.
  - Hecho cuando: las plantillas compilan y la marca se ve en navegador, en claro y oscuro, en login, catálogo público, portal y descarga.
- [x] T-015-07 — Android físico con el diseño nuevo.
  - RF: RF-015-01, 02, 04. Componente: mobile.
  - Depende de: T-015-03..06.
  - Hecho cuando: el recorrido del 2026-10-25 (login, HU-03, HU-04, avisos con pantalla bloqueada, cierre de sesión, roles de la 013, privacidad de la 014) y el panel de plan quedan registrados en `validation.md`.

## iOS (macOS)

- [ ] T-015-08 — Dependencias iOS y build de simulador (A10).
  - RF: RF-015-09. Componente: mobile/ios.
  - Depende de: T-015-04 y P-015-02.
  - Archivos previstos: `mobile/pubspec.yaml`, `mobile/ios/Podfile.lock`, `mobile/ios/Runner.xcodeproj/project.pbxproj`, `mobile/ios/Runner.xcworkspace/contents.xcworkspacedata`, `mobile/ios/Runner/AppDelegate.swift`.
  - Hecho cuando: `pod install` y `flutter build ios --simulator --debug` terminan en macOS con el `pubspec` actual y el registro queda en `validation.md`. `flutter analyze` y `flutter test` siguen pasando en Windows.
- [ ] T-015-09 — Instalación y flujo por rol en iPhone físico.
  - RF: RF-015-10. Componente: mobile/ios.
  - Depende de: T-015-08 y P-015-01.
  - Hecho cuando: quedan registrados la instalación, el login por la red local y el flujo titular/familiar/cuidador con aviso de política y consentimiento, con modelo, versión de iOS y fecha.
- [ ] T-015-10 — Avisos locales y cámara en iPhone.
  - RF: RF-015-11, 12. Componente: mobile/ios.
  - Depende de: T-015-09.
  - Hecho cuando: el aviso llega con la pantalla bloqueada y el permiso concedido; con el permiso denegado la app lo informa; tras cerrar sesión no llega ningún aviso; el análisis con la cámara guarda una observación `platform: "ios"` sin imagen en el servidor.
- [ ] T-015-11 — Push en iOS según P-015-01.
  - RF: RF-015-13. Componente: mobile/ios y web.
  - Depende de: T-015-09 y P-015-01.
  - Hecho cuando: con la opción B, una caída simulada produce un push en el iPhone con el texto genérico y el tiempo queda medido; con la opción A, la app muestra que el push no está disponible y la limitación queda registrada.

## Cierre

- [ ] T-015-12 — Documentación de alcance e instalación.
  - RF: RF-015-07, 08. Componente: docs.
  - Depende de: T-015-05 (guía Android); T-015-09 (guía iPhone).
  - Archivos previstos: `docs/INSTALACION_CELULAR.md` y los documentos de RF-015-08.
  - Hecho cuando: la guía no tiene IP fija, contraseñas ni rutas personales, los enlaces son válidos y «iOS fuera de alcance» solo aparece en antecedentes.
- [ ] T-015-13 — Validación y cierre documental.
  - RF: RF-015-01..13.
  - Depende de: tareas anteriores.
  - Hecho cuando: los resultados reales están en `validation.md` y la trazabilidad, el estado y el índice están actualizados; se quita el remoto `unificado`; queda la PR hacia `develop` sin fusionar.

## Autorización posterior
2026-10-26: «P-015-02 sandra compila iOS, y autorizo para T-015-01..06. la 07 dejala en pendiente». Autorizadas T-015-01..06; T-015-07 queda pendiente; T-015-08..13 sin autorizar. Sin merge, despliegue ni migración real.
2026-10-26: «te autorizo a la prueba en android fisico». Autorizada T-015-07. No confundir aprobación de requisitos con autorización de producción ni de publicación en tiendas.

## Ejecución
| Fecha | Tarea | Archivos / comando | Resultado / pendiente |
|---|---|---|---|
| 2026-10-26 | T-015-01 | Rama `feature/015-integracion-unificado` (sobre `docs/015-integracion-unificado`, que parte de `develop` `ab9eab8`); `git remote add unificado` + `git fetch unificado` (`unificado/main` = `b4368e3`) | Línea base: `check` y `makemigrations --check` sin cambios; Django 227 OK (con PrivacidadApp); Edge 22 OK; `flutter analyze` sin problemas; Flutter 39 OK |
| 2026-10-26 | T-015-02 | `web/PlanesApp/entitlements.py` (`mobile_catalog`, `mobile_capabilities`), `web/CuidadosApp/api/views.py`, `web/CuidadosApp/test_mobile.py` | Prueba portada del catálogo y nueva de 401 sin sesión; `manage.py test CuidadosApp.test_mobile PlanesApp`: 65 OK |
| 2026-10-26 | T-015-03 | `mobile/lib/features/subscription/subscription_panel.dart`, `mobile/test/subscription_test.dart`, `mobile/lib/shared/vigia_design.dart` (A1, adelantado porque el panel lo usa) | Versión de `vigia-unificado` con la corrección de `b035678` (botón de avisos y texto sin cámara sin detección) y el enlace leído de `change_plan_path`. `flutter analyze` sin problemas; Flutter 41 OK |
| 2026-10-26 | T-015-04 | `care_home.dart` (base local), `home_overview.dart`, `patient_summary_card.dart`, `care_agenda_card.dart`, `vigia_app.dart`, `posture_hub.dart`; prueba nueva `test/home_redesign_test.dart`; `interface_details_test.dart` ajustada | Se conservan la puerta de política (T-014-12), «Unirme con un código» y el rol en la lista (013). Sin la barra superior, «Cerrar sesión» queda bajo el aviso de política. Pestaña «Plan» → «Planes» y «ACCIONES RÁPIDAS» por el diseño adoptado (D-070). `flutter analyze` sin problemas; Flutter 43 OK. Revisión visual en Android pendiente (T-015-07) |
| 2026-10-26 | T-015-05 | `web/core/mobile_demo_urls.py` (`android_artifact`, `apk_available`), `web/templates/mobile_demo_download.html`, `mobile/tool/build_android.sh`, `.gitignore`; prueba nueva `web/CuidadosApp/test_mobile_demo.py` | Prueba Django: 3 OK (sin APK la página lo dice y la descarga da 404; se prefiere `artifacts/` sobre `build/`). `sh mobile/tool/build_android.sh` en Git Bash de Windows: APK en `artifacts/android/` en 65 s, ignorado por Git. El script usa el `flutter` del PATH si no hay `.tooling/`. Texto iPhone según D-069 |
| 2026-10-26 | T-015-06 | `web/static/img/vigia.svg`; `logo.svg` → `vigia.svg` en `base.html` (favicon), `base_simple.html`, `login.html`, `navbar_desktop.html` («VIGIA · Tu espacio de cuidado»), `catalogo.html` («VIGIA · Planes») y `mobile_demo_download.html`; título «· VIGIA»; prueba nueva `web/homeApp/test_marca.py` | Prueba Django: 3 OK (login, catálogo público, portal y descarga con `vigia.svg` y sin `logo.svg`). **Pendiente:** revisión en navegador en claro y oscuro, que no se pudo hacer en esta sesión |
| 2026-10-26 | T-015-06 (navegador) | `runserver` con `core.mobile_demo_settings` (base desechable en `.mobile-demo/`, superusuario ficticio) y Chrome sin interfaz controlado por Playwright (entorno temporal fuera del repositorio); 1280×800 y 390×844 | Login, catálogo público, descarga y portal muestran `vigia.svg`; el favicon responde 200 en todas; título «· VIGIA». Portal revisado en claro y oscuro, en escritorio y móvil. Las páginas sin sesión se ven siempre en claro porque el modo oscuro es una preferencia de cada usuario. Observación: en oscuro el trazo `#5057a0` del logo tiene poco contraste con el fondo (≈2,3:1), pero se distingue; los logotipos están exentos del criterio de contraste. Se pide la confirmación visual del propietario |
| 2026-10-26 | T-015-07 | ELI NX9, Android 16, APK debug por USB (`adb reverse`), cuentas `demo_premium` y `demo_free` y una cuenta temporal sin política | Login, HU-03, HU-04, aviso con pantalla bloqueada, error de conexión informado, panel de plan, cierre de sesión sin alarmas, rol cuidador y puerta de privacidad: OK. Dos hallazgos de interfaz sin corregir. Detalle en [validation.md](validation.md#android-físico--t-015-07-2026-10-26) |

## Reanudación
2026-10-26: spec, plan y tareas creados en fase DOCUMENTAR. Spec, plan y tareas en la rama `docs/015-integracion-unificado` (`a02a9cd`), sin código.
2026-10-26: revisión con el propietario. Lista A completa y nada de la B; P-015-01 = A (D-069), P-015-03 = adoptar (D-070), P-015-04 = sí (D-071). Siguiente paso: P-015-02 (equipo macOS, bloquea T-015-08..11) y autorización explícita de implementación de T-015-01..07.
2026-10-26: P-015-02 = Sandra (D-072). Implementadas en `feature/015-integracion-unificado` T-015-01..06 (T-015-06 revisada en navegador). Suites finales: Django 235, Edge 22 y Flutter 43 OK; `flutter analyze` sin problemas; `git diff` sin archivos de la lista B. T-015-07 hecha en el teléfono (ver [validation.md](validation.md)). Pendientes: dos hallazgos de interfaz por decidir; T-015-08..11 (iOS, Sandra en macOS) y T-015-12..13 sin autorizar. El remoto `unificado` sigue configurado hasta T-015-13. Sin PR ni merge.

## Aceptación del usuario
Pendiente; no marcarla automáticamente después de ejecutar tests.
