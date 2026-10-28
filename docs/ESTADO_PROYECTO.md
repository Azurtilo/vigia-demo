# Estado y reanudación

Fecha: 2026-10-28.

## Pendientes abiertos — consolidado al 2026-10-28

Lista única de lo que falta. El detalle vive en cada spec y en DECISIONES. «Propietario» indica que requiere dispositivo, cuenta externa, voluntarios o una decisión suya.

| # | Pendiente | Dónde | Quién |
|---|---|---|---|
| 1 | ~~Revisar y fusionar la [PR #4](https://github.com/Azurtilo/vigia-demo/pull/4)~~ Fusionada en `develop` el 2026-10-25 (`0da7eda`) | — | Hecho |
| 2 | Prueba en Android físico. **Hecho el 2026-10-25** (ELI NX9, Android 16, servidor por USB con `adb reverse`): instalación y login (T-011-09), HU-03, HU-04, permisos y aviso local con pantalla bloqueada (T-011-03), cierre de sesión sin alarmas (T-011-04), cupo Plus y bloqueo de cámara (T-011-05, parcial), flujo titular/cuidador de la 013, aceptación de política en el portal y consentimiento por paciente de la 014. Ver validaciones [011](../specs/011-ecosistema-instalable/validation.md#android-físico--2026-10-25), [013](../specs/013-cuidado-delegado/validation.md#límites-y-fallos) y [014](../specs/014-privacidad/validation.md#android-físico). **Falta:** servidor por la red local, T-011-05 con Free/Premium y reducción de cupo, revisión visual (T-011-06), validación integrada (T-011-11) | specs 011, 013, 014 | Propietario |
| 3 | Firebase de prueba con credenciales fuera del repositorio; push real con la app cerrada; medir caída → teléfono (≤ 10 s) | D-054, T-011-04, QA-15 | Propietario |
| 4 | Protocolo de caídas con voluntarios (25 caídas y 60 actividades normales desde la spec 017, que agrega deslizamientos de la cama y casos de sábanas, persona tapada y penumbra), `bench.py` con ese video (p50/p95) y ajuste de umbrales de ambas reglas | D-053, RF-017-15, `edge/README.md` | Propietario + equipo |
| 5 | Revisión legal del texto de la política antes de usar datos reales | D-067, `/privacidad/` | Propietario |
| 6 | Política de sesiones de D-056 (vencimiento, cierre de sesión remoto, revocación de nodos desde el portal web): aprobada, sin spec ni código | D-056 | Equipo (DOCUMENTAR) |
| 7 | Hallazgos de la QA del 2026-10-22 sin abordar: QA-12/13 (refactor de validación duplicada y funciones largas), QA-17 (límite de tasa en `/api/v1/edge/*`), QA-18 (HSTS al tener dominio con HTTPS), QA-20 (IDs de decisiones ambiguos). QA-07 se corrigió el 2026-10-22 (ver [QA_2026-10-26.md](QA_2026-10-26.md), sección 7) | `docs/QA_2026-10-22.md` | Equipo |
| 8 | Aplicar las migraciones (CuidadosApp 0008/0009/0010, PrivacidadApp 0001) en una base real, con respaldo y autorización | — | Propietario |
| 9 | RNF de disponibilidad ≥ 99,5 %: declarado objetivo de diseño no medido; describir la arquitectura necesaria en el informe | D-060 | Equipo (informe) |
| 10 | ~~Decidir si `.claude/skills/` se versiona~~ Versionada con ajustes ([PR #6](https://github.com/Azurtilo/vigia-demo/pull/6), `1f620a6`) | — | Hecho |
| 11 | ~~Revisar y fusionar la [PR #5](https://github.com/Azurtilo/vigia-demo/pull/5)~~ Detalles de interfaz fusionados en `develop` (`f71d1be`) | — | Hecho |
| 12 | ~~Revisar y fusionar la [PR #8](https://github.com/Azurtilo/vigia-demo/pull/8)~~ Spec 015 fusionada en `develop` el 2026-10-26 (`8d2be54`) | — | Hecho |
| 13 | iOS: dependencias y build de simulador, iPhone físico, avisos locales y cámara (T-015-08..10); mensaje de push no disponible (T-015-11, D-069) | spec 015 | Sandra (macOS), con autorización aparte |
| 14 | Programar en el servidor real `purge_expired_data` (diaria) y `send_mobile_reminders` (cada 5 min, propuesta; cadencia definitiva en P-012-01) y comprobar que corren | [OPERACION.md](OPERACION.md), QA-2026-10-26-04 | Propietario |
| 15 | Decidir cómo se activa `VIGIA_PUSH_ENABLED` en producción: hoy no se define en ninguna configuración ni se lee del entorno, así que los avisos no pueden encenderse. Requiere un cambio de configuración con spec | `send_mobile_reminders`, `push.py`, D-054 | Propietario (decisión) + equipo |
| 16 | Hallazgos de la QA del 2026-10-26 sin abordar: 07 (lock con hashes del Edge), 09 (contraseña demo en `MOVIL_DESARROLLO.md`), 10 (prueba de la API con la puerta de privacidad activa), 11 (logo con poco contraste en modo oscuro), 12 (dependencias de Flutter con versiones mayores), 13 (conteos repetidos en este estado). El 05 (push real y RNF) sigue en los pendientes 3, 4 y 9 | [QA_2026-10-26.md](QA_2026-10-26.md) | Equipo |
| 17 | ~~Revisión de calidad y correcciones 01–04, 06 y 08~~ PR #10 (informe) y PR #11 (spec 016) fusionadas el 2026-10-26 | spec 016 | Hecho |
| 18 | ~~Revisar y fusionar la [PR #12](https://github.com/Azurtilo/vigia-demo/pull/12) de la spec 017~~ Fusionada en `develop` el 2026-10-27 (`2bf9c53`) | spec 017 | Hecho |
| 19 | Pruebas en vivo de la 017: calibración con ventana, deslizamiento simulado, tapar o desconectar la cámara, apagar la luz, cortar la red del nodo y recepción de los avisos | T-017-13 | Propietario |
| 22 | Instalar JDK 21, Node LTS y `firebase-tools` para los emuladores de Firebase: **autorizado con `winget` el 2026-10-28 (D-099)** | T-019-03 | Equipo |
| 23 | ~~Confirmar las diferencias 4 y 5 del plan 019~~ Se porta la privacidad de la 014 (D-098, T-019-16); las demás diferencias, con su valor por defecto | P-019-02 | Hecho (decisión) |
| 24 | Crear el proyecto Firebase real (Spark), el servicio en Render y la tarea en cron-job.org, confirmando sus condiciones gratuitas. **Pendiente por decisión del propietario (D-100)**; el punto de control del 2026-11-04 necesita al menos el proyecto Firebase | P-019-03, T-019-07 | Propietario |
| 25 | Punto de control de la 019 el 2026-11-04: nodo real → caída → push en Android. Si falla, decidir si se entrega con Django | D-081 | Propietario + equipo |

Los números 20 y 21 los usa la rama de la 018, sin fusionar.

Trabajo futuro registrado (no comprometido): invitación por correo (D-050), traspaso de titularidad, papelera de pacientes con «deshacer» (D-067), cifrado en reposo y PostgreSQL (014), registro de lecturas, push inmediato de inmovilidad (D-051). iOS pasó al alcance el 2026-10-26 (D-068, spec 015).

## Estado vigente — spec 019 migración a FastAPI + Firebase, 2026-10-28

- **Pedido.** Revisar el proyecto `vigia 26` de otro integrante (FastAPI + Firebase, hecho sin specs) para traer su frontend móvil. Después, el propietario decidió migrar el producto a FastAPI + Firebase antes de la entrega y autorizó: «concuerdo con tus decisiones, dejamos develop con django y probamos los cambios en una nueva rama, autorizo que cambies codigo pero antes registra todo».
- **Hecho.** Rama `feature/019-migracion-firebase` desde `origin/develop` (`73fb6a1`); [spec](../specs/019-migracion-firebase/spec.md), [plan](../specs/019-migracion-firebase/plan.md) y [tareas](../specs/019-migracion-firebase/tasks.md); decisiones D-081..D-097.
- **Hallazgos.** El backend base ya cubre pacientes, permisos, invitaciones, medicamentos, tareas, agenda, historial y planes; le faltan Edge, alertas, push, recordatorios y consentimiento. Su portal React es solo un esqueleto. Con un nodo renovando cada 10 s, Firestore gratis se agotaría sin caché (D-095).
- **Siguiente.** Cerrar T-019-01 (AGENTS y CLAUDE) y seguir con T-019-02 (importación). Bloqueos en los pendientes 22–24.
- **No hecho.** Sin código, merge, despliegue ni cuentas.

## Estado anterior — spec 017 implementada, 2026-10-27

- **Pedido.** Revisar el prototipo `pose_app` (detector de caídas de la cama en Kotlin), redactar la spec 017 con lo que conviene traer a VIGIA y, tras las decisiones D-073..D-077, «Autorizo T-017-01 a T-017-12, sin merge, migración real ni despliegue».
- **Hecho** en `feature/017-robustez-caidas` ([spec 017](../specs/017-robustez-caidas/spec.md), [tareas](../specs/017-robustez-caidas/tasks.md)):
  - Edge: zona de cama calibrada en local y regla «acostado fuera de la cama» (`fall-bed-v1`) con seguimiento contra sábanas, puntos de respaldo y un aviso por evento junto a la regla de impacto; estado de monitoreo (persona no visible, sin imagen, poca luz) informado en la renovación; el nodo ya no termina si la cámara deja de entregar cuadros.
  - Backend: estado del nodo con migración aditiva `0010`; avisos de cámara ciega y de nodo sin señal (60 s) por `send_mobile_reminders`, una vez por episodio.
  - App: estado en la tarjeta del nodo (titular) y línea «Cámara: …» de solo lectura para los tres roles.
  - Documentación: guía de instalación, casos difíciles y protocolo ampliado a 25 caídas y 60 actividades normales en [edge/README.md](../edge/README.md).
- **Evidencia (Windows, sintética).** Django **246**, Edge **56** y Flutter **51** OK; check y `makemigrations --check` sin cambios; `0010` probada en avance y reversión; 12 mutaciones detectadas. Brillo + regla de cama ≈ 0,5 ms por cuadro con video sin personas. Detalle en [validation.md](../specs/017-robustez-caidas/validation.md).
- **No hecho.** Sin cámara real, `edge.run` en vivo, calibración con ventana ni Firebase real (T-017-13). Sin merge, migración real ni despliegue.
- **Fusión.** [PR #12](https://github.com/Azurtilo/vigia-demo/pull/12) fusionada en `develop` el 2026-10-27 (`2bf9c53`), con autorización del usuario («haz merge»). Incluye T-017-14/15 (contrato de estados nodo ↔ servidor y avisos de nodo una vez por ejecución). Sin migración real ni despliegue.
- **Después.** T-017-16 en `feature/017-config-caidas`: `edge/fall.py` usa `edge/options.py` como la cama y el monitoreo, sin cambiar su comportamiento.
- **Siguiente paso seguro.** T-017-13 junto con el protocolo ampliado (pendiente 4).

## Antecedente — spec 016 en implementación, 2026-10-26

- **Pedido.** Revisión de calidad general ([QA_2026-10-26.md](QA_2026-10-26.md), [PR #10](https://github.com/Azurtilo/vigia-demo/pull/10)) y corrección de los hallazgos 01–04, 06 y 08.
- **Hecho** en `feature/016-correcciones-qa` ([spec 016](../specs/016-correcciones-qa/spec.md)):
  - Pillow 13.0.0 y certifi 2026.10.23; herramientas de desarrollo en `requirements-dev.txt`; `pip-audit` sin vulnerabilidades;
  - comando de pruebas con `PrivacidadApp` en todos los documentos vigentes;
  - CI en `.github/workflows/ci.yml`;
  - guía [OPERACION.md](OPERACION.md) para programar la purga y los avisos.
- **Hallado de paso.** `VIGIA_PUSH_ENABLED` no está definido en la configuración ni se lee del entorno: en producción los avisos no pueden activarse sin decidir cómo se configura.
- **CI.** Verde en la [PR #11](https://github.com/Azurtilo/vigia-demo/pull/11): Django 235, Edge 22, Flutter 46, `pip-audit` sin vulnerabilidades.
- **PR.** [PR #10](https://github.com/Azurtilo/vigia-demo/pull/10) y [PR #11](https://github.com/Azurtilo/vigia-demo/pull/11) fusionadas en `develop` el 2026-10-26 por pedido del propietario («fusiona 10 y 11 y registra los demas en pendientes»).
- **Siguiente paso seguro.** Pendientes 14 y 15 (servidor y activación del push) y 16 (hallazgos menores de la QA). Pendiente del propietario: programar las tareas en el servidor (OPERACION.md) y decidir la activación del push.

## Antecedente — spec 015 fusionada, 2026-10-26

- **Pedido.** Comparar este repositorio con [Sndrpaola/vigia-unificado](https://github.com/Sndrpaola/vigia-unificado) y «prepara la spec con la lista, ademas quiero incluir iOS al alcance».
- **Hecho.** [Spec](../specs/015-integracion-unificado/spec.md), [plan](../specs/015-integracion-unificado/plan.md) y [tareas](../specs/015-integracion-unificado/tasks.md) de la 015, con la lista de lo que se trae (A1–A11), lo que no (B1–B10) y la resolución de los archivos modificados en ambas copias. D-068 (iOS en el alcance) sustituye D-011-02; AGENTS.md y CLAUDE.md actualizados. Rama `docs/015-integracion-unificado`, sin código.
- **Revisión del propietario.** Se trae toda la lista A y nada de la B. P-015-01 = Apple ID gratuito, sin push en iPhone (D-069); P-015-03 = adoptar el rediseño (D-070); P-015-04 = `develop` único (D-071).
- **Implementación.** P-015-02: Sandra compila iOS (D-072). Autorizadas T-015-01..07. En `feature/015-integracion-unificado`: catálogo de planes en la API, panel de plan, rediseño de la app con roles (013) y privacidad (014), descarga estable del APK (`mobile/tool/build_android.sh`) y marca VIGIA en el portal. Django 235, Edge 22 y Flutter 43 OK.
- **Android físico (T-015-07).** Recorrido completo en el ELI NX9: login, HU-03, HU-04, aviso con pantalla bloqueada, panel de plan, cierre de sesión, rol cuidador y puerta de privacidad, todo OK ([validation.md](../specs/015-integracion-unificado/validation.md)). Los dos hallazgos de interfaz («Registrar medicamento» cortaba la palabra y al cambiar de pestaña se conservaba la posición de desplazamiento) se corrigieron en T-015-14 y se repitieron en el teléfono. La revisión de la PR corrigió además el enlace de cambio de plan con subruta. Flutter 46 OK.
- **No comprobado.** iOS. La marca se revisó en navegador (claro y oscuro) el 2026-10-26.
- **PR.** [PR #8](https://github.com/Azurtilo/vigia-demo/pull/8) revisada y fusionada en `develop` el 2026-10-26 (`8d2be54`).
- **Cierre de etapa.** Guía [INSTALACION_CELULAR.md](INSTALACION_CELULAR.md) y documentación de alcance iOS (T-015-12); remoto `unificado` quitado (T-015-13 parcial).
- **Siguiente paso seguro.** iOS (T-015-08..11) con Sandra en macOS, con autorización aparte; después, completar T-015-13.

## Antecedente — PR #5 y #6 fusionadas, 2026-10-25

- **Pedido.** «fusiona todo».
- **Hecho.** [PR #5](https://github.com/Azurtilo/vigia-demo/pull/5) (detalles de interfaz, `f71d1be`) y [PR #6](https://github.com/Azurtilo/vigia-demo/pull/6) (skill `validar-produccion-sdd` versionada, `1f620a6`) fusionadas en `develop`. Pendientes 1, 10 y 11 cerrados.
- **Siguiente paso seguro.** Pendientes abiertos de la tabla: servidor por la red local y T-011-05 completo (fila 2), Firebase (3), protocolo de caídas (4), revisión legal (5), sesiones D-056 (6), QA (7), migración real (8) e informe de disponibilidad (9).

## Antecedente — PR #4 fusionada y detalles de interfaz, 2026-10-25

- **Pedido.** «acepta el merge y arregla los detalles de interfaz».
- **Hecho.** PR #4 fusionada en `develop` (merge commit `0da7eda`). Rama `feature/011-detalles-interfaz` desde `develop` con T-011-12/13/14 y T-014-12 ([tareas 011](../specs/011-ecosistema-instalable/tasks.md), [tareas 014](../specs/014-privacidad/tasks.md)).
- **Evidencia.** `flutter analyze` sin problemas; Flutter **39 OK** (7 nuevas en `interface_details_test.dart`, todas fallaban antes); cada detalle repetido en el ELI NX9.
- **Datos demo.** `demo_premium` tiene además «Prueba Premium».
- **Siguiente paso seguro.** PR de `feature/011-detalles-interfaz` hacia `develop` (fila 11).

## Antecedente — prueba en Android físico y dos correcciones, 2026-10-25

- **Pedido.** «prueba la app, inicia la app en el telefono conectado»; luego «sigue probando flujos […] ve actualizando la lista de pendientes» y «corrige fallos 1 y 2».
- **Hecho.** App debug en ELI NX9 (Android 16) con el servidor demo por USB (`adb reverse`). Comprobados login, HU-03, HU-04, avisos locales con pantalla bloqueada (T-011-03 cerrada), cierre de sesión, cupo Plus, flujo titular/cuidador de la 013 y política y consentimiento de la 014. Detalle en las validaciones de [011](../specs/011-ecosistema-instalable/validation.md#android-físico--2026-10-25), [013](../specs/013-cuidado-delegado/validation.md#límites-y-fallos) y [014](../specs/014-privacidad/validation.md#android-físico).
- **Corregido (autorizado).** T-013-13: «Unirme con un código» caía en pantalla roja. T-014-11: con la política pendiente, el login no mostraba el botón al portal y el reintento daba 409. Cinco pruebas nuevas; Flutter analyze sin problemas y **32 OK**; ambos flujos repetidos en el teléfono.
- **Datos demo.** `demo_plus` tiene «Prueba Uno» y «Prueba Dos»; `demo_plus` y `demo_free` aceptaron la política; `demo_free` es cuidador de Rosa Demo; el reloj de Rosa Demo quedó vencido.
- **No hecho.** Servidor por la red local, cámara MediaPipe en Premium, detalles de interfaz (fila 11), push.

## Antecedente — 014 privacidad implementada, 2026-10-25

- **Pedido.** «respecto a p14 me parece todo bien, registralo […] autorizo implementar». También preguntó si conviene conservar por un tiempo los datos de un paciente eliminado: se recomendó no hacerlo y usar archivar como vía reversible (D-067).
- **Hecho.** Rama `feature/014-privacidad`, commits 0870edb, 58de2f3 y 444d0c3. App `PrivacidadApp` con:
  - política versionada y puerta de aceptación (en la API, 403 `consent_required`);
  - consentimiento por paciente, con alcances cuidado y detección, que bloquea registros y la cámara;
  - exportación JSON de cuenta y de paciente;
  - eliminación de paciente y de cuenta con anonimización;
  - comando `purge_expired_data` con los plazos de D-064.

  La app móvil muestra el aviso y pide el consentimiento al crear un paciente. La demo quedó migrada y con consentimientos ficticios.
- **Evidencia (Windows).** Django **218 OK** (16 nuevas), Edge **22 OK**, Flutter **26 OK** (4 nuevas); migración probada en avance y reversión. [Validación](../specs/014-privacidad/validation.md).
- **Desviación.** `core.test_settings` desactiva las reglas para las suites anteriores; las pruebas de privacidad las activan.
- **Revisión en navegador (mismo día).** El propietario revisó la 014 en la demo: «lo demás que vi estaba bien». Hubo dos correcciones: aviso junto a los campos del representante, y autoría en el panel «Mis cuidados» («Hecho por …», «registrada por …», «Cuenta eliminada»; RF-013-15). Django **219 OK**.
- **No hecho.** Android físico, revisión legal de la política, merge.
- **Fusión (mismo día).** PR #3 fusionada en `develop` y traída a esta rama. Conflicto solo en este archivo. Django **227 OK**, Edge **22 OK**, Flutter **27 OK**.
- **Siguiente paso seguro.** Revisión de la PR de la 014; prueba en Android físico de 013/014.

## Spec 014 privacidad — DOCUMENTAR, 2026-10-25

- **Pedido.** «sigue con la spec 14».
- **Contexto.** [PR #2](https://github.com/Azurtilo/vigia-demo/pull/2) (013) fusionada en `develop`. [PR #3](https://github.com/Azurtilo/vigia-demo/pull/3) (ajustes de la 012) abierta.
- **Hecho.** Rama `feature/014-privacidad` desde `develop` con:
  - [spec](../specs/014-privacidad/spec.md) (14 RF);
  - [plan](../specs/014-privacidad/plan.md), con app nueva `PrivacidadApp`, puerta de consentimiento, consentimiento por paciente y alcance, exportación JSON, eliminación ordenada con anonimización y comando de purga;
  - [tareas](../specs/014-privacidad/tasks.md) T-014-01..10, pendientes.
- **Propuestas para el propietario:**
  - P-014-01: plazos de conservación;
  - P-014-02: al eliminar la cuenta del titular se eliminan sus pacientes;
  - P-014-03: pacientes existentes sin consentimiento quedan con registros bloqueados;
  - P-014-04: texto de la política como borrador pendiente de revisión legal.
- **No hecho.** Sin código. Implementación no autorizada.
- **Siguiente paso seguro.** Respuestas a P-014-01..04 e instrucción de implementación.

## Antecedente — paso 3, ajustes de la 012 (PR #3 fusionada), 2026-10-25

- **Pedido.** «levanta pull request hacia develop y avanza en el paso 3».
- **Hecho.** [PR #2](https://github.com/Azurtilo/vigia-demo/pull/2) de `feature/013-cuidado-delegado` hacia `develop`. Rama `feature/012-push-inmediato-qa` creada desde la 013. Spec 012 con RF-012-07 precisado y RF-012-13..16; plan con envío común, reserva de recibos y push inmediato; tareas T-012-13..21.
- **Implementado (mismo día, autorizado: «autorizo implementacion de T-012-13 a T-012-21», push inmediato solo para caídas).** Commits e1f25c4, da04a1d, 84daf76:
  - `push.py`: reserva de recibo, FCM fuera de transacción y confirmación (QA-09; migración aditiva 0009);
  - push de caída tras `on_commit` en un hilo (D-051); la inmovilidad sigue por el comando;
  - texto genérico con visibilidad privada (D-058), enviado a los destinatarios de la 013;
  - `minSdk` 26 con APK compilado;
  - «Posible caída» en la app (QA-16);
  - demo con clave propia y solo IP privadas (QA-10);
  - listado de usuarios sin N+1 (QA-19);
  - artefacto Android eliminado (QA-21).
- **Evidencia.** Django **210 OK**, Edge **22 OK**, Flutter **23 OK**; [validación 012](../specs/012-deteccion-caidas/validation.md).
- **No hecho.** Firebase real, medición de ≤ 10 s, merge.
- **Siguiente paso seguro.** PR de `feature/012-push-inmediato-qa` hacia `develop` después de la PR #2 (comparte su historia). Luego spec 014 de privacidad (D-052).

## Estado vigente — 013 cuidado delegado implementada, 2026-10-25

- **Pedido.** «haz commit y pasa a implementarla en feature/013-cuidado-delegado».
- **Hecho.** Rama `feature/013-cuidado-delegado` (desde `docs/decisiones-2026-10-25`), un commit por bloque de tareas (3a6e60d..4f39c68):
  - vínculos e invitaciones (migración aditiva 0008);
  - `access.py` con la matriz por rol; servicios que bloquean al titular y usan su cupo y su plan;
  - web y API por rol, con gestión de accesos y «Unirme con un código»;
  - push de cuidado a titular y cuidador, y de riesgo a todos los roles (D-063);
  - app Flutter adaptada al rol.
- **Evidencia (Windows).** Django **202 OK** (21 nuevas), check y makemigrations sin cambios, migración 0008 probada en avance y reversión. Edge **22 OK**. Flutter analyze sin problemas, **22 OK** (3 nuevas). [Validación](../specs/013-cuidado-delegado/validation.md).
- **Revisión en navegador (mismo día).** El propietario revisó la web con el servidor demo y cuentas ficticias de los tres roles: «se ve todo bien». A pedido suyo, los mensajes emergentes ahora se cierran solos (6/10/12 s según tipo). Servidor detenido.
- **No hecho.** Ensayo en Android físico con dos cuentas, Firebase real, merge, despliegue y migración de una base real.
- **Pendiente de la 013: prueba en Android físico.** Requiere un servidor alcanzable desde la red local (T-011-09) y dos cuentas ficticias. Pasos:
  1. El titular crea un código desde la app.
  2. El cuidador lo ingresa en «Unirme con un código» y confirma.
  3. El cuidador registra un medicamento y una postura.
  4. El titular ve esos registros con el nombre del cuidador.
  5. El titular revoca el acceso y el cuidador deja de ver la ficha.

  El resultado se anota en [validation.md](../specs/013-cuidado-delegado/validation.md).
- **Orden siguiente (plan del 2026-10-25):**
  1. Prueba de la 013 en Android físico.
  2. PR de `docs/decisiones-2026-10-25` y `feature/013-cuidado-delegado` hacia `develop`.
  3. Tareas fechadas de la 012: push de caída inmediato (D-051) con destinatarios de la 013 (D-063), texto genérico del push (D-058), `minSdk` 26 (D-057) y hallazgos QA técnicos (QA-09, 10, 16, 19, 21).
  4. Spec 014 de privacidad (D-052).
  5. En paralelo, por parte del propietario: Firebase de prueba (D-054) y protocolo de caídas con voluntarios (D-053).
- **Siguiente paso seguro (detalle).** Ensayo en dispositivo; luego PR de `docs/decisiones-2026-10-25` y `feature/013-cuidado-delegado` hacia `develop`.

## Antecedente — spec 013 DOCUMENTAR, 2026-10-25

- **Pedido.** Documentar la spec de familiar/cuidador decidida en D-050.
- **Hecho.** [Spec](../specs/013-cuidado-delegado/spec.md) con 14 RF y matriz por rol (titular, familiar invitado, cuidador, sin vínculo); [plan](../specs/013-cuidado-delegado/plan.md) con `access.py`, bloqueo por titular, invitaciones con hash y límite de intentos, tres modelos nuevos (migración aditiva 0008) y endpoints aditivos; [tareas](../specs/013-cuidado-delegado/tasks.md) T-013-01..11, todas pendientes. Índice y trazabilidad prevista actualizados.
- **Decisiones del propietario (mismo día):** D-061 familiar invitado igual al titular salvo archivar, cupo, nodos y accesos; D-062 el cuidador ve solo la agenda del día y la última postura; D-063 el push de riesgo también llega al cuidador. Spec, plan y tareas ajustados; sin decisiones pendientes.
- **No hecho.** Sin código. Implementación no autorizada.
- **Siguiente paso seguro.** Revisión de la 013 y, si corresponde, instrucción de implementación en la rama `feature/013-cuidado-delegado`.

## Decisiones del propietario — 2026-10-25

- **Pedido.** Registrar las respuestas al documento de pendientes del 23-10-2026 y las respuestas de la sesión.
- **Hecho.** D-050 a D-060 en [DECISIONES.md](DECISIONES.md): familiar/cuidador con invitación por código (P-010-02), push de caída inmediato (P-012-01), spec de privacidad (QA-05), protocolo de caídas propio (P-012-02), Firebase de prueba (P-010-05), funciones por plan con nodos 0/0/1 (P-010-06), autenticación vigente con vencimiento y revocación (P-010-04), Edge como vía principal y Android API 26 (P-010-01/03), texto genérico del push (QA-14), política de Git (AGENTS.md) y disponibilidad declarada como no medida. Specs [010](../specs/010-aplicacion-movil/spec.md) y [012](../specs/012-deteccion-caidas/spec.md) marcan sus pendientes como resueltos.
- **Actualización de reglas y documentación (mismo día).** AGENTS.md describe VIGIA (tres componentes, apps reales, comandos Windows por componente). Prompts 01/03/04/05/07 revisados: 04 y 07 ya no prohíben commits que D-059 permite; el comando Edge incluye `test_fall` y `test_run`; 05 remite a la matriz y a D-060. Nuevo [prompts/08-revision-qa.md](../prompts/08-revision-qa.md). Corregidos también CLAUDE.md y `.claude/agents/qa-vigia.md` (comando Edge incompleto), [PROYECTO.md](PROYECTO.md) (nombre VIGIA y estado 010–012), [specs/README.md](../specs/README.md), [ENTORNO_Y_VERIFICACION.md](ENTORNO_Y_VERIFICACION.md) y la [matriz HU/RT/RNF](TRAZABILIDAD.md#matriz-hurtrnf-vigente) en TRAZABILIDAD.
- **Inconsistencia detectada, sin corregir (es código).** `mobile/android/app/build.gradle.kts` fija `minSdk = maxOf(24, …)`, pero D-057 decide API 26. Requiere una tarea.
- **No hecho.** Sin código, specs nuevas ni tareas. Ninguna decisión autoriza implementación.
- **Siguiente paso seguro.** DOCUMENTAR la spec 013 (familiar/cuidador) y la de privacidad, y las tareas fechadas de la 012 (D-051, D-058, minSdk 26 y QA técnicos).

## Antecedente — 012 detección de caídas (RT-03), 2026-10-22

- **Pedido.** Crear e implementar en la misma sesión la [spec 012](../specs/012-deteccion-caidas/spec.md): regla de caída en Edge, riesgo `fall` en el backend con aviso push, métricas KPI, `edge/bench.py`, pruebas sintéticas y protocolo de 20 caídas.
- **Hecho.** `edge/fall.py` (velocidad de descenso de la cadera, descenso, ángulo del tronco, relación de aspecto y confirmación en el suelo; umbrales por `--fall-*` o JSON), `edge/metrics.py`, `edge/bench.py`, integración en `edge/run.py` con logging y reintento. Backend: `risk="fall"` (migración aditiva 0007 solo de `choices`), log de recepción, `received_at` en el historial y aviso «Posible caída» con prioridad alta en `send_mobile_reminders`. App: texto de caída en el historial. Protocolo en [edge/README.md](../edge/README.md#protocolo-de-prueba-de-caídas-simuladas).
- **Evidencia (Windows).** Django **178 OK**, check y makemigrations --check sin cambios. Edge **16 OK** (sintéticos) y `edge.smoke` OK con el nuevo `.venv-edge-win`. Bench ejecutado solo con video sintético sin personas. Flutter analyze sin problemas, **19 OK**. Detalle en [validation 012](../specs/012-deteccion-caidas/validation.md).
- **Correcciones QA (2026-10-22, posterior).** [QA_2026-10-22](QA_2026-10-22.md) QA-01/02/03 corregidos: envío del nodo en hilo aparte con cola, backoff y entrega al reconectar; riesgos aceptados hasta 1 h; avisos push por `received_at` sin ventana de 2 min y con reintento; `edge/run.py` en `Uplink`/`Monitor` con `edge/test_run.py`. Django **181 OK**, Edge **22 OK**, Flutter **19 OK**. Rama `feature/deteccion-caidas` (D-012-02).
- **No hecho.** Sin ejecución en vivo de `edge.run` ni protocolo de 20 caídas: sensibilidad, falsos positivos y latencias **no medidos**. Sin Firebase real, DB real, migración real, deploy ni commit.
- **Siguiente paso seguro.** Protocolo de 20 caídas con video autorizado y decisión P-012-01 (frecuencia de avisos). Siguen vigentes los pendientes de 011 (APK en Android real).

## Antecedente — 011 reloj vacío y avisos locales, 2026-10-22

- **Pedido.** Priorizar T-011-01/02 (reloj sin eventos) y T-011-03/04 (avisos locales Android) con regresiones, APK debug nuevo y commits por tarea. T-011-06 (estilo web) y T-011-10 (iOS) quedan para después.
- **Hecho.** El estado vacío del reloj seguía fallando en web/API: se ofrecían pausar/reanudar/cambiar intervalo sin reloj y se respondía 404. Se reprodujo con tests y se corrigió en servicio, formulario, panel web y `ClockPanel` (commit `08e33f4`). Los avisos locales ya cumplían cancelación y reemplazo; se añadieron regresiones al pausar, registrar postura, archivar y cerrar sesión (commit `51d9728`). Detalle y mutaciones en [validation 011](../specs/011-ecosistema-instalable/validation.md).
- **Evidencia (Windows).** Django **176 OK**, check y makemigrations --check sin cambios. Flutter analyze sin problemas, **19 tests OK**. APK debug: ver validación.
- **No hecho.** Prueba en un Android físico (notificación con pantalla bloqueada, permisos, reinicio). Sin DB real, migraciones reales, deploy ni push.
- **Siguiente paso seguro.** T-011-09/11: instalar el APK en un Android real con servidor LAN y repetir los flujos del reloj y los avisos.

## Antecedente — reconciliación 011 en Windows, 2026-10-22

- **Pedido.** CLAUDE.md, ejecución de suites y reconciliación de estado; sin cambios de código. Nuevo [CLAUDE.md](../CLAUDE.md): remite a AGENTS.md y resume los requisitos del informe (HU-01..07, RT-01..03, RNF). El propietario fija **Windows, Android primero e iOS fuera de alcance**, registrado en [D-011-02](DECISIONES.md), la spec 011 y el índice de specs.
- **Hecho según el código.** Separación física `web/` (todas las apps Django; `manage.py` raíz delega), `mobile/` y `edge/`. Flutter modularizado en `mobile/lib/{app,core,features/*,notifications,shared}`. El reloj ya admite inicio sin evento, pausa/reanudación e intervalos 60/90/120 en servicio, API y UI. Hay avisos locales (`flutter_local_notifications`) y migración 0006 de coordinación con push (aplicada solo en la demo). Los tokens web usan la paleta índigo. Detalle en [tasks 011](../specs/011-ecosistema-instalable/tasks.md#reconciliación-con-el-código--2026-10-22): T01/02/07/08 hechas; T03/04/06/09 parciales; T05/11 pendientes; T10 fuera de alcance.
- **Evidencia (Windows).** `.venv` nuevo con lock `--require-hashes`. Django: check y makemigrations --check sin cambios, **173 tests OK**. Edge: **5 tests OK** (sintéticos); smoke sin modelo `.task`. Flutter: al principio no ejecutaba (SDK 3.47.1 frente a pubspec ^3.13.5). Con autorización se fijó el SDK en 3.47.7 / Dart 3.13.5, sin cambiar pubspec: pub get OK, **analyze sin problemas, 13 tests OK** y sin correcciones de código. Los venv `.venv-edge`/`.venv-mobile` del repo son de macOS. El de Edge se creó solo en un temporal fuera del repo.
- **Requisitos del informe sin implementar.** RT-03 caídas (Edge y README declaran «No detecta caídas»). Separación familiar/cuidador y cuidado delegado (P-010-02 abierta: hoy una cuenta propietaria opera sus pacientes). Push real no configurado (Firebase). RNF de latencia, disponibilidad y precisión sin medir.
- **No hecho.** Sin DB real, migraciones reales, dependencias del proyecto modificadas, deploy, commit ni push.
- **Siguiente paso seguro.** Probar el APK en un Android real con un servidor alcanzable (T-011-09). Después, specs nuevas para RT-03 (caídas) y la decisión P-010-02 (familiar/cuidador).

## Pedido más reciente — corregir flechas de selectores

- «corriges eso porfa», captura de postura: T-009-15 RF-009-11/12 completa. Reproducido SVG 240×240 fuera del campo, corregido con override crispy local/CSS semántico a 20×20 dentro del selector y color del tema. Función nativa/attrs/opciones/múltiples conservados; caché del CSS renovada.
- Navegador 390/1440 claro/oscuro sin overflow; teclado/obligatorio/POST de postura e intervalo comprobados. Contratos de render correctos, Tailwind 86 ms/check/diff OK. Suite final **158 OK, 15,142 s**. Primera suite detectó intermitencia de carrera SQLite (cero altas por bloqueo); aislado 1 OK y repetición total correcta, sin tocar backend. Estabilizar ese ensayo en seguimiento propio; [validación y evidencia](../specs/009-cuidados-cuidadores/validation.md).
- Sin DB real, migración/dependencias/deploy/commit/push. Preview detenido/pestaña cerrada/viewport restaurado y temporales retirados. Siguiente: revisión visual del propietario; pendientes anteriores de 009/007 conservados. No repetir implementación de imágenes ni entrevista de requisitos.

## Pedido más reciente — mejorar imágenes de guías 009

- Pedido directo «puedes mejorar las imágenes», ajuste visual RF-009-05/11: T-009-14 completa. Cuatro PNG originales más detallados y coherentes con la base, integrados por CareGuide.illustration/componente compartido, alt actualizado y caché versionada. Laterales revisados/asignados según lado anatómico; SVG/rutas de datos/textos clínicos e imágenes personalizadas preservados. Sin nueva spec ni entrevista.
- Estado anterior decía cuatro SVG: corresponde a la entrega inicial, ahora la presentación usa PNG v2 para esas cuatro guías. Evidencia anterior conservada. **31 tests CuidadosApp OK, 0,915 s** tras ajuste final, Ruff/check/esquema correctos. 390/1440 claro/oscuro: cuatro imágenes cargadas, sin overflow; [validación](../specs/009-cuidados-cuidadores/validation.md), [mediciones](../specs/009-cuidados-cuidadores/evidencia/imagenes-v2-navegador.json), [prompts](../specs/009-cuidados-cuidadores/evidencia/prompts-imagenes-v2.json).
- Sin migración real/deploy/commit/push. Preview en memoria detenido, pestaña cerrada, viewport restaurado y temporales retirados. Siguiente: revisión visual del propietario; pendientes manuales/operativos anteriores de 009/007 conservados. No queda implementación pendiente de este ajuste.

## Pedido actual — IMPLEMENTAR 009 / CuidadosApp, entrega técnica

- Autorización posterior explícita: «te doy permiso de implementar specs 009 alcanse completo», vigente tras RETOMAR. DOCUMENTAR se entregó primero; plan/tareas con estado previo se reconciliaron con archivos reales. No repetir entrevista/reconstrucción ni pedir autorización de código otra vez.
- CuidadosApp implementada: pacientes propios para todos los cargos/root, medicamentos/horarios/tareas, cuatro guías SVG, postura con 60/90/120, agenda/eventos/correcciones, reloj persistente/pausa y avisos con web abierta. Catálogo Free $0/1, Plus $4.990/3, Premium $9.990/ilimitados; IA/cámaras futuras. Reducción/fin de cancelación con elección y archivo conservando historial.
- **158 tests OK, 14,126 s** (31 nuevos de cuidados), core.test_settings y SQLite efímero; check sin problemas/esquema sin cambios, 89 HTML y JS/Ruff correctos, Tailwind standalone 4.3.0 (79 ms). Carrera de dos transacciones observa un solo cupo y crea un paciente; otro escritor recibe error recuperable. Cuatro SIM117 de tests antiguos reproducidos en HEAD y no limpiados fuera del alcance.
- Ensayo de migraciones/reversión/reaplicación conserva catálogo previo personalizado y snapshots/importes/fechas comerciales. Nuevos archivos PlanesApp 0003/0004 y CuidadosApp 0001/0002/0003 **no aplicados a DB existente**. Sin .env/DB/media personal/dependencias nuevas, deploy/commit/push.
- Navegador: diez mediciones responsive claro/oscuro 360–1440 sin overflow, 13 JPEG; alta/cupo/horarios/omisión/postura/pausa, preaviso/vencido/recarga/dos pestañas, dos cuidadores/404, Inicio interno y panel propio vacío, cancelación/selección/Free inmediato, guías, teclado Tab, corrección/archivo/reactivación y fallback cero scripts. Reloj de postura queda pausado al reactivar; programación diaria retoma desde ese momento, sin atrasos inventados. Fixtures de medianoche corregidas a Santiago.
- [Validación completa y límites](../specs/009-cuidados-cuidadores/validation.md), [spec](../specs/009-cuidados-cuidadores/spec.md), [plan](../specs/009-cuidados-cuidadores/plan.md), [tareas](../specs/009-cuidados-cuidadores/tasks.md), [guía de desarrollo](CUIDADOSAPP_DESARROLLO.md). T-009-01–11 completas; T-009-12 parcial por zoom/movimiento reducido/offline/suspensión nativos; T-009-13 documentación entregada, aceptación del propietario pendiente. Backend con bloqueo de filas debe verificarse al elegir entorno productivo.
- Preview efímero detenido, pestañas temporales cerradas, viewport restaurado y .work-009 retirado tras conservar evidencia. Git con cambios locales de alcance, sin commit/push. Siguiente: revisión manual/aceptación y operación de migración en DB existente con entorno/respaldo/autorización propios; Google real conserva pendiente 007. Ningún trabajo de negocio autorizado queda por implementar. Próxima spec sugerida 010, comprobar antes de crear.

## Antecedente documental — DOCUMENTAR 009 / CuidadosApp

- Pedido humano amplía la demo a cuidadores: pacientes propios, medicamentos, posturas/cuidados con guías e imágenes, registro manual, reloj y avisos. Documento adjunto e imagen tratados como contexto; precios ficticios, dos planes y cambio al próximo período del documento no sustituyen las instrucciones humanas ni las reglas 007.
- Siguiente libre 009 y ausencia de colisión CuidadosApp comprobados. Entregados en orden [spec](../specs/009-cuidados-cuidadores/spec.md), [plan](../specs/009-cuidados-cuidadores/plan.md) y [tareas](../specs/009-cuidados-cuidadores/tasks.md): doce RF y trece tareas pendientes. Una app propuesta CuidadosApp, nombre delegado con mayúscula inicial/sufijo App.
- P-009-01/02/03 confirmadas expresamente: Free $0/1, Plus $4.990/3 y Premium $9.990/ilimitados; avisos solo con web abierta; selección del cuidador de pacientes que permanecerán activos al bajar de plan. Archivo conserva datos/historial. IA/cámaras futuras. Todos los cargos, incluido root, ven solamente pacientes propios.
- Plan integrado con código actual: cuotas/transacciones compartiendo bloqueo de User con pagos; reducción inmediata condicionada al resultado aprobado y selección; cancelación a término con selección futura; consulta de elegibilidad sin escrituras GET. Transición Pro→Premium/Hogar histórico, horarios diarios y resolución de vencimiento sin selección son propuestas técnicas revisables, no respuestas atribuidas al propietario.
- Solo Markdown; sin creación de app/código/assets/tests ejecutables/migraciones/dependencias. No suite/build, lectura de .env/DB/media personal, commit/push ni despliegue. Los 127 tests de 008 no validan cuidado de pacientes.
- Verificación documental: diez documentos y 185 enlaces locales válidos; SHA-256 de 362 archivos no Markdown conservados sin cambios/adiciones/eliminaciones. git diff --check sin errores, con avisos LF/CRLF. Estado Git de cierre contiene solo siete Markdown modificados y la carpeta documental 009 nueva; ninguna aceptación funcional asumida.
- Siguiente: revisión documental e instrucción posterior explícita para implementar 009 según AGENTS.md. Las autorizaciones anteriores de 007/008 siguen vigentes para esos alcances. No quedan preguntas críticas pendientes; próxima spec sugerida 010, comprobar.

## Entrega anterior — implementación 008 / Dashboard y navegación

- Instrucción posterior explícita: «implementa specs 8 Dashboard de suscripciones y navegación coherente alcance completo». Tareas técnicas 01–07 terminadas; aceptación del propietario pendiente. No repetir autorización de código.
- Entregados seis SVG, Inicio por permisos internos, selector visual compartido y dashboard de solo lectura con estados/distribución/volumen mensual simulado, conservando accesos y reglas 007. Sidebar desplazable; menú móvil nativo como fallback noscript. Sin nueva app/modelos/migraciones/dependencias.
- **127 tests OK (12,153 s)**; 15 Home tras último ajuste, check/esquema/Ruff/JS/77 HTML correctos y Tailwind 4.3.0 compilado. Diez casos nuevos: matriz, cálculo/fechas/cancelación/población/snapshots, cuatro consultas sin crecimiento por usuario y escape de JSON. [Validación y resultados](../specs/008-dashboard-navegacion/validation.md).
- Navegador: cinco anchos 360–1440 px y dos modos sin desbordamiento; ADMIN/MANAGER, cliente sin Inicio, SVG/selector, menú/Escape/foco, fallback sin CDN/recursos JS y vacío. 18 JPEG verificados. Fallback servido sin scripts/noscript activo en preview aislado; no configuración global del navegador. Zoom 200% y preferencia reducida nativos siguen manuales.
- Preview en memoria detenido, pestaña temporal cerrada, viewport restaurado y .work-008 retirado. Hashes preservan dependencias/autenticación/servicios 007; cambios anteriores fuera de once archivos del alcance intactos. No DB real, .env/media personal, commit/push ni despliegue.
- Documentación final: 237 enlaces locales de trece documentos válidos y diff --check sin errores; avisos de conversión LF/CRLF sin alterar significado. Evidencia estructurada en la spec.
- Siguiente: revisión visual del propietario y comprobaciones manuales indicadas. Pendientes operativos de 007 conservados. Próxima spec sugerida 009, comprobar antes de usar.

## Antecedente documental — DOCUMENTAR 008

- Pedido posterior a 007: SVG en Correo/Google y cuatro enlaces de suscripciones, ocultar Inicio a RESTRICTED, dashboard acorde al producto para ADMIN/MANAGER y mismos SVG sol/luna de Inicio en Mi suscripción. Capturas usadas como referencias de controles, sin instrucciones adicionales.
- Siguiente número libre 008 comprobado. Entregados en orden [spec](../specs/008-dashboard-navegacion/spec.md), [plan](../specs/008-dashboard-navegacion/plan.md) y [tareas](../specs/008-dashboard-navegacion/tasks.md), todas pendientes. Propuesta: agregados de suscripciones registradas, períodos/planes y volumen mensual simulado; conserva últimos accesos y permisos generales de root.
- Inspección: Home ya redirige clientes antes de consultas, pero nav muestra Inicio; seis enlaces sin SVG y selector de Mi suscripción con glifos. Index usa gráfico meteorológico de ejemplo. No se corrigió código durante esta fase; cambios locales de 007 preservados.
- Solo Markdown actualizado. Verificación documental: 165 enlaces locales de diez documentos válidos; hashes de 338 archivos no-Markdown conservados sin adiciones/eliminaciones/cambios; git diff --check sin errores (avisos de conversión LF/CRLF de archivos anteriores). No ejecutados tests/build/migraciones ni importado settings normal; no lectura de .env/DB/media personal. Los 117 tests anteriores siguen perteneciendo a 007.
- Siguiente: revisión e instrucción posterior explícita para implementar 008, conforme a AGENTS.md. Sin vacío crítico que requiera entrevista; métricas/disposición son propuestas revisables. La autorización completa de 007 ya recibida se conserva.

## Entrega anterior — implementación 007 / PlanesApp

- Autorización posterior explícita: «te doy permsio de implementar todo la specs 007 alcanse completo». Entorno confirmado por el propietario: **.venv**. Documentación inicial spec→plan→tasks ya entregada antes del permiso; su evidencia de 176 enlaces/293 no-Markdown sin cambios correspondía a DOCUMENTAR, no al cierre actual.
- Implementado registro Google/email RESTRICTED+Free atómico, confirmación previa a contratar, cuatro planes y pagos/renovación simulados, tarjeta en vivo/giro, checkout/cambio/cancelación/revocación, historial y propiedad. Cliente no ve cuentas ajenas; 004/006 y MFA conservados. Sin vigilancia ni pagos reales.
- **117 métodos Django OK (11,865 s)** en core.test_settings; check/esquema/pip correctos, 76 HTML cargados, Ruff OK y Tailwind standalone 4.3.0 compilado. Último ajuste no-store de catálogo revalidado con su regresión. Ensayo SQLite en memoria: seed 4 planes/19 beneficios, reversión/reaplicación y colisión de cargo sin cambios parciales. [Evidencia](../specs/007-planes-app/evidencia/verificacion.json).
- Navegador: catálogo/métodos claro/oscuro, 360/390/768/1024/1440 px sin desbordamiento; tarjeta/nombre largo/teclado, máscaras, Plus aprobado, Hogar rechazado conservando Plus, cancelación/retiro, errores y guardado con scripts bloqueados. Capturas correctas en [validación](../specs/007-planes-app/validation.md). Zoom 200% y preferencia reducida en navegador siguen manuales; regla CSS implementada. Preview detenido, pestaña temporal cerrada/viewport restaurado.
- .venv reconstruido en su ruta conservando paquetes por Python ausente; pyvenv.cfg original en .recovery-007. Lock recibido real: 51 pins sin hashes; regenerado con 54 paquetes/hashes, versiones previas conservadas más oauthlib/PyJWT/pip declarado. No upgrade general ni nueva auditoría de vulnerabilidades. [Entorno y configuración Google](PLANESAPP_DESARROLLO.md).
- Tareas 01–14 técnicamente completas; 15 parcial por revisión manual visual, 16 parcial por aceptación del propietario. OAuth real no ensayado por ausencia de credenciales; mocks prueban callback/state/PKCE/alta/repetición/colisión/error, no red/consentimiento reales. SQLite no acredita bloqueos de otro motor.
- Temporales de preview/compilación 007 retirados; .venv y respaldo conservados. No lectura de .env/DB/media personal, migración real, commit/push o despliegue. Siguiente: configurar OAuth propio, autorizar instalación en DB local elegida tras respaldo y completar revisión manual/aceptación. Próxima spec sugerida 008, comprobar. No repetir autorizaciones de implementación ya recibidas.

## Último ajuste visual — 2026-10-05

Pedido acotado ejecutado: tarjetas internas de Perfil, Registro y cuenta/2FA centradas horizontalmente en el área junto al menú. CSS compartido y versión de caché actualizados; interiores/anchos/espaciado vertical conservados. Navegador con cuenta ficticia: tres tarjetas de 640 px, centrado exacto y sin desbordamiento en escritorio. Build Tailwind 4.3.0 y diff --check correctos; preview detenido y pestaña cerrada. Sin cambios funcionales, datos reales ni migraciones. Pendiente: revisión visual del propietario.

## Antecedente — correcciones autorizadas, specs 005/006

Seguimiento del 2026-10-02: requirements.txt encontrado con versiones antiguas y regenerado desde requirements.in con hashes. Las 52 versiones coinciden exactamente con .venv-actualizada y con las ya verificadas; presentes los 52 hashes de artefactos de instalación anteriores, pip check OK. [Evidencia](evidencia/actualizacion-20261002/requisitos-restaurados.json). No usar pip freeze desde otro entorno para actualizar este lock; ver la guía. Sin cambios de runtime/código ni repetición de la suite previa.

- Autorización posterior del propietario: aplicar correcciones de la validación y conservar axes/preventconcurrentlogins comentados. P-005-01 aceptada expresamente (correos/principales allauth, pruebas de colisión/restauración sin DB real). 006 documentada spec→plan→tasks y luego autorizada; P-006-01 confirmada: ADMIN solo MANAGER/RESTRICTED, MANAGER RESTRICTED, solo root con ADMIN crea ADMIN. No repetir aprobaciones ni preguntas ya resueltas.
- Entregado: Django 5.2.17 LTS, allauth 65.19.7 y dependencias compatibles; 49 entradas/lock de 52 paquetes con hashes, bcrypt completo, pip 26.2.1 y extra MFA sin activar WebAuthn/socialaccount. Alpine 3.17.4/DOMPurify 3.4.16/ECharts 6.1.0 exactos y SRI. Login/MFA/correo/jerarquía 004 conservados. [Guía](DEPENDENCIAS.md), [validación 005](../specs/005-actualizacion-dependencias/validation.md).
- Corregido Registro: permiso por cargo/código y opciones por actor, sin pk mágico; menú y POST coinciden. Alta/edición User/Profile indivisibles, preparación previa de foto, compensación y borrado anterior tras commit. Nuevas fotos en carpeta user_id para aceptar usernames de longitud máxima; sin mover archivos existentes. [Validación 006](../specs/006-integridad-registro/validation.md).
- Verificación final: **76 métodos Django correctos** (57 recibidos + 6 dependencias + 13 integridad), pip check/check/esquema OK, **61 HTML**, build Tailwind 4.3.0 idéntico, 52 Python + tres JS sin avisos devueltos por OSV. Deploy simulado mantiene W005/W021 de subdominios/preload, sin silenciarlos. Ruff de archivos nuevos principales y diff --check OK. [Evidencia](evidencia/actualizacion-20261002/verificacion.json).
- Migraciones: fixtures entre 5.1.2/allauth 0.62.1 y 5.2.17/65.19.7, principal/constraints/factores/hash/preferencia preservados y recovery heredado válido; preflight bloquea colisiones/estado MFA inválido sin escritura. Respaldo sintético restaurado con paquetes antiguos. **No migración real ni nueva migración propia**. Comando preflight disponible para entorno autorizado, no modifica datos ni evita por sí mismo ejecutar migrate manualmente.
- Navegador: Registro por ADMIN/MANAGER/root sin cargo, listado/MFA, escritorio/móvil, modos/gráfico/menús y CDN bloqueado con degradación correcta. Ingreso/guardado de credenciales nuevas por interfaz y aceptación funcional quedan manuales por política del navegador; servidor comprobado. Pantallas y límites detallados en validaciones.
- Conservación: main/6bc1bd4, documentación/skill local previas preservadas. Snapshot .recovery-005 de 204 archivos seleccionados con rutas únicas y hashes verificados, sin secretos/DB/media; .venv anterior intacto (roto), nueva **.venv-actualizada** lista para pruebas/desarrollo. Core/settings normal y opciones comentadas preservados; no .env, DB/media personal, datos reales, producción, deploy, commit/push ni otros repositorios. Preview detenido, pestaña temporal cerrada y .work-005 retirada; entorno actualizado, respaldo y evidencia conservados. [Manifiesto de cierre](evidencia/actualizacion-20261002/cierre.json).
- Estado de tareas: T00501–07 y T00601–05 técnicamente completas; aceptación del propietario y tareas manuales históricas de 002–004 siguen pendientes. AUD-001 a 006 corregidos en su alcance; AUD-010 mitigado con entorno nuevo; AUD-007/008/009 requieren decisiones de cifrado/antiabuso/auditoría por producto. No se activa axes por inferencia. [Informe actualizado](VALIDACION_PREPRODUCCION.md).
- Siguiente paso: revisar manualmente formularios/credenciales en entorno ficticio y elegir .venv-actualizada como intérprete. Para cada derivado, definir hosting/proxy, correo/opcionales, logs/cifrado/respaldo y autorizar aparte su migración tras preflight/ensayo. No se recomienda producción por una suite verde. Próximo número libre sugerido 007, comprobar.

## Antecedente — auditoría de base y DOCUMENTAR 005

- Pedido: validar la base de futuros proyectos mediante skill validar-produccion-sdd y preparar corrección de dependencias antiguas. Fase ejecutada: auditoría independiente y Markdown; la skill separa revisión de correcciones y AGENTS exige documentación previa para actualizar dependencias.
- Versión revisada: main/6bc1bd484b6fd0d2eea9e1c0e6802370c069cc71; inicialmente solo skill nueva sin seguimiento, conservada. [Informe global](VALIDACION_PREPRODUCCION.md) y [evidencia](evidencia/auditoria-20261002/INVENTARIO_DEPENDENCIAS.md). Fuente funcional preservada; no cambios de versiones/código/tests/migraciones propios.
- Resultado: **Con bloqueadores**, además de evidencia operativa insuficiente. Django 5.1 sin soporte, librerías Python/JS con avisos por versión, MANAGER puede crear ADMIN cuando su cargo no es pk=1, alta parcial ante fallo de Profile. Hash bcrypt configurado sin biblioteca y entorno .venv roto; demás riesgos/condiciones en informe. No se afirma explotación de todas las CVEs.
- Verificado actualmente: venv limpio Python 3.12.14 con 47 pins existentes, pip check correcto, **57 tests OK**, check sin problemas, no cambios de esquema, **60 plantillas**, build Tailwind 4.3.0 en copias idéntico al CSS actual; deploy simulado con W005/W021 contextualizadas. Diagnósticos y navegador exclusivamente ficticios: modo persistente, abrir/cancelar restablecimiento, denegación de MANAGER, root sin cargo y logout. No cierre de pendientes visuales/aceptación históricos.
- Dependencias: 38 de 47 pins tienen versión publicada posterior; OSV devuelve 146 registros brutos, **88 coincidencias distintas por paquete/versión** tras aliases (67 Python/21 JS), no 88 ataques demostrados. 47 candidatas + tres frontend sin avisos devueltos en consulta actual; resolución Python preliminar sin conflicto. No se instalaron versiones nuevas ni se probaron funcionalmente.
- Documentos nuevos: [spec 005](../specs/005-actualizacion-dependencias/spec.md), [plan](../specs/005-actualizacion-dependencias/plan.md), [tareas](../specs/005-actualizacion-dependencias/tasks.md), [validación documental](../specs/005-actualizacion-dependencias/validation.md). Seis RF/siete tareas pendientes; propone Django 5.2.17 LTS, actualizaciones compatibles, frontend fijo/integridad y lock/mantenimiento. No nueva app ni correcciones funcionales de Registro/perfil en 005.
- **Decisión P-005-01 pendiente:** allauth 65.19.7 normaliza correos, desmarca principales extra y agrega restricciones mediante cinco migraciones nuevas. Dos backfills tienen reverse noop; reversión no restaura datos. Wheel oficial inspeccionado con hash verificado, no instalado. No asumir aceptación de efectos ni aplicar migraciones reales.
- Siguiente paso: revisar 005, resolver P-005-01 y dar instrucción posterior explícita para implementar su alcance. AUD-004/005 requieren definición/autorización de alcance propio; no se solucionan por upgrade. No repetir P-004-01/02. Próximo número libre sugerido 006, comprobar.
- Cierre de diagnóstico, conservación de fuentes y enlaces documentales en [cierre.json](evidencia/auditoria-20261002/cierre.json). Sin lectura de .env/DB/media personal, datos reales, producción, despliegue, commit/push ni reparación del venv normal.

## Pedido anterior — spec 004, implementación entregada

- Autorización: propietario revisó spec/plan/tasks y después autorizó explícitamente únicamente el alcance completo de 004 el 2026-10-02. Implementación ejecutada; no repetir aprobación de código. Sin permiso para datos reales, producción, despliegue, commit/push o migraciones reales.
- Documentos: [spec](../specs/004-administracion-usuarios/spec.md), [plan](../specs/004-administracion-usuarios/plan.md), [tareas](../specs/004-administracion-usuarios/tasks.md), [validación](../specs/004-administracion-usuarios/validation.md). Siete RF; T-004-01 a 06 completas, T-004-07 parcial y T-004-08 revisión pendiente.
- Implementado: restablecimiento administrativo sin correo/token desde listado, formulario con contraseña del operador y nueva dos veces; validadores/hashing/POST/CSRF/no-cache/campos sensibles. Cambia solo password; no activa ni altera MFA/cargo/email/preferencia/fotos. Sesiones anteriores del destinatario invalidadas al siguiente request; operador conserva su sesión.
- Permisos: ADMIN gestiona MANAGER/RESTRICTED y restablece sus contraseñas; MANAGER solo activa/desactiva RESTRICTED. Incluso superusuario requiere cargo. Propia cuenta/ADMIN/root destinatario/sin cargo o desconocido protegidos. Política única por acción y fila; 403/404/405, actor/destinatario vigentes. Helper global/Registro y demás vistas conservados.
- Integridad: escrituras mínimas/transaccionales, reenvío idempotente, error 500 contextual sin éxito falso para fallo previsto; pruebas revierten una escritura real seguida de error. Sin catch general ni cambios de modelos/migraciones/dependencias de producto.
- Estado Git inicial de esta implementación: main/8f9adda, ocho documentos modificados y carpeta 004 previa. Conservados, sin stage/reset/commit/push. Snapshot .recovery-004/antes-implementacion.zip (123 archivos seleccionados), manifiesto/auditoría SHA-256. Configuración/mixin/modelos/adapter/home/tokens/interfaz/requirements/AGENTS/constitución idénticos.
- Evidencia: **57 métodos Django OK** (43 recibidos + 14 nuevos; dos de gestión ajustados), check sin problemas, no cambios de esquema, Tailwind 4.3.0 OK/CSS generado idéntico y 60 plantillas compiladas. Matriz actor/destinatario/URL/HTML, root/cargos/inactivos, CSRF, contraseñas/espacios, rollback, sesiones A/B, correo/MFA/modo visual y atributos preservados comprobados en entorno aislado.
- Prueba MFA: allauth 0.62.1 registra modelos socialaccount desactivado al reanudar MFA y afectó una cascada posterior. Caso de nuevo login+TOTP aislado en subprocess con los mismos test_settings/SQLite efímero; suite completa pasó. No se activó socialaccount ni cambió la prueba de cascada de 003; detalle del fallo/corrección en validation.md.
- Navegador: listado/formulario en cinco anchos, claro/oscuro, sin desbordamientos; acciones inferiores de MANAGER y root sin cargo, desactivación/reactivación, campos requeridos, Tab/foco, cancelar, envío vacío bloqueado, errores reales y CSP sin scripts. [Formulario](../specs/004-administracion-usuarios/evidencia/formulario-light-1440.png). Guardado válido y sesiones probados en servidor; introducir/enviar nueva contraseña por interfaz queda para revisión manual del usuario, exigida por la política de la herramienta de navegador. No se emplearon contraseñas reales.
- Entorno: .venv vuelve a fallar por Python312 inexistente; no reparado. Runtime Codex con requirements exactos temporales, descarga/escalación revisada; sandbox no leía los paquetes. pip advierte cffi/cryptography global, sin actualización. Preview detenido tras comprobar PID/comando; pestaña cerrada/viewport restituido. Runtime temporal eliminado con ruta absoluta verificada, sin enlaces; snapshot/helpers/evidencia conservados. No .env, DB de desarrollo/producción ni media personal.
- Cierre documental: 13 documentos/150 enlaces locales válidos, siete RF y seis tareas completas/dos parciales; 14 contratos protegidos idénticos por SHA-256, diff revisado sin errores de espacios. Sin aceptación del propietario asumida ni autorización extra solicitada para el código.
- Pendientes: envío válido de nueva contraseña por interfaz y revisión/aceptación funcional del propietario (T-004-07/08). SQLite no certifica bloqueos/concurrencia PostgreSQL. Se mantienen pendientes visuales previos de 002/003 y la aplicación real de 0002 de 003 excluida de esta autorización.
- Siguiente paso: revisar la entrega y completar el envío válido manualmente con datos ficticios en entorno aislado; no repetir preguntas P-004-01/02 ni autorización de 004. Próxima spec sugerida 005, comprobar disponibilidad.

## Antecedente documental de 004 — previo a autorización

- Pedido: restablecimiento administrativo sin correo desde UsuarioApp y jerarquía ADMIN > MANAGER > RESTRICTED. El propietario confirmó que se aplica a activar y desactivar: ADMIN sobre MANAGER/RESTRICTED; MANAGER solo RESTRICTED.
- Fase permitida: DOCUMENTAR. No hay instrucción posterior de implementación de 004; las autorizaciones previas de 002/003 se conservan para su alcance.
- Documentos: [spec](../specs/004-administracion-usuarios/spec.md), [plan](../specs/004-administracion-usuarios/plan.md), [tareas](../specs/004-administracion-usuarios/tasks.md), [validación documental](../specs/004-administracion-usuarios/validation.md). Siete RF, ocho tareas de implementación pendientes.
- Inspección actual: Git main, HEAD 8f9adda; árbol limpio inicial. Sin stage/reset/commit/push. Las descripciones de cambios locales/sin Git que aparecen en entregas anteriores son históricas, no el estado de esta inspección.
- Referencia: inventario y lectura selectiva del ZIP compartido, sin extracción/ejecución. Propone SetPasswordForm con contraseña de operador y nueva dos veces; contiene otras reglas/cambios/dependencia de FruticulaApp que no se trasladan. Captura orienta ubicación de acción; no acredita implementación local.
- Propuesta: política por acción/destinatario para vistas y filas, formulario privado con validadores Django, POST/CSRF, hash seguro y cambios mínimos. Sin nueva app/modelos/migraciones; conserva login, correo/MFA, registro/perfil y modo visual. No evita el ORM: elimina dependencia del correo para esta operación.
- Decisiones críticas resueltas: P-004-01 exige cargo incluso al superusuario (ADMIN para restablecer, ADMIN/MANAGER para gestionar inferiores); P-004-02 aplica jerarquía al activar y desactivar. Confirmadas por el propietario, sin repetir preguntas; helper global y permisos de otras acciones conservados.
- Evidencia actual: lectura estática y documentación en orden spec/plan/tasks. Doce documentos, 105 enlaces locales sin destinos inexistentes, siete RF y ocho tareas pendientes; 211 archivos versionados no Markdown idénticos por SHA-256. [Cierre documental](../specs/004-administracion-usuarios/validation.md). No se ejecutan pruebas Django/build/servidor/migraciones en esta fase; las 43 pruebas de 003 son antecedente y no certifican 004.
- Siguiente paso: revisar documentos 004 con el propietario; después una instrucción posterior explícita permitirá implementar tareas de esta spec. No quedan decisiones críticas pendientes. No usar datos reales, desplegar ni aplicar 0002 por este pedido. Próxima spec sugerida 005, comprobar disponibilidad.

## Pedido anterior — spec 003, implementación entregada

- Pedido: botón de sol/luna en Inicio para alternar claro/oscuro y guardar la elección por usuario.
- Fase autorizada: el propietario revisó documentos y después autorizó explícitamente únicamente el alcance completo de 003. No autoriza datos reales, producción, despliegue, commit/push ni aplicación de migraciones a la base existente.
- Documentos: [spec](../specs/003-modo-visual-usuario/spec.md), [plan](../specs/003-modo-visual-usuario/plan.md), [tareas](../specs/003-modo-visual-usuario/tasks.md) y [validación](../specs/003-modo-visual-usuario/validation.md). Siete RF; T-003-01 a 06 completadas, T-003-07 validación visual parcial y T-003-08 revisión del propietario pendientes.
- Implementado: luna/sol con nombre/estado/foco accesibles en Inicio; POST/CSRF idempotente, propietario de sesión, todos los actores activos; preferencia separada de Profile, sin fotos/cargos. Processor de lectura sin altas en GET, HTML inicial y paletas compartidas. Anónimo/preautenticación claro, logout conserva elección por cuenta.
- Colores: único tokens.css, pares --brand-light/--brand-dark y sus textos; petróleo inicial, ciruela/cobre en ambos modos medidos/probados y petróleo restituido. Hover oscuro ajustado tras detectar contraste 4,34:1; QR sobre blanco para conservar legibilidad. Guía actualizada.
- Esquema: 0002 CreateModel con one-to-one/check; generado, aplicado y revertido únicamente en SQLite efímero de pruebas. No backfill ni cambios a User/Profile/Position. Rollback real pierde elecciones; aplicación a la base existente necesita autorización de entorno/respaldo antes de usar allí el guardado.
- Inspección actual: Git está disponible, rama main, con cambios locales de la renovación y archivos sin seguimiento. Se conservaron; no se hizo stage, reset, commit ni push. El registro «sin Git» de 002 que sigue debajo corresponde a aquella fase.
- Recuperación: .recovery-003/antes-implementacion.zip, 123 archivos con rutas relativas y manifiesto SHA-256. Ninguna eliminación; contratos protegidos idénticos (settings normal/aislado, requirements, mixin/rutas, home vistas/middleware, AGENTS/constitución). Las diferencias respecto de ese snapshot están en el mapa de 003 y sus documentos. Código previo de 002 conservado.
- Evidencia ejecutada: **43 métodos Django OK** (27 previos y 16 nuevos; MFA ampliado), check sin problemas y no cambios de esquema pendientes; build Tailwind 4.3.0, 59 HTML, cinco contratos JS y 180 pares de contraste correctos. Propiedad/CSRF/activos e inactivos, fallos, restricciones, aislamiento A/B, sesiones y migración/reversión comprobados en servidor aislado.
- Navegador: cinco anchos de Inicio en ambos modos, tres marcas, luna/sol, Enter/Espacio/Tab/foco, logout/login A/B y usuario sin perfil; usuarios/registro/perfil/contraseña/MFA/QR/gráfico. Selector sin scripts verificado en preview separado con CSP script-src 'none'. [Vista final](../specs/003-modo-visual-usuario/evidencia/inicio-final.png); evidencia y límites en validation.md.
- Entorno: .venv/Scripts/python.exe --version falla (Python312 inexistente), no reparado. Dependencias exactas temporales con runtime de Codex; primera descarga bloqueada por red del sandbox, revisión automática permitió después. No se actualizaron requirements ni el runtime global. Ambos previews detenidos por sus PID/comandos comprobados; .codex-test-runtime retirada tras verificar su ruta absoluta dentro del proyecto. Se conservan snapshot, helpers y evidencia.
- Documentación final: 22 documentos revisados, 175 enlaces locales válidos y cero inexistentes; siete RF conservados, seis tareas completas y dos con pendientes explícitos. Sin consultas a datos reales ni aceptación asumida.
- Pendientes: zoom real 200 %, preferencia reducida activada en navegador, autofill real y revisión visual exhaustiva de estados alternativos/errores/mensajes largos (T-003-07); revisión estética/funcional del propietario (T-003-08). Se conservan T-002-13 y aceptación de 002; no atribuir esas limitaciones a falta de autorización de código.
- Siguiente paso seguro: completar revisión visual pendiente y revisar entrega con el propietario. Antes de usar la función en la base existente, acordar entorno/respaldo y autorizar allí 0002. No repetir autorización de implementación de 003 ya recibida. Próxima spec sugerida: 004, comprobar disponibilidad.

Antecedente DOCUMENTAR de 003: 13 documentos, 106 enlaces locales válidos, siete RF y ocho tareas pendientes; SHA-256 de 105 archivos de código/recursos/dependencias idénticos entonces, sin ejecución funcional en aquella fase. La implementación posterior y su evidencia se describen arriba.

## Renovación 002 — entrega anterior del 2026-10-02

- Pedido: renovación integral de la identidad visual de Base-2, con colores centralizados y mejores interacciones; usar frontend-design.
- Fase autorizada: después de DOCUMENTAR, el propietario revisó spec/plan/tasks y autorizó explícitamente el **alcance completo de 002** el 2026-10-02. No autorizó producción, despliegue, commit ni push.
- Spec activa: [002-Renovación visual](../specs/002-renovacion-visual/spec.md), [plan](../specs/002-renovacion-visual/plan.md), [tareas](../specs/002-renovacion-visual/tasks.md), [validación](../specs/002-renovacion-visual/validation.md). T-002-01 a 12 y 14 completadas; T-002-13 parcial. Aceptación estética y funcional pendiente.
- Implementado: espacio claro de gestión, navegación compacta/móvil, login, Inicio/listado/registro/perfil, cuenta/MFA y seis errores; controles, crispy, mensajes, diálogos/foco y carga. Identidad inicial petróleo; ciruela/cobre comprobadas y petróleo restituido.
- Colores: [tokens.css](../web/static/css/tokens.css), puente Tailwind y gráfico con estilos computados. [Guía reutilizable](PERSONALIZACION_VISUAL.md) guardada; skill frontend-design referencia el contrato y pasó quick_validate. Cambiar valores no requiere build; gestionar caché según guía.
- Preservado por SHA-256: configuración común/normal/aislada, requirements, modelos, vistas, rutas, helper/mixin, logo/avatar, AGENTS/constitución. Formularios cambian solo atributos visuales; processor/HTML comparten el mismo permiso. No se leyó .env, db.sqlite3 ni media personal.
- Git: esta copia sigue sin repositorio; no existe diff contra la base principal ni rama actual verificable. Recuperación en `.recovery-002/antes-implementacion.zip` (189 archivos seleccionados) con manifiesto SHA-256; ninguno eliminado en la auditoría posterior. Los 106 archivos de código/recursos iniciales estaban intactos antes de implementar.
- Evidencia: **27 pruebas Django OK** (15 base y 12 añadidas), check sin problemas, sin cambios de esquema, Tailwind 4.3.0 standalone OK, 59 HTML compiladas, cinco contratos JS y 27 contrastes medidos correctos. Permisos por URL/visibilidad, POST/CSRF, filtros, imagen, login/logout/reset y TOTP completo verificados en servidor aislado.
- Documentación: 18 documentos revisados, 127 enlaces locales válidos y cero inexistentes; nueve RF conservados, 13 tareas completadas y T-002-13 parcial explícita.
- Navegador: datos sintéticos, SQLite en memoria y media/correo temporales; Inicio/listado en cinco anchos, tres paletas, Tab/Escape/foco/scroll, confirmaciones, perfil/imagen y registro inválido. Revisión final de login/recuperación/cierre público/Inicio/contraseña/MFA y consola. Capturas en `specs/002-renovacion-visual/evidencia/`; [Inicio final](../specs/002-renovacion-visual/evidencia/inicio-final.png).
- Pendiente de T-002-13: zoom real al 200 %, preferencia reducida activada en navegador, revisión visual completa de estados alternativos de cuenta/MFA/errores y mensajes largos. Las capacidades disponibles no ofrecieron zoom/preferencia; contratos JS y CSS reducido sí comprobados. No apareció decisión crítica ni migración no acordada.
- Entorno: `.venv` apunta a Python 3.12 inexistente, fallo reproducido. Verificación mediante runtime de Codex y dependencias exactas aisladas; requirements y `.venv` intactos. Preview detenido y dependencias temporales retiradas al cerrar; se conserva el snapshot y el helper de revisión. Su ejecución solo prepara SQLite en memoria.
- Siguiente paso de aquella entrega: completar T-002-13 con navegador que permita zoom/preferencia reducida y revisar visualmente la entrega con el propietario. No repetir la solicitud de autorización de implementación de 002 ya recibida. El siguiente pedido se documentó después como 003.

## Fase inicial de esta copia — DOCUMENTAR, 2026-10-02

Antes de la autorización posterior se entregaron únicamente Markdown: spec/plan/tasks e índices/estado/decisiones/trazabilidad. Se verificaron 11 documentos y 67 enlaces locales válidos, nueve RF y 14 tareas pendientes, sin código, servidor, build ni tests de aplicación. Los hashes de los 106 archivos de código/recursos/dependencias se mantuvieron idénticos. Ese resultado es histórico y no debe confundirse con la implementación posterior registrada arriba.

## Antecedente de la base recibida — 2026-09-22

Información histórica conservada. Sus pruebas y rama no certifican el estado funcional actual de esta copia ni la propuesta 002.

- Entrega actual: [spec transversal 001-CalidadBase](../specs/001-calidad-seguridad-base/spec.md) implementada y verificada técnicamente.
- Código: configuración común/aislada, pruebas de usuarios, permiso compartido de navegación y Tailwind 4.3.0 standalone implementados.
- Fase: validación técnica terminada; aceptación funcional final del propietario pendiente.
- Módulo de negocio activo: ninguno.
- Próximo identificador de spec: 002, confirmar disponibilidad.
- Autorización de implementación: concedida por el propietario el 2026-09-20 para todas las tareas T-001; ejecutada.
- Trabajo preservado: requirements.txt UTF-8, media/ ignorado, ACCOUNT_ADAPTER conectado, ACCOUNT_ALLOW_REGISTRATION ausente, opcionales desactivados, correo de consola y gráfico demostrativo.
- Evidencia: 15 tests OK con core.test_settings; check sin problemas; sin migraciones pendientes; build Tailwind 4.3.0 standalone y testigos de fuentes/exclusión OK. La revisión de navegador escritorio/móvil corresponde al 2026-09-20 y no se repitió porque este ajuste no cambió plantillas. Detalle en [validation.md](../specs/001-calidad-seguridad-base/validation.md#ajuste-del-2026-09-22).
- Entorno: el Python configurado por `py` sigue roto. La verificación del 2026-09-22 usó dependencias aisladas en `.codex-test-runtime`, eliminadas al terminar; no se modificaron datos reales.
- Siguiente acción: revisión/aceptación del propietario o documentar el siguiente cambio con ID 002.
- Rama/commit: main; no se creó commit ni se hizo push.

## Actualizar al terminar o pausar una sesión

| Campo                     | Registrar                                                   |
| ------------------------- | ----------------------------------------------------------- |
| Fecha / producto / módulo | Datos reales                                                |
| Fase autorizada           | Documentar, revisar, implementar tareas concretas o validar |
| Spec y tarea activa       | Rutas e IDs                                                 |
| Cambio pedido             | Resumen y exclusiones                                       |
| Trabajo preservado        | Archivos/cambios previos del usuario                        |
| Hecho                     | Archivos efectivamente guardados                            |
| Evidencia                 | Comandos, resultados y límites                              |
| Pendientes / bloqueos     | Decisiones y pruebas que faltan                             |
| Siguiente paso seguro     | Una acción concreta                                         |
| Rama/commit               | Solo si existe; no inventar                                 |

No guardar secretos ni copiar datos personales. «Documentación lista» no equivale a «módulo implementado».


## Antecedente documental — aplicación móvil, 2026-10-19

- Solicitud: crear la aplicación móvil aprovechando esta carpeta y el informe Word aportado. Orquestador aplicado: 01-especificar → 02-planificar → 03-tareas, solo DOCUMENTAR.
- Entrega: [spec 010](../specs/010-aplicacion-movil/spec.md), [plan](../specs/010-aplicacion-movil/plan.md), [tareas](../specs/010-aplicacion-movil/tasks.md). Todas las tareas pendientes; sin código/APK, instalación, migración, despliegue, commit o push.
- Inspección estática: existen PlanesApp/CuidadosApp y propiedad por owner, incluso root; rutas web y servicios transaccionales reutilizables. Git tiene numerosos cambios locales anteriores y archivos 009/CuidadosApp sin seguimiento, preservados. Informe leído como referencia; no son instrucciones de ejecución sus recomendaciones ni evidencia sus afirmaciones de eficacia/cumplimiento.
- Aclaración posterior 2026-10-19: usuario confirma Flutter iOS/Android, funciones por plan y detección de posición con MediaPipe. RF-010-09 ampliado y RF-010-11/12 añadidos; 15 tareas pendientes. P-010-01 conserva ubicación/hardware/reglas, P-010-02 colaboración; P-010-06 matriz comercial nueva por confirmar. Propuesta Premium para MediaPipe según beneficio futuro del catálogo 0004; no atribuida como decisión comercial aprobada. Autenticación y push pendientes. No código autorizado.
- Verificación de esta entrega: lectura/extracción del Word, inspección estática y revisión de documentos/enlaces. Sin suites/build ni pruebas Android; resultados históricos no acreditan RF-010. No se leyó .env ni DB real.
- Siguiente paso: incorporar respuestas en esta misma spec, cerrar contrato/alcance y esperar instrucción posterior explícita de implementación. Aceptación pendiente.


### Verificación documental del ajuste 010 — 2026-10-19

Catálogo y modelos inspeccionados: 0004 conserva funciones manuales en todos los planes, cupos 1/3/ilimitados y anuncio Premium de IA/cámaras; PlanBenefit es descriptivo, no sistema de permisos funcionales. Propuesta nueva: capacidades explícitas comprobadas en API/procesamiento/push y Flutter. Referencias oficiales Flutter y MediaPipe consultadas; no versiones/SDK instalados ni detección probada. Actualizados spec/plan/tasks, índice, arquitectura, proyecto, decisiones y trazabilidad; enlaces locales revisados. No suites ni compilaciones por cambios exclusivamente Markdown. Siguiente: resolver matriz y detalles pendientes en esta spec, mantener fase DOCUMENTAR hasta instrucción posterior de implementación.


## Estado vigente 010 — implementación autorizada, 2026-10-19

La instrucción posterior «hacelo en base a todo lo que te proporcione…» y «sigue ejecutando» autoriza código/pruebas. Sustituye el estado exclusivamente documental anterior. Flutter para Android/iOS implementado con API Django propia; autenticación allauth headless, capacidades por plan, agenda/pacientes/medicamentos/postura/historial, nodo local MediaPipe calibrable y registro de dispositivos push.

168 tests Django aislados OK; APK Android compilado; 5 pruebas sintéticas Edge y carga real del modelo OK. Ver resultados finales de Flutter/iOS, evidencia visual y limitaciones en [validation 010](../specs/010-aplicacion-movil/validation.md). [Guía para probar](MOVIL_DESARROLLO.md). Demo separada de DB existente, sin datos reales. No despliegue, commit ni push.

Pendientes: cámara/hardware y métricas reales, Google/Firebase/APNs, paridad en teléfonos, colaboración y aceptación funcional. Las detecciones no registran cuidados manuales. La migración nueva no se aplicó a DB existente. Cambios previos preservados.

## Ajuste vigente — 2026-10-20

Usuario exige registro en web y login de la misma cuenta en app; formulario de alta móvil retirado del código, sustituido por enlace al registro web. APK anterior aún no contiene este ajuste. SDK temporal ausente al reanudar; análisis/recompilación pendientes. Referencia AI Studio recibida, inaccesible sin login Google; adaptación visual pendiente de inspección. [Validación y límites](../specs/010-aplicacion-movil/validation.md).


### Referencia AI Studio revisada — 2026-10-20

Acceso resuelto y prototipo inspeccionado. Usuario confirma planes de la web (Free/Plus/Premium,1/3/ilimitados) y MediaPipe tanto en teléfono como en nodo fijo. Registro web/login móvil compartidos. [Mapa y límites](../specs/010-aplicacion-movil/referencia-ai-studio.md); spec/plan/tasks010 ampliados, tareas18–23 pendientes. No se afirma que el diseño o la cámara móvil ya estén implementados.


### Código adaptado a referencia — 2026-10-20

Autorización posterior recibida; UI de seis secciones, tema índigo y cámara puntual móvil mediante plugin MediaPipe Android/iOS escritos, manteniendo nodo fijo y planes web. API dual/migración0005 y170 tests aislados OK. Compilación, lock actualizado, UI y cámara reales pendientes por SDK ausente/disco lleno. APK antiguo no contiene estos cambios. [Validación detallada](../specs/010-aplicacion-movil/validation.md).


## Móvil — 2026-10-21
SDK restaurado; lock actualizado, análisis limpio y9 pruebas Flutter OK. APK ARM64 debug actualizado con plugin MediaPipe; UI y login demo comprobados en navegador. Migración0005 solo demo. iOS bloqueado por menos de1GB libre y SDK pendiente; cámaras físicas, OAuth/push y firma sin validar. Ver [validación010](../specs/010-aplicacion-movil/validation.md).

## Pedido22/10/2026 — 011 DOCUMENTAR

Usuario aprueba estilo móvil y pide instalar en Android e iPhone, alarmas desde Reloj, web de planes con misma identidad y carpetas/componentes diferenciados. [Spec011](../specs/011-ecosistema-instalable/spec.md), plan y tareas creados solo en Markdown. Inspección confirma reloj vacío cuando no existe PostureTimer, API exige primer evento, sin dependencia de notificaciones locales. RAR comparado selectivamente: cinco archivos de planes/diseño idénticos; rutas antiguas sin API móvil. No sobreescribir carpeta.11GB libres observados, sin nueva compilación. Propuesta web/mobile/edge y avisos locales sin cuidado ficticio. Pendiente instrucción posterior de implementación, servidor remoto y firma/dispositivo iOS; no código/dependencias/migraciones/despliegue ejecutados.
