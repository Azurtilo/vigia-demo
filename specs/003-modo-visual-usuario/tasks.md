# Tareas — 003 / Modo visual por usuario

Fecha: 2026-10-02. [Spec](spec.md), [plan](plan.md).
Estado: alcance completo autorizado por instrucción posterior el 2026-10-02. T-003-01 a 06 completadas; T-003-07 parcial por verificaciones visuales pendientes; T-003-08 documentación entregada, revisión del propietario pendiente.

- [x] **T-003-01 — Preparar implementación y recuperación acotada.**
  - RF: RF-003-07.
  - Depende de: instrucción posterior explícita de implementación de 003.
  - Archivos: mapa del plan, cambios locales y entorno de prueba existentes.
  - Hecho cuando: se verifica Git/cambios del propietario de nuevo, se preservan cambios de 002, se dispone de recuperación y runtime aislado sin datos reales. No reparar .venv ni actualizar dependencias fuera de alcance.

- [x] **T-003-02 — Añadir modelo y migración de preferencia.**
  - RF: RF-003-02, RF-003-03, RF-003-07.
  - Depende de: T-003-01.
  - Archivos: UsuarioApp/models.py; migración nueva con siguiente número confirmado.
  - Hecho cuando: relación uno a uno y modo light/dark con restricciones; CreateModel sin tocar Profile/Position/User; sin creación masiva ni procesamiento de fotos. Migración y rollback comprobados solo sobre SQLite efímero.

- [x] **T-003-03 — Crear guardado de preferencia propia.**
  - RF: RF-003-02, RF-003-03, RF-003-06.
  - Depende de: T-003-02.
  - Archivos: UsuarioApp/forms.py, views.py, urls.py y tests.py.
  - Hecho cuando: POST/CSRF y activo autenticado, destino válido e idempotente, propietario exclusivamente request.user; todos los cargos activos incluidos; GET/CSRF/valores inválidos/usuarios ajenos y error de guardado probados. Retorno a Home sin next externo ni GET a URL solo POST.

- [x] **T-003-04 — Aplicar preferencia al renderizado compartido.**
  - RF: RF-003-02, RF-003-04, RF-003-07.
  - Depende de: T-003-02.
  - Archivos: core/context_processors.py, common_settings.py, templates/components/Layout/base.html; tests de usuarios/inicio.
  - Hecho cuando: modo inicial desde cuenta y atributo html validado; lectura sin filas nuevas; anónimo o ausencia de preferencia en claro; usuario sin perfil conserva su elección. Cuenta A/B y logout/login sin heredar elecciones. Processor de permisos y configuración normal/aislada conservados.

- [x] **T-003-05 — Definir tokens claros/oscuros y controles.**
  - RF: RF-003-04, RF-003-05, RF-003-07.
  - Depende de: T-003-04.
  - Archivos: static/css/tokens.css, styles.css; gráfico solo si hace falta corregir consumo; puente Tailwind si requiere clases nuevas; CSS generado mediante build.
  - Hecho cuando: colores centralizados, color-scheme adecuado, pares de marca editables y estados independientes; controles/crispy/autofill, mensajes, diálogos, carga y gráfico legibles. Composición de 002 preservada; no colores duplicados por plantilla.

- [x] **T-003-06 — Añadir botón sol/luna en Inicio.**
  - RF: RF-003-01, RF-003-04, RF-003-05, RF-003-06.
  - Depende de: T-003-03, T-003-04, T-003-05.
  - Archivos: templates/pages/index.html y estilos acotados existentes si hacen falta.
  - Hecho cuando: botón junto a acciones actuales, SVG decorativo y nombre accesible de destino; formulario con CSRF y valor explícito, funciona sin JS y ofrece acción contraria tras confirmar guardado. Error no anuncia éxito; teclado/móvil probados.

- [ ] **T-003-07 — Ejecutar regresión y validación visual.**
  - RF: RF-003-01 a RF-003-07.
  - Depende de: T-003-03 a T-003-06.
  - Archivos: UsuarioApp/tests.py, homeApp/tests.py; validation.md y evidencia sintética nuevos solo al validar.
  - Hecho cuando: suite base/ampliada, check, detección de migraciones y build aislados correctos; matriz directa y dos usuarios/sesiones/dispositivos; seis pares marca/modo, contraste, estados y gráfico; cinco anchos, teclado, JS desactivado, zoom 200 % y movimiento reducido revisados. Registrar faltantes concretos sin declararlos aprobados ni confundir pendientes históricos de 002.

- [ ] **T-003-08 — Actualizar guía, trazabilidad y entrega.**
  - RF: RF-003-07.
  - Depende de: T-003-07.
  - Archivos: docs/PERSONALIZACION_VISUAL.md, README/índice, proyecto/estado/decisiones/trazabilidad/arquitectura; documentos de 003.
  - Hecho cuando: guía coincide con implementación, migración/rollback claros y comandos/evidencia reales; estados/enlaces correctos. El propietario revisa la entrega; no marcar aceptación estética/funcional por cuenta del agente.

## Autorización posterior

Recibida: el propietario revisó spec/plan/tasks y autorizó únicamente el alcance completo de 003 el 2026-10-02. Migración real, producción, despliegue, commit y push excluidos; no ejecutados.

## Ejecución

2026-10-02: inspección y spec/plan/tasks redactados; índices, estado, proyecto, decisiones, trazabilidad y referencias actualizados. Revisión documental: 13 documentos, 106 enlaces locales válidos, cero inexistentes; siete RF y ocho tareas pendientes. Los 105 archivos de código/recursos/dependencias inventariados mantienen SHA-256 idéntico. Ninguna tarea de código ejecutada; tests, build, servidor y migraciones de 003 no ejecutados. Evidencia y siguiente paso en [ESTADO_PROYECTO](../../docs/ESTADO_PROYECTO.md).

## Reanudación

Implementación posterior: modelo/0002, endpoint/form propio, processor/HTML inicial, tokens y botón entregados. Resultados en [validation.md](validation.md): 43 pruebas Django, check, detección de migraciones, build 4.3.0, cinco contratos JS, 59 HTML y 180 contrastes correctos. Navegador: cinco anchos en ambos modos, tres marcas, teclado/foco, dos cuentas, QR y gráfico. Selector sin scripts comprobado con CSP en preview efímero.

T-003-07 parcial: faltan zoom real al 200 %, preferencia reducida activada en navegador, autofill real y revisión visual exhaustiva de estados alternativos/errores/mensajes largos. T-003-08: guía, índices, decisiones, trazabilidad y estado actualizados; revisión/aceptación del propietario pendiente. No se alteran esos criterios para declarar terminado lo no comprobado.

Siguiente paso: completar esas verificaciones visuales y revisar la entrega. Antes de usarlo sobre la base existente, acordar respaldo/entorno y autorizar allí la migración por separado; no repetir autorización de implementación de 003. Conservar pendientes históricos de 002.
