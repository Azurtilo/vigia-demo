# Tareas — 002 / Renovación visual

Spec: [spec.md](spec.md). Plan: [plan.md](plan.md). Fecha: 2026-10-02.
Estado: alcance implementado; regresión verificada, T-002-13 parcialmente verificada y aceptación pendiente. Alcance completo autorizado por el propietario el 2026-10-02 mediante instrucción posterior a DOCUMENTAR.
No ejecutar código ni marcar tareas por el hecho de que estén descritas aquí.

- [x] **T-002-01 — Preparar punto de recuperación y entorno de revisión aislado.**
  - RF: RF-002-07, RF-002-09.
  - Depende de: instrucción posterior explícita de implementación.
  - Archivos previstos: archivos concretos del plan; core/test_settings.py como configuración existente, sin leer .env/DB real.
  - Hecho cuando: snapshot acotado disponible sin secretos/datos personales, estado inicial de archivos documentado y estrategia de servidor con usuarios sintéticos definida. Registrar cualquier limitación de runtime antes de probar.

- [x] **T-002-02 — Crear tokens y puente semántico Tailwind.**
  - RF: RF-002-01, RF-002-02, RF-002-09.
  - Depende de: T-002-01.
  - Archivos previstos: static/css/tokens.css (nuevo); theme/static_src/src/styles.css; templates/components/Layout/base.html.
  - Hecho cuando: única fuente editable de color, paletas/estados/foco/series definidos, carga CSS correcta y utilidades con nombres completos; cambiar valores conserva semántica sin editar clases.

- [x] **T-002-03 — Renovar estructura, tipografía y contenedores privados.**
  - RF: RF-002-01, RF-002-03, RF-002-06.
  - Depende de: T-002-02.
  - Archivos previstos: templates/components/Layout/base.html, base_extendido.html, base_pages.html; static/css/styles.css.
  - Hecho cuando: superficie clara, anchuras/espaciados/títulos coherentes, bloques preservados y sin scroll horizontal de página a 360 px. Especificidades acotadas; sin cambios de rutas.

- [x] **T-002-04 — Renovar menú, cabecera y comportamiento móvil/cuenta.**
  - RF: RF-002-02, RF-002-03, RF-002-05, RF-002-06, RF-002-07.
  - Depende de: T-002-03.
  - Archivos previstos: templates/components/navbar/*; templates/components/header/header.html y components/*; base_extendido.html; static/js/interfaz.js (nuevo si es necesario).
  - Hecho cuando: una definición de menú, selección visible, estado ARIA real, Tab/Escape/retorno de foco y bloqueo/liberación de fondo/scroll funcionan incluso al pasar a escritorio. Se conserva política y cierre por POST/CSRF.

- [x] **T-002-05 — Unificar controles y formularios crispy.**
  - RF: RF-002-02, RF-002-04, RF-002-06.
  - Depende de: T-002-02, T-002-03.
  - Archivos previstos: templates/components/btn/*, paginador.html, input_perfil.html; static/css/styles.css; UsuarioApp/forms.py solo atributos de presentación; static/js/script.js.
  - Hecho cuando: inputs/selects/errores/ayudas/botones comparten tokens y foco; selector de imagen y carga funcionan con nodos presentes/ausentes; campos, validaciones y contratos se conservan. No se parchean paquetes instalados.

- [x] **T-002-06 — Renovar listado, registro y perfil con controles coherentes.**
  - RF: RF-002-01, RF-002-04, RF-002-06, RF-002-07.
  - Depende de: T-002-04, T-002-05.
  - Archivos previstos: templates/pages/UsuarioApp/* y perfil/perfil.html; core/context_processors.py.
  - Hecho cuando: búsqueda, filtros, paginación, vacíos, errores y formulario de imagen preservados; gestión visible según helper existente, incluido superusuario sin perfil. Confirmación dice «Desactivar» y cancelarla no envía POST.

- [x] **T-002-07 — Renovar login y pantallas públicas de cuenta.**
  - RF: RF-002-01, RF-002-02, RF-002-04, RF-002-06, RF-002-07.
  - Depende de: T-002-03, T-002-05.
  - Archivos previstos: templates/account/Layout/base_simple.html; login.html, logout.html y pantallas públicas HTML de templates/account; snippets pertinentes.
  - Hecho cuando: composición de acceso adaptable, identidad coherente, errores legibles, redirect_field/CSRF preservados y registro público cerrado. Sin editar correos de texto ni añadir autenticación nueva.

- [x] **T-002-08 — Renovar cuenta interna y MFA.**
  - RF: RF-002-01, RF-002-04, RF-002-06, RF-002-07.
  - Depende de: T-002-04, T-002-05, T-002-07.
  - Archivos previstos: templates/account/Layout/base_account.html; pantallas internas de templates/account; templates/mfa/*.
  - Hecho cuando: contraseña, correo, reautenticación, TOTP y recuperación comparten el diseño y conservan formularios/acciones/condiciones allauth, incluidos estados de error. Nada sensible se usa en capturas.

- [x] **T-002-09 — Renovar mensajes, diálogos y carga accesibles.**
  - RF: RF-002-02, RF-002-04, RF-002-05, RF-002-06.
  - Depende de: T-002-04, T-002-05.
  - Archivos previstos: templates/components/mensajes.html, modal/modal.html, spinner.html, progress.html; static/css/mensajes.css, spiner.css; static/js/mensajes.js, modal.js, interfaz.js; confirmación en usuarios_lista.html.
  - Hecho cuando: mensajes largos caben en móvil, cierre con botón/teclado y anuncio adecuado; texto seguro; foco de diálogo controlado; movimiento reducido incluye animaciones y carga; sin selector global button ni errores por contenedor inexistente.

- [x] **T-002-10 — Renovar inicio y adaptar gráfico al sistema de colores.**
  - RF: RF-002-01, RF-002-02, RF-002-05, RF-002-06, RF-002-08.
  - Depende de: T-002-02, T-002-03, T-002-09.
  - Archivos previstos: templates/pages/index.html; static/js/grafico_home.js.
  - Hecho cuando: actividad real precede a demostración claramente identificada, sin nuevos datos de negocio; gráfico lee tokens, se redimensiona, respeta movimiento reducido y su fallo de carga deja la página utilizable.

- [x] **T-002-11 — Renovar las seis páginas de error.**
  - RF: RF-002-01, RF-002-02, RF-002-06.
  - Depende de: T-002-03, T-002-05.
  - Archivos previstos: templates/400.html, 401.html, 403.html, 404.html, 429.html, 500.html.
  - Hecho cuando: todas renderizan sin dependencia de perfil/sesión, tienen textos/acciones legibles y no modifican códigos HTTP o registran handlers nuevos por inferencia.

- [x] **T-002-12 — Ejecutar regresión funcional y compilación.**
  - RF: RF-002-02, RF-002-04, RF-002-07, RF-002-08.
  - Depende de: T-002-06, T-002-07, T-002-08, T-002-09, T-002-10, T-002-11.
  - Archivos previstos: UsuarioApp/tests.py, homeApp/tests.py; CSS generado por build; validation.md (nuevo al registrar resultados reales).
  - Hecho cuando: check, detección de migraciones, suite base/ampliada con core.test_settings y build standalone ejecutados; resultados/conteos reales registrados. Casos significativos de permisos directos, visibilidad de controles y filtros. Si el entorno bloquea un comando, registrar pendiente, no marcarlo como aprobado.

- [ ] **T-002-13 — Verificar interacción, accesibilidad y tres paletas en navegador.**
  - Ejecución parcial: cinco anchos en Inicio/listado, paletas, Tab/Escape/foco, cierre al pasar a escritorio, búsqueda/paginación, confirmación, perfil/imagen y consola comprobados. Pendientes: zoom real al 200 %, preferencia reducida activada en navegador y revisión visual completa de pantallas de cuenta/errores/mensajes largos. CSS y contratos JS de movimiento reducido sí comprobados; no sustituyen esa revisión. Ver validation.md.
  - RF: RF-002-01 a RF-002-09.
  - Depende de: T-002-12.
  - Archivos previstos: archivos afectados para corregir hallazgos; validation.md y capturas de datos sintéticos.
  - Hecho cuando: flujos del plan comprobados a 360/390/768/1024/1440 px, zoom 200 %, Tab/Escape/foco y movimiento reducido; paletas petróleo/ciruela/cobre aplicadas solo en tokens; contraste medido y consola sin errores de la interfaz. Capturas y límites registrados; volver a la paleta inicial tras comprobar alternativas.

- [x] **T-002-14 — Documentar personalización y ajustar orientación de la skill local.**
  - Documentación completada con la evidencia parcial de T-002-13; no se declara satisfecho su criterio completo. Guía, índices/estado/trazabilidad y skill guardados; quick_validate correcto. Aceptación del propietario pendiente.
  - RF: RF-002-09.
  - Depende de: T-002-13.
  - Archivos previstos: docs/PERSONALIZACION_VISUAL.md (nuevo); README.md; .codex/skills/frontend-design/SKILL.md; docs/ARQUITECTURA_BASE.md, DECISIONES.md, TRAZABILIDAD.md, ESTADO_PROYECTO.md; specs/README.md; validation.md.
  - Hecho cuando: guía coincide con archivo/componentes reales y explica colores/contraste/build; skill local referencia esa guía y favorece tokens sin obligar una paleta a futuros proyectos (aplicar skill-creator al editarla). Enlaces válidos, RF/evidencia/tareas reflejan lo ejecutado; aceptación estética y funcional sigue pendiente hasta declaración del propietario.

## Autorización posterior

2026-10-02: el propietario revisó los documentos y autorizó explícitamente el alcance completo de la spec 002, T-002-01 a T-002-14. Sin autorización de producción, despliegue, commit o push.

## Ejecución

2026-10-02, después de autorización: T-002-01 a 12 ejecutadas, T-002-14 completada y T-002-13 parcial. Evidencia en [validation.md](validation.md), [ESTADO_PROYECTO](../../docs/ESTADO_PROYECTO.md) y capturas de `evidencia/`.

Se preservaron los 15 métodos de la suite base (ajustando solo el título demostrativo); se añadieron 12 métodos significativos de usuarios/cuenta/inicio. Resultado: 27 pruebas OK, check sin problemas, sin cambios de migraciones y build standalone OK. Cinco comprobaciones JS separadas y contraste de tres paletas OK. Recuperación acotada conservada, sin Git en esta copia.

## Reanudación y aceptación

- [x] **Ajuste visual — 2026-10-05:** centrado horizontal de tarjetas internas Perfil/Registro/cuenta mediante `margin-inline: auto` sobre `.site-page-main > .form-panel`, con versión CSS renovada para caché. Verificado en navegador: tres pantallas, tarjetas de 640 px, desviación respecto del centro 0 px y sin desbordamiento horizontal en escritorio. Build Tailwind 4.3.0 OK; sin cambios de lógica/datos ni nuevas pruebas ejecutables. Preview ficticio detenido y pestaña cerrada; aceptación visual pendiente del propietario.

Última acción: implementación autorizada y validación/documentación de lo ejecutado. Próximo paso: completar los puntos pendientes de T-002-13 en navegador con zoom/preferencia reducida disponibles y revisar visualmente la entrega con el propietario. No apareció una decisión crítica ni migración nueva. La aceptación del usuario sigue pendiente; no se solicita nuevamente autorización de código.
