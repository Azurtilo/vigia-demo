# Tareas — 013 / Cuidado delegado

Spec: [spec.md](spec.md). Plan: [plan.md](plan.md).
Estado: propuestas. Implementación autorizada: NO.
No ejecutar tareas de código por el hecho de aparecer aquí.

- [ ] T-013-01 — Modelos `PatientAccess`, `PatientInvitation` y `AccessCodeAttempt` con la migración aditiva 0008.
  - RF: RF-013-01, 02, 05, 06. Componente: web.
  - Depende de: ninguna.
  - Archivos previstos: `web/CuidadosApp/models.py`, `web/CuidadosApp/migrations/0008_*.py`.
  - Hecho cuando: `makemigrations --check` sin cambios pendientes; pruebas de restricciones (un vínculo activo por paciente y usuario, rol válido); avance y reversión 0008 ↔ 0007 probados en SQLite de pruebas.
- [ ] T-013-02 — Módulo `access.py`: matriz de acciones, `role_for`, `patient_for`, `accessible_patients`, `active_ids_for` y `recipients`.
  - RF: RF-013-07, 08, 10, 11. Componente: web.
  - Depende de: T-013-01.
  - Archivos previstos: `web/CuidadosApp/access.py`, `web/CuidadosApp/test_access.py`.
  - Hecho cuando: pruebas unitarias de cada rol × acción (incluidos superusuario sin vínculo y vínculo revocado) y de ids activos con dos titulares de planes distintos.
- [ ] T-013-03 — Servicios: resolver con `patient_for`, bloquear la fila del titular, comprobar de nuevo el rol tras el bloqueo y usar elegibilidad y plan del titular.
  - RF: RF-013-07, 09, 10. Componente: web.
  - Depende de: T-013-02.
  - Archivos previstos: `web/CuidadosApp/services.py`, `web/CuidadosApp/capacity.py`.
  - Hecho cuando: el cuidador registra con autor propio; la ocurrencia no se duplica entre titular y cuidador; un paciente fuera del cupo del titular rechaza a ambos; una revocación previa al bloqueo produce 404; la suite actual de CuidadosApp sigue verde.
- [ ] T-013-04 — Vistas web de cuidados con `care_action` por vista, listas y agenda con pacientes vinculados, insignia de rol y vista resumida del cuidador.
  - RF: RF-013-07, 08, 14. Componente: web.
  - Depende de: T-013-03.
  - Archivos previstos: `web/CuidadosApp/views.py`, `web/CuidadosApp/permissions.py`, `scheduling.py` y plantillas en `web/templates/pages/CuidadosApp/`.
  - Hecho cuando: pruebas de vistas por rol (200/403/404) sin cambios en la base al denegar; sin coincidencias de `owner=request.user` fuera de acciones de titular (revisión con `grep` anotada en validation).
- [ ] T-013-05 — Servicio de invitaciones: generar, previsualizar, aceptar, revocar, renunciar y límite de intentos.
  - RF: RF-013-01..06, 10. Componente: web.
  - Depende de: T-013-02.
  - Archivos previstos: `web/CuidadosApp/invitations.py`, `web/CuidadosApp/test_access.py`.
  - Hecho cuando: los criterios de aceptación RF-013-01..06 y 10 pasan como pruebas, incluido el código usado dos veces en paralelo (solo uno gana) y ningún código en claro en la base ni en logs.
- [ ] T-013-06 — Interfaz web: «Personas con acceso» (titular), «Unirme con un código» y «Dejar de cuidar», con enlace en el menú.
  - RF: RF-013-01, 02, 06, 13. Componente: web.
  - Depende de: T-013-04, T-013-05.
  - Archivos previstos: `web/CuidadosApp/views.py`, `urls.py`, `forms.py`, plantillas nuevas, `web/templates/components/navbar/nav.html`; build de Tailwind si cambian clases.
  - Hecho cuando: pruebas de vistas (CSRF, POST, roles); revisión en navegador claro/oscuro y en ancho móvil registrada en validation.
- [ ] T-013-07 — API móvil: `role` y `allowed_actions` en pacientes; endpoints de acceso, aceptación, renuncia y resumen; `patient_for` en todos los endpoints con paciente.
  - RF: RF-013-07, 08, 12, 13, 14. Componente: web (API).
  - Depende de: T-013-04, T-013-05.
  - Archivos previstos: `web/CuidadosApp/api/views.py`, `api/urls.py`, nuevo `api/access.py`.
  - Hecho cuando: prueba parametrizada de cada endpoint × rol; las pruebas actuales de `test_mobile.py` siguen verdes (campos aditivos).
- [ ] T-013-08 — Detección: nodos y revocación solo titular, observaciones solo titular y familiar, `allowed()` con capacidades del titular.
  - RF: RF-013-07, 09. Componente: web (API).
  - Depende de: T-013-02.
  - Archivos previstos: `web/CuidadosApp/api/detection.py`.
  - Hecho cuando: pruebas de acceso denegado por rol y usuario ajeno (404, sin cambios en la base) en `nodes`, `observations`, `phone-observations` y `revoke` (cierra QA-08); contrato del nodo sin cambios.
- [ ] T-013-09 — Destinatarios de avisos: cuidado pendiente al titular y a los cuidadores; riesgo al titular, a los familiares y a los cuidadores (D-063); todo según el plan del titular.
  - RF: RF-013-11. Componente: web.
  - Depende de: T-013-02.
  - Archivos previstos: `web/CuidadosApp/scheduling.py`, `web/CuidadosApp/management/commands/send_mobile_reminders.py`.
  - Hecho cuando: pruebas con Firebase simulado de cada rol, sin duplicados por dispositivo y sin avisos tras la revocación. Coordinar con la tarea de push inmediato de la spec 012 (D-051).
- [ ] T-013-10 — App Flutter: insignia de rol, acciones según `allowed_actions`, pantalla de código, gestión de accesos del titular, vista resumida del cuidador y manejo de 403/404.
  - RF: RF-013-12, 13, 14. Componente: mobile.
  - Depende de: T-013-07.
  - Archivos previstos: `mobile/lib/core/api.dart`, `mobile/lib/features/patients/`, `mobile/lib/features/home/care_home.dart`, `mobile/lib/features/profile/profile_panel.dart`, pruebas en `mobile/test/`.
  - Hecho cuando: `flutter analyze` sin problemas y pruebas de widgets para titular y cuidador.
- [ ] T-013-11 — Validación integrada y documentación.
  - RF: todos. Componentes: web, mobile y edge (regresión).
  - Depende de: T-013-01..10.
  - Hecho cuando:
    - suites Django, Edge y Flutter verdes con conteos reales;
    - ensayo en navegador y en Android físico con dos cuentas (titular y cuidador): invitar, aceptar, registrar, revisar autoría y revocar;
    - resultados en `validation.md`;
    - TRAZABILIDAD (HU-01/02/03/04/06), `specs/README.md`, ESTADO, `CUIDADOSAPP_DESARROLLO.md` y `MOVIL_DESARROLLO.md` actualizados.

## Autorización posterior

Pendiente. Registrar mensaje/fecha y tareas autorizadas solo cuando ocurra. No confundir aprobación de requisitos con autorización de producción.

## Ejecución

| Fecha | Tarea | Archivos / comando | Resultado / pendiente |
|---|---|---|---|

## Reanudación

Última acción: spec, plan y tareas creados el 2026-10-25 en fase DOCUMENTAR. P-013-01..03 resueltas (D-061 a D-063). Siguiente: instrucción explícita de implementación. Rama prevista al implementar: `feature/013-cuidado-delegado` (D-059).

## Aceptación del usuario

Pendiente; no marcarla automáticamente después de ejecutar tests.
