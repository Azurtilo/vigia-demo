# Tareas — 014 / Privacidad de datos de salud

Spec: [spec.md](spec.md). Plan: [plan.md](plan.md).
Estado: propuestas. Implementación autorizada: NO.
No ejecutar tareas de código por el hecho de aparecer aquí.

- [ ] T-014-01 — App `PrivacidadApp` con `AccountConsent`, `PatientConsent` y `PrivacyOperation`, ajuste `PRIVACY_POLICY_VERSION` y migración inicial.
  - RF: RF-014-02, 04, 13. Componente: web.
  - Depende de: ninguna.
  - Archivos previstos: `web/PrivacidadApp/` (apps, models, migrations), `web/core/common_settings.py`.
  - Hecho cuando: `makemigrations --check` sin cambios pendientes; restricción de un consentimiento vigente por paciente y alcance probada; avance y reversión de la migración en SQLite temporal.
- [ ] T-014-02 — Política pública versionada y página de aceptación.
  - RF: RF-014-01. Componente: web.
  - Depende de: T-014-01.
  - Archivos previstos: `web/PrivacidadApp/views.py`, `urls.py`, `web/templates/pages/PrivacidadApp/`, `web/core/urls.py`.
  - Hecho cuando: la política responde 200 sin sesión y muestra versión y fecha; el texto se marca como borrador pendiente de revisión.
- [ ] T-014-03 — Aceptación en el registro y puerta de consentimiento en web y API.
  - RF: RF-014-02, 03. Componente: web.
  - Depende de: T-014-02.
  - Archivos previstos: `web/UsuarioApp/signup_forms.py`, `web/PrivacidadApp/middleware.py`, `web/core/common_settings.py`, `web/CuidadosApp/api/base.py`.
  - Hecho cuando: registro sin aceptar falla; versión antigua redirige en web y da 403 `consent_required` en API; rutas exentas (cerrar sesión, recuperar contraseña, verificar correo, política, estáticos) funcionan; suites existentes ajustadas sin relajar la regla.
- [ ] T-014-04 — Consentimiento del paciente al crearlo, bloqueos por alcance y revocación.
  - RF: RF-014-04, 05, 06, 07. Componente: web.
  - Depende de: T-014-01.
  - Archivos previstos: `web/PrivacidadApp/consent.py`, `web/CuidadosApp/forms.py`, `services.py`, `capacity.py`, `api/views.py`, `api/detection.py`, ficha web.
  - Hecho cuando: los criterios RF-014-04..07 pasan, incluido el nodo con consentimiento de detección revocado (403 en `edge/status`).
- [ ] T-014-05 — Exportación JSON de cuenta y de paciente.
  - RF: RF-014-09, 10, 13. Componente: web.
  - Depende de: T-014-01.
  - Archivos previstos: `web/PrivacidadApp/export.py`, vistas y plantillas de perfil y ficha.
  - Hecho cuando: el contenido coincide con la spec; no aparecen `token`, `session_key`, `credential_hash` ni datos de otro titular; familiar y cuidador reciben 403 en la exportación del paciente.
- [ ] T-014-06 — Eliminación de paciente.
  - RF: RF-014-11, 13. Componente: web.
  - Depende de: T-014-01.
  - Archivos previstos: `web/PrivacidadApp/erase.py`, vista y confirmación en la ficha.
  - Hecho cuando: nombre incorrecto rechaza; nombre correcto borra el paciente y todas las filas que lo referencian (prueba que recorre las relaciones), con correcciones encadenadas; cupo liberado.
- [ ] T-014-07 — Eliminación de cuenta con anonimización.
  - RF: RF-014-12, 13. Componente: web.
  - Depende de: T-014-06.
  - Archivos previstos: `web/PrivacidadApp/erase.py`, vista en el perfil, `web/CuidadosApp/api/views.py` (`event_data`), plantilla de historial.
  - Hecho cuando: contraseña incorrecta rechaza; titular y cuidador eliminados según la spec; registros ajenos con «Cuenta eliminada»; sin inicio de sesión, sesiones ni dispositivos activos; imagen de perfil borrada.
- [ ] T-014-08 — Plazos de conservación y comando de purga.
  - RF: RF-014-08. Componente: web.
  - Depende de: T-014-06.
  - Archivos previstos: `web/PrivacidadApp/retention.py`, `management/commands/purge_expired_data.py`.
  - Hecho cuando: con datos vencidos y vigentes de cada tipo, `--dry-run` solo reporta y la ejecución borra solo lo vencido; la salida no contiene datos personales.
- [ ] T-014-09 — App móvil: aviso `consent_required`, consentimiento al crear paciente y enlaces del perfil.
  - RF: RF-014-03, 04, 14. Componente: mobile.
  - Depende de: T-014-03, T-014-04.
  - Archivos previstos: `mobile/lib/core/api.dart`, `mobile/lib/features/home/care_home.dart` (alta de paciente), `mobile/lib/features/profile/profile_panel.dart`, pruebas en `mobile/test/`.
  - Hecho cuando: `flutter analyze` sin problemas y pruebas de widget del aviso y del alta con representante.
- [ ] T-014-10 — Validación integrada y documentación.
  - RF: todos. Componentes: web, mobile y edge (regresión).
  - Depende de: T-014-01..09.
  - Hecho cuando: suites verdes con conteos reales; revisión en navegador y en Android; `validation.md`, TRAZABILIDAD, ESTADO, DECISIONES (P-014-01..04) y guías actualizados.

## Autorización posterior

Pendiente. Registrar mensaje/fecha y tareas autorizadas solo cuando ocurra. No confundir aprobación de requisitos con autorización de producción.

## Ejecución

| Fecha | Tarea | Archivos / comando | Resultado / pendiente |
|---|---|---|---|

## Reanudación

Última acción: spec, plan y tareas creados el 2026-10-25 en fase DOCUMENTAR. Siguiente: respuestas del propietario a P-014-01..04 e instrucción explícita de implementación. Rama: `feature/014-privacidad`.

## Aceptación del usuario

Pendiente; no marcarla automáticamente después de ejecutar tests.
