# 015 — Integración de `vigia-unificado` e iOS en el alcance

Estado: borrador documental. Fecha: 2026-10-26.
Módulo: cambio transversal en `mobile/`, `web/` (CuidadosApp, PlanesApp, core, plantillas) y documentación. Fuente: comparación de este repositorio con [Sndrpaola/vigia-unificado](https://github.com/Sndrpaola/vigia-unificado) y pedidos del propietario del 2026-10-26: «prepara la spec con la lista, ademas quiero incluir iOS al alcance».
Implementación autorizada: NO. Revisión del usuario: pendiente (P-015-01..04).

## Problema y resultado

Hay dos copias de VIGIA que se separaron el 2026-10-22 en el commit `cb064b6` («incorpora la reorganización en web/, mobile/ y edge/»):

- **`vigia-demo`** (este repositorio, rama `develop`): 53 commits posteriores con las specs 011 (cierre), 012 (caídas), 013 (cuidado delegado) y 014 (privacidad).
- **`vigia-unificado`**: un único commit del 2026-10-26 (`b4368e3`, autora Sndrpaola) con unas 1.900 líneas reales en 48 archivos. Contiene un rediseño de la app, el catálogo de planes en la app, una descarga estable del APK y la preparación de iOS (CocoaPods y Xcode) hecha en macOS. También trae cambios que contradicen decisiones vigentes y archivos que no deben versionarse.

Además, el propietario reincorpora **iOS al alcance** ([D-068](../../docs/DECISIONES.md)), lo que sustituye a D-011-02.

Resultado esperado: una sola base (`develop` de este repositorio) que conserva todo lo de 012–014, incorpora lo útil de `vigia-unificado` y entrega la app en iPhone con las mismas funciones por rol que en Android, con evidencia registrada por plataforma.

## Inventario de la comparación

Base de la comparación: `cb064b6` contra `b4368e3`, sin contar las diferencias que son solo de fin de línea (CRLF/LF). Esas diferencias afectan a unos 230 archivos sin cambio real y **no se traen**.

### Se trae (lista A)

| # | Pieza de `vigia-unificado` | Archivos | Requisito |
|---|---|---|---|
| A1 | Sistema visual de la app: colores y `PlanPill` | `mobile/lib/shared/vigia_design.dart` (nuevo) | RF-015-02 |
| A2 | Inicio rediseñado | `mobile/lib/features/home/home_overview.dart` (nuevo), `care_home.dart` (conflicto) | RF-015-02 |
| A3 | Tarjeta de agenda | `mobile/lib/shared/care_agenda_card.dart` (nuevo) | RF-015-02 |
| A4 | Tarjeta de resumen del paciente | `mobile/lib/features/patients/patient_summary_card.dart` (nuevo) | RF-015-02 |
| A5 | Ajustes de navegación y del panel de posturas | `mobile/lib/app/vigia_app.dart`, `mobile/lib/features/posture/posture_hub.dart` | RF-015-02 |
| A6 | Panel de plan con comparación de planes | `mobile/lib/features/subscription/subscription_panel.dart` (conflicto), `mobile/test/subscription_test.dart` (nuevo) | RF-015-03, 04 |
| A7 | Catálogo de planes en la API | `web/PlanesApp/entitlements.py` (`mobile_catalog`, `mobile_capabilities`), `web/CuidadosApp/api/views.py` (conflicto), prueba en `web/CuidadosApp/test_mobile.py` (conflicto) | RF-015-03 |
| A8 | Descarga estable del APK | `web/core/mobile_demo_urls.py`, `web/templates/mobile_demo_download.html`, `mobile/tool/build_android.sh` (nuevo), `.gitignore` (`/artifacts/`, `.tooling/`) | RF-015-05 |
| A9 | Marca VIGIA en la web | `web/static/img/vigia.svg` (nuevo); favicon y logo en `components/Layout/base.html` (conflicto), `account/Layout/base_simple.html`, `account/login.html`, `components/navbar/navbar_desktop.html`, `pages/PlanesApp/catalogo.html` | RF-015-06 |
| A10 | Preparación iOS con CocoaPods | `mobile/pubspec.yaml` (`enable-swift-package-manager: false`), `mobile/ios/Podfile.lock`, `Runner.xcodeproj/project.pbxproj`, `Runner.xcworkspace/contents.xcworkspacedata`, `Runner/AppDelegate.swift` | RF-015-09 |
| A11 | Guía de instalación en el celular | Contenido de `docs/INSTALACION_CELULAR.md`, **reescrito** según RF-015-07 | RF-015-07 |

### No se trae (lista B)

| # | Cambio de `vigia-unificado` | Motivo |
|---|---|---|
| B1 | Borrado de `CLAUDE.md` | Es la guía vigente del proyecto |
| B2 | Sección «Ubicaciones vigentes» añadida a `AGENTS.md` | Ya está cubierta por AGENTS.md y D-011-03 |
| B3 | Re-exportaciones `mobile/lib/api.dart`, `care.dart`, `phone_pose*.dart`, `pose_classifier.dart` | Eliminadas por D-011-03 punto 2 |
| B4 | Cambios a `specs/011/tasks.md` y `spec.md` | Borran la reconciliación del 2026-10-22 y reabren estados ya cerrados. T-011-10 se trata en esta spec |
| B5 | `.DS_Store`, `mobile/plugins/vigia_pose/android/.gradle/`, `.work-025/` | Archivos de sistema, caché y registros locales con rutas personales (D-011-03 punto 3) |
| B6 | `docs/ORGANIZACION.md` | Duplica README y ARQUITECTURA_BASE con comandos solo de macOS |
| B7 | `INSTALACION_CELULAR.md` tal cual | Trae una IP fija, la contraseña de la demo en texto y comandos solo de macOS. Se reescribe (A11) |
| B8 | Evidencias de `specs/010` y `specs/011/evidencia` de esa copia | Son de otra máquina y de otra versión del código. Se citan como antecedente en `validation.md`, no se copian |
| B9 | Diferencias solo de fin de línea en ~230 archivos | No tienen cambio real |
| B10 | Ediciones de `docs/ESTADO_PROYECTO.md`, `DECISIONES.md`, `TRAZABILIDAD.md`, `PROYECTO.md` y `README.md` de esa copia | Desactualizadas frente a 012–014. Los hechos útiles (por ejemplo, el estado de Xcode) se registran en esta spec |

### Archivos modificados en ambas copias

| Archivo | Cambios de este repositorio desde `cb064b6` | Resolución |
|---|---|---|
| `mobile/lib/features/home/care_home.dart` | Roles (013), aviso de política y consentimiento (014), detalles de interfaz (T-011-12..14) | Base local; se insertan A2–A4 sin perder las funciones por rol ni de privacidad |
| `mobile/lib/features/subscription/subscription_panel.dart` | Detalle de interfaz (`b035678`) | Base de `vigia-unificado`; se vuelve a aplicar la corrección de `b035678` |
| `web/CuidadosApp/api/views.py` | API por rol (013) y consentimiento (014) | Base local; se cambia solo `capabilities` → `mobile_capabilities` en `MeView` y `CapabilitiesView` |
| `web/CuidadosApp/test_mobile.py` | Pruebas de 011 y 012 | Base local; se agrega la prueba del catálogo |
| `web/templates/components/Layout/base.html` | Mensajes emergentes que se cierran solos | Base local; se cambia solo el favicon |
| Documentación (`README.md`, `AGENTS.md`, `CLAUDE.md`, `docs/*`, `specs/010`, `specs/011`, `specs/README.md`, `mobile/README.md`, `.gitignore`) | Varios | Base local; se agregan solo los hechos de A8, A10 y A11 y lo que exige D-068 |

## Actores y permisos

No se agregan permisos nuevos. Se aplica la matriz por rol de la [spec 013](../013-cuidado-delegado/spec.md) y la puerta de consentimiento de la [spec 014](../014-privacidad/spec.md) en ambas plataformas.

| Acción / datos | Anónimo | Titular | Familiar | Cuidador | Superusuario |
|---|---|---|---|---|---|
| Ver el catálogo de planes en la app (`plans` en `/me` y `/capabilities`) | No (401, igual que hoy) | Sí | Sí | Sí, solo lectura | Sí |
| Cambiar de plan | No | Solo en la web (HU-07) | Solo en la web, de su propia cuenta | Solo en la web, de su propia cuenta | Solo en la web |
| Descargar el APK de la demo | Sí, solo en `core.mobile_demo_settings` | Igual | Igual | Igual | Igual |
| Usar la app en iPhone | No | Igual que en Android | Igual que en Android | Igual que en Android | Igual que en Android |

Los precios del catálogo ya son públicos en `/planes/`. El catálogo no expone datos de otras cuentas.

## Alcance y exclusiones

Incluye: las piezas de la lista A, con sus conflictos resueltos; la resolución de los archivos modificados en ambas copias; iOS como plataforma soportada (compilación, instalación en iPhone, avisos locales, cámara con MediaPipe y push si P-015-01 lo permite); y la actualización de la documentación que hoy declara iOS fuera de alcance.

No incluye: lo de la lista B; publicación en App Store o Google Play; TestFlight (salvo que P-015-01 elija la opción B); iPad ni orientación horizontal; compilar iOS en Windows, que no es posible; cambios de reglas de negocio, de precios o de permisos; migraciones de base de datos.

## Historias y flujo

1. **Integración.** El equipo crea `feature/015-integracion-unificado` desde `develop` y trae cada pieza de la lista A en un commit por tarea. No hace `git merge` del repositorio externo.
2. **App rediseñada.** Titular, familiar y cuidador abren la app y ven el inicio, la agenda y el resumen del paciente con el nuevo diseño. Cada rol conserva las acciones permitidas por la 013, y siguen apareciendo el aviso de política y el consentimiento de la 014.
3. **Plan en la app.** La persona abre «Plan», compara Free, Plus y Premium con los precios y beneficios del servidor y pulsa «Cambiar plan en la web», que abre el portal.
4. **Android de prueba.** El equipo ejecuta el script de compilación. La página `/descargar/` ofrece el APK solo si existe.
5. **iPhone.** En un Mac con Xcode, el equipo instala los pods, compila para el simulador y luego instala en un iPhone físico. Inicia sesión contra el servidor de la red local y repite en el iPhone las pruebas físicas de Android (avisos con pantalla bloqueada, cierre de sesión, cámara, roles y privacidad).

## Requisitos funcionales

Integración:

- RF-015-01: La integración parte de `develop` y trae solo las piezas de la lista A. SI un archivo de `vigia-unificado` difiere solo en fin de línea, ENTONCES se conserva la versión de este repositorio. Ningún RF de 011–014 queda sin cumplir después de la integración (las suites de Django, Flutter y Edge pasan).
- RF-015-02: CUANDO un titular, familiar o cuidador abre el inicio de la app, EL SISTEMA muestra el diseño de A1–A5 con las acciones que su rol permite según la 013, el aviso de política pendiente y el consentimiento por paciente de la 014.
- RF-015-03: CUANDO la app pide `/api/v1/me` o `/api/v1/capabilities`, EL SISTEMA agrega `plans` (código, nombre, descripción, precio en CLP, moneda, cupo de pacientes activos y beneficios de los planes activos `free`, `plus` y `pro`, leídos de la base) y `change_plan_path: "/planes/"`. Los campos existentes no cambian. Leer el catálogo no modifica la suscripción.
- RF-015-04: CUANDO la persona abre el panel de plan, EL SISTEMA muestra su plan vigente y los planes del catálogo, y deriva el cambio de plan al portal web. La app no cambia planes ni muestra precios fijos en el código.
- RF-015-05: CUANDO existe `artifacts/android/VIGIA-android-prueba.apk`, la página `/descargar/` de la demo lo ofrece. SI no existe, ENTONCES usa el APK debug de `mobile/build/` y, si tampoco existe, muestra que el APK no está disponible y la descarga responde 404. `artifacts/` y `.tooling/` no se versionan.
- RF-015-06: El portal muestra la marca VIGIA (`img/vigia.svg`) en el favicon, el inicio de sesión, las páginas de cuenta, la barra de navegación, el catálogo público y la página de descarga.
- RF-015-07: `docs/INSTALACION_CELULAR.md` explica cómo instalar y probar en Android (Windows o macOS) y en iPhone (macOS). No contiene una IP fija, contraseñas ni rutas personales, y enlaza la validación de esta spec.

iOS (D-068):

- RF-015-08: La documentación vigente (`CLAUDE.md`, `AGENTS.md`, `README.md`, `mobile/README.md`, `docs/PROYECTO.md`, `docs/MOVIL_DESARROLLO.md`, `specs/README.md`) declara Android e iOS en el alcance, Android primero, y las compilaciones iOS solo en macOS. T-011-10 conserva su ID y su trabajo pasa a esta spec.
- RF-015-09: En macOS con Xcode, `pod install` y `flutter build ios --simulator --debug` terminan sin errores con el objetivo mínimo iOS 15.0, CocoaPods (A10) y el `Podfile.lock` versionado.
- RF-015-10: En un iPhone físico, la app se instala, inicia sesión contra un servidor de la red local (ATS `NSAllowsLocalNetworking`, ya presente) y ofrece las mismas funciones por rol y la misma puerta de privacidad que en Android.
- RF-015-11: En iOS, al activar los avisos del reloj de cuidados, EL SISTEMA pide permiso de notificaciones. Con el permiso concedido, el aviso llega con la pantalla bloqueada. Con el permiso denegado, la app lo informa sin fallar. Al cerrar sesión, los avisos se cancelan. No se programan más de 60 avisos pendientes (iOS admite 64).
- RF-015-12: En iOS, el análisis con la cámara del teléfono pide permiso de cámara, procesa la imagen en el dispositivo con MediaPipe (`vigia_pose`, `MediaPipeTasksVision` 0.10.21) y envía al servidor solo metadatos con `platform: "ios"`. Sin video a la nube.
- RF-015-13: SI P-015-01 elige la opción B, ENTONCES el push de riesgo llega a iOS por APNs a través de Firebase, con el texto genérico de D-058 y los destinatarios de D-063. SI elige la opción A, ENTONCES la app en iOS indica que los avisos push no están disponibles en esa instalación, sin fingir un envío, y HU-05 se comprueba en Android.

## Datos y reglas

- Sin modelos ni migraciones nuevas. El catálogo se lee de `Plan` y `PlanBenefit` (007) en cada petición, sin copias de precios en la app.
- El contrato de la API agrega campos y no quita ninguno: la app y el nodo ya instalados siguen funcionando (AGENTS.md, compatibilidad de API).
- Identificadores de app: Android `cl.vigia.vigia_mobile`, iOS `cl.vigia.vigiaMobile`. No se cambian.
- Credenciales de Apple, APNs y Firebase (`GoogleService-Info.plist`, clave `.p8`) nunca se versionan (D-054).
- Los commits que traen código de `vigia-unificado` reconocen la autoría de Sndrpaola con un `Co-Authored-By` que usa la identidad del commit original `b4368e3`.

## Criterios de aceptación

| RF | Dado / cuando | Entonces |
|---|---|---|
| RF-015-01 | La rama integrada, al ejecutar las suites | Django, Edge y Flutter pasan, con al menos las pruebas de hoy más las nuevas. `git diff develop` no contiene archivos de la lista B |
| RF-015-02 | Un cuidador abre el inicio rediseñado | Ve la agenda del día y la última postura, sin historial completo (D-062) ni gestión de accesos |
| RF-015-02 | Un titular con un paciente sin consentimiento | Ve la ficha y el aviso de consentimiento; el registro nuevo queda bloqueado (D-066) |
| RF-015-03 | Se cambia el precio de Plus en la base y se llama a `/capabilities` | La respuesta trae el precio nuevo; plan, versión y monto de la suscripción del usuario no cambian |
| RF-015-03 | Sin sesión | 401, igual que hoy |
| RF-015-04 | Prueba de widget del panel con tres planes | Muestra los tres con su precio y el botón abre `/planes/` |
| RF-015-05 | Sin APK en `artifacts/` ni en `build/` | La página dice que no está disponible y `/descargar/android.apk` responde 404 |
| RF-015-06 | Navegador en login, catálogo público y portal | Se ve `vigia.svg`; no queda `logo.svg` en esas plantillas |
| RF-015-07 | Revisión de la guía | Sin IP fija, contraseñas ni rutas personales; enlaces válidos |
| RF-015-08 | Búsqueda de «iOS fuera de alcance» en la documentación vigente | Solo aparece en antecedentes fechados y en D-011-02 |
| RF-015-09 | Mac con Xcode | El build de simulador termina; el registro queda en `validation.md` |
| RF-015-10 | iPhone físico | Instalación, login y flujo titular/familiar/cuidador registrados con fecha, modelo y versión de iOS |
| RF-015-11 | iPhone con permiso concedido y pantalla bloqueada | El aviso llega; tras cerrar sesión no llega ninguno |
| RF-015-11 | iPhone con permiso denegado | La app lo informa y no falla |
| RF-015-12 | Análisis con la cámara del iPhone | La observación guardada tiene `platform: "ios"` y no hay imagen en el servidor |
| RF-015-13 | Opción B: caída simulada desde el nodo | El push llega al iPhone con el texto genérico; se registra el tiempo |

## No funcionales

- Sin video a la nube, también en iOS.
- Las cifras de latencia (alerta ≤ 10 s, inferencia < 100 ms) siguen siendo objetivos. Si se miden en iPhone, se registran en `validation.md`; no se declaran cumplidas sin esa evidencia.
- Español es-CL en los textos nuevos, incluidos los permisos de iOS (`NSCameraUsageDescription` y `NSLocalNetworkUsageDescription`, ya en español).
- El rediseño mantiene el contraste y los tamaños táctiles de la app actual. La revisión visual la hace el propietario (P-015-03).

## Compatibilidad

- Specs 010, 011 (reloj y avisos locales), 012 (push de caída), 013 (roles) y 014 (privacidad): se preservan en Android y se extienden a iOS.
- D-011-02 queda sustituida por D-068. D-011-03 se mantiene: no vuelven las re-exportaciones ni los archivos ignorados.
- La app instalada antes de esta spec sigue funcionando con el backend nuevo (solo se agregan campos).

## Supuestos y decisiones pendientes

Supuestos:

- El trabajo iOS se hace en el Mac de la autora de `vigia-unificado`, que ya tiene Xcode 27.1, la licencia aceptada y simuladores iOS 26.4 (según su `validation.md` del 2026-10-22). El 2026-10-22 ese equipo necesitaba liberar de 8 a 10 GB para compilar.
- `MediaPipeTasksVision` puede no correr en simuladores de Apple Silicon. Si pasa, RF-015-12 se comprueba solo en iPhone físico y se registra el límite.

Decisiones del propietario:

- **P-015-01 — Instalación y push en iPhone.**
  - (A) Apple ID gratuito (Personal Team): instalación por cable en un iPhone propio, perfil que vence a los 7 días y sin push APNs.
  - (B) Apple Developer Program (pago anual): push APNs real y TestFlight para el equipo.

  Propuesta: A para el prototipo, con HU-05 comprobada en Android; B solo si el informe exige el push en iPhone.
- **P-015-02 — Equipo macOS.** Confirmar quién compila y prueba iOS y en qué equipo, porque la evidencia iOS solo puede venir de macOS. Propuesta: el Mac de la autora de `vigia-unificado`, trabajando en ramas de este repositorio.
- **P-015-03 — Diseño de la app.** Adoptar el rediseño de `vigia-unificado` como diseño vigente. Esto sustituye la preservación del diseño móvil aceptado en 010 (D-011-01). Propuesta: adoptarlo, sujeto a revisión visual en Android y iPhone.
- **P-015-04 — Repositorio único.** Propuesta: `develop` de este repositorio queda como única fuente. `vigia-unificado` queda como antecedente de solo lectura y el trabajo nuevo de su autora entra por ramas `feature/NNN-…` y PR (D-059).

## Revisión y cambios

- 2026-10-26: borrador creado a partir de la comparación de ambos repositorios. D-068 (iOS en el alcance) registrada por pedido explícito del propietario. Sin autorización de implementación.
