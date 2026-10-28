# Tareas — 018 / Usabilidad del portal

Spec: [spec.md](spec.md). Plan: [plan.md](plan.md).
Estado: T-018-01..03 hechas; T-018-04..07 pendientes. Implementación autorizada: SÍ, T-018-01..07 (2026-10-27), sin despliegue; el merge de la PR requiere autorización aparte.
Rama: `feature/018-usabilidad-portal` desde `develop`, un commit por tarea y PR hacia `develop` (D-059).

- [x] T-018-01 — Documentos y línea base.
  - RF: todos (regresión).
  - Depende de: autorización.
  - Archivos previstos: `specs/018-usabilidad-portal/*`, `specs/README.md`, `docs/DECISIONES.md` (D-078..D-080).
  - Hecho cuando: spec, plan y tareas están en la rama; la suite Django pasa sin cambios de código y su conteo queda en `validation.md`.
- [x] T-018-02 — Indicadores de contraseña.
  - RF: RF-018-01, RF-018-02, RF-018-03, RF-018-04.
  - Depende de: T-018-01.
  - Archivos previstos: `UsuarioApp/password_rules.py`, `UsuarioApp/account_forms.py`, `UsuarioApp/signup_forms.py`, `UsuarioApp/forms.py`, `core/common_settings.py`, `templates/components/password_checklist.html`, las seis plantillas, `static/js/contrasena.js`, `static/css/styles.css`, `components/Layout/base.html`, `UsuarioApp/tests.py`.
  - Hecho cuando: las pruebas comprueban que las reglas salen de los validadores, que la ayuda de Django ya no aparece, que cada código rechazado por el servidor se marca en la lista, que los seis formularios la muestran y que la contraseña no queda en el HTML.
- [x] T-018-03 — Política de privacidad legible.
  - RF: RF-018-05, RF-018-06, RF-018-07.
  - Depende de: T-018-01.
  - Archivos previstos: `templates/pages/PrivacidadApp/politica.html`, `static/css/styles.css`, `PrivacidadApp/tests.py`.
  - Hecho cuando: las pruebas comprueban el índice con enlaces a cada sección y las salidas con y sin sesión; el contenido y la versión no cambian.
- [ ] T-018-04 — Páginas de cuenta con salida.
  - RF: RF-018-08, RF-018-09, RF-018-10.
  - Depende de: T-018-01.
  - Archivos previstos: `templates/account/Layout/base_simple.html`, `templates/account/{email,logout,verification_sent,email_confirm,verified_email_required,password_reset_done,password_reset_from_key,password_reset_from_key_done,account_inactive}.html`, `UsuarioApp/tests.py`.
  - Hecho cuando: las pruebas comprueban el menú en correos y cerrar sesión con sesión, cada salida de la tabla de RF-018-09 y el destino del logo con y sin sesión.
- [ ] T-018-05 — Historial del navegador y modo visual.
  - RF: RF-018-11, RF-018-12, RF-018-13.
  - Depende de: T-018-04 (comparten `email.html`).
  - Archivos previstos: `core/navigation.py`, `core/common_settings.py`, `static/js/historial.js`, `components/Layout/base.html`, plantillas con formularios marcados, `components/visual_mode.html`, `UsuarioApp/views.py`, pruebas en `UsuarioApp/tests.py` y `CuidadosApp`.
  - Hecho cuando: las pruebas del middleware cubren redirección interna con y sin cabecera, redirección externa, GET y formulario con errores; las del modo visual cubren `next` interno, externo y vacío; los formularios de exportación no están marcados.
- [ ] T-018-06 — Textos en español tuteado.
  - RF: RF-018-14, RF-018-15.
  - Depende de: T-018-02, T-018-04 y T-018-05 (tocan las mismas plantillas).
  - Archivos previstos: `templates/account/**`, `templates/account/messages/*.txt`, `templates/mfa/**` si hace falta, plantillas de `UsuarioApp`, `UsuarioApp/account_forms.py` (`LoginForm`), `UsuarioApp/forms.py`, prueba de textos.
  - Hecho cuando: la prueba que renderiza las páginas de cuenta con y sin sesión no encuentra frases en inglés ni fórmulas de «usted» de su lista.
- [ ] T-018-07 — Verificación y cierre documental.
  - RF: todos.
  - Depende de: T-018-02..06.
  - Archivos previstos: `specs/018-usabilidad-portal/validation.md`, `docs/ESTADO_PROYECTO.md`, `docs/TRAZABILIDAD.md`, `specs/README.md`.
  - Hecho cuando: pasan Django completo, `check`, `makemigrations --check` y `tailwind build`; la PR tiene CI verde; `validation.md` registra lo comprobado en el navegador y lo que quedó pendiente.

## Registro de ejecución

| Fecha | Tarea | Resultado |
|---|---|---|
| 2026-10-27 | T-018-01 | Spec, plan, tareas y D-078..D-080. Django 247 OK sin cambios de código |
| 2026-10-27 | T-018-02 | `PasswordRulesMixin` en los seis formularios, lista en vivo y mensaje único de coincidencia. 6 pruebas nuevas, 4 mutaciones detectadas. Django 253 OK. JavaScript sin verificar en navegador (T-018-07) |
| 2026-10-27 | T-018-03 | Política con secciones, índice, aviso destacado y salidas según la sesión; texto original intacto (comparado párrafo a párrafo). 3 pruebas nuevas |
