# Tareas — 001 / CalidadBase

Spec: [spec.md](spec.md). Plan: [plan.md](plan.md). Fecha: 2026-09-20.
Estado: implementación y validación técnica terminadas. Implementación autorizada por el propietario el 2026-09-20.
Los cuatro cambios manuales ya aplicados se preservaron.

- [x] **T-001-01 — Extraer configuración compartida sin acceso al entorno.**
  - RF: RF-001-01, RF-001-02, RF-001-07.
  - Depende de: instrucción explícita posterior de implementación.
  - Archivos: core/settings.py existente; core/common_settings.py nuevo; UsuarioApp/tests.py existente para comprobación de configuración.
  - Hecho cuando: inventario de settings conserva valores/defaults normales, adapter, validadores, apps/MFA/middleware, correo y opcionales; entrada normal sigue siendo core.settings. La comparación antes/después usa entorno ficticio sin leer .env, y common_settings no consulta entorno ni recursos.
- [x] **T-001-02 — Crear y verificar core.test_settings aislado.**
  - RF: RF-001-01.
  - Depende de: T-001-01.
  - Archivos: core/test_settings.py nuevo; UsuarioApp/tests.py existente.
  - Hecho cuando: P-01 acredita SQLite en memoria, locmem de correo/caché, hasher rápido solo de pruebas, hosts y HTTP de pruebas, temporales con limpieza y arranque sin secretos/.env. La prueba falla si se intenta leer .env; no se importa core.settings. No se usan DB ni media reales.
- [x] **T-001-03 — Probar cierre del registro público.**
  - RF: RF-001-02.
  - Depende de: T-001-02.
  - Archivos: UsuarioApp/tests.py; inspección de UsuarioApp/adapters.py y configuración compartida, sin reemplazar su conexión en tests.
  - Hecho cuando: P-02 resuelve el adapter real y verifica GET/POST sin altas de User/Profile/EmailAddress; cierre no explicado por errores ajenos como HTTPS, CSRF o 500. Código HTTP observado queda documentado.
- [x] **T-001-04 — Probar autorización GET/POST del registro interno.**
  - RF: RF-001-03.
  - Depende de: T-001-02.
  - Archivos: UsuarioApp/tests.py; core/mixins.py, UsuarioApp/views.py y rutas como código bajo prueba.
  - Hecho cuando: P-03/P-04 cubren toda la matriz, superusuario sin perfil y sin cargo, inactivo incluso superusuario, y staff sin cargo. Diferenciar denegación por sesión y por helper/mixin; denegados no crean registros.
- [x] **T-001-05 — Probar formularios y alta completa con datos ficticios.**
  - RF: RF-001-01, RF-001-04.
  - Depende de: T-001-02, T-001-04.
  - Archivos: UsuarioApp/tests.py; formularios/modelos/vistas existentes bajo prueba.
  - Hecho cuando: P-05/P-06 acreditan alta por cada actor permitido, contraseña, vínculos, cargo y ausencia de privilegios inyectados; entradas inválidas/username duplicado/cargo excluido/carga inválida no crean User/Profile. Archivos sintéticos quedan solo en temporales. No se añade unicidad interna de email ni se asume significado de pk=1.
- [x] **T-001-06 — Unificar autorización del enlace Registro.**
  - RF: RF-001-03, RF-001-05.
  - Depende de: T-001-01, T-001-04.
  - Archivos: core/context_processors.py nuevo; core/common_settings.py propuesto por T-001-01; templates/components/navbar/nav.html existente; UsuarioApp/tests.py y homeApp/tests.py.
  - Hecho cuando: processor llama a usuario_tiene_cargo con la política de PermitsPositionMixin.permisos, plantilla consume el booleano y mantiene rutas/estructura. P-04/P-07 prueban acceso y href para todos los actores, incluidos superusuarios sin perfil/cargo; contenedores móvil/escritorio coherentes, sin duplicar listas de roles.
- [x] **T-001-07 — Ampliar patrones Tailwind a fuentes propias.**
  - RF: RF-001-06.
  - Depende de: autorización posterior; T-001-06 antes de la compilación final.
  - Archivos: theme/static_src/tailwind.config.js existente.
  - Hecho cuando: HTML actual cubierto, JS/Python propios incluidos, resolución de rutas definida, entornos/dependencias/staticfiles/generados excluidos según plan; se documenta mantenimiento de raíces y clases completas/safelist.
- [x] **T-001-08 — Comprobar compilación y alcance del escaneo.**
  - RF: RF-001-06, RF-001-07.
  - Depende de: T-001-07.
  - Archivos: CSS generado theme/static/css/dist/styles.css; fuentes testigo temporales en raíces propias/excluidas, retiradas al terminar; package.json/package-lock.json existentes conservados.
  - Hecho cuando: npm ci y npm run build ejecutados desde theme/static_src; P-08 muestra clases testigo HTML/JS/Python incluidas y controles excluidos ausentes. Compilación final sin testigos y clases del formulario presentes; registrar resultados, no solo exit code.
- [x] **T-001-09 — Ejecutar regresiones y revisión en navegador.**
  - RF: RF-001-01 a RF-001-07.
  - Depende de: T-001-03, T-001-05, T-001-06, T-001-08.
  - Archivos: homeApp/tests.py y UsuarioApp/tests.py; templates existentes bajo validación; sin cambios funcionales ajenos al alcance.
  - Hecho cuando: P-09 y suite completa con --settings=core.test_settings, check y makemigrations --check --dry-run tienen resultados registrados y número real de casos mayor que cero. Navegador sobre instancia aislada verifica menú móvil/escritorio, teclado, navegación y gráfico de ejemplo; opcionales/correo/ajustes manuales conservados. Fallos se corrigen con regresión dentro de RF, sin cambiar requisitos para ocultarlos.
- [x] **T-001-10 — Registrar evidencia y actualizar estado documental.**
  - RF: RF-001-01 a RF-001-07.
  - Depende de: T-001-09.
  - Archivos: validation.md futuro en esta carpeta; tasks.md; specs/README.md; docs/ESTADO_PROYECTO.md, TRAZABILIDAD.md, ARQUITECTURA_BASE.md, OBSERVACIONES_BASE.md, ENTORNO_Y_VERIFICACION.md y DECISIONES.md cuando corresponda.
  - Hecho cuando: resultados reales por P/RF, comandos, versiones, archivos y límites registrados; rutas propuestas distinguidas de las creadas; diff final acotado. Solo tareas efectivamente verificadas se marcan hechas; aceptación funcional queda pendiente del propietario.

## Ajuste solicitado el 2026-09-22

- [x] **T-001-11 — Hacer reproducible Tailwind 4 standalone.**
  - RF: RF-001-06.
  - Archivos: `requirements.txt`, `core/common_settings.py`.
  - Hecho cuando: django-tailwind/pytailwindcss y Tailwind 4.3.0 quedan fijados; el modo standalone es explícito y no requiere Node.js.
- [x] **T-001-12 — Trasladar el escaneo a configuración CSS-first.**
  - RF: RF-001-06.
  - Depende de: T-001-11.
  - Archivos: `theme/static_src/src/styles.css`, CSS generado.
  - Hecho cuando: las raíces propias y exclusiones quedan expresadas con `@source`; no se restaura `tailwind.config.js`; el build termina correctamente y genera Tailwind 4.3.0.
- [x] **T-001-13 — Corregir documentación y detalle de pruebas por RF.**
  - RF: RF-001-06, RF-001-07.
  - Depende de: T-001-12.
  - Archivos: documentos transversales, spec/plan/tasks/validation y trazabilidad.
  - Hecho cuando: no quedan instrucciones npm/Tailwind 3 vigentes, `ROADMAP.md` no autoriza trabajo, `VERIFICACION.md` distingue historia y estado actual, y trazabilidad nombra/contabiliza métodos asociados sin confundir asociaciones con cobertura.

## Autorización posterior

Concedida por el propietario el 2026-09-20 para T-001-01 a T-001-10 y el 2026-09-22 para documentar, implementar y verificar T-001-11 a T-001-13. No autorizó despliegue, commit ni push.

## Ejecución

| Fecha | Tarea | Archivos / comando | Resultado / pendiente |
|---|---|---|---|
| 2026-09-20 | Preparación documental; no es tarea de implementación | spec.md → plan.md → tasks.md y documentos relacionados | Documentación redactada; todas las tareas T-001 permanecen pendientes |
| 2026-09-20 | T-001-01 a T-001-06 | Configuración, tests, processor y navegación | Implementado; 15 pruebas OK |
| 2026-09-20 | T-001-07 a T-001-08 | tailwind.config.js, npm ci, testigos temporales y npm run build | Build OK; JS/Python incluidos y migraciones excluidas; testigos retirados |
| 2026-09-20 | T-001-09 | check, migraciones, suite y navegador | Todo OK; escritorio y móvil verificados con DB temporal |
| 2026-09-20 | T-001-10 | validation.md y documentación transversal | Completado; aceptación del propietario pendiente |
| 2026-09-22 | T-001-11 a T-001-12 | Dependencias, configuración standalone, `@source` y build | Tailwind 4.3.0; testigos JS/Python incluidos, migración excluida; build final limpio |
| 2026-09-22 | T-001-13 | Documentación y trazabilidad | Coherencia revisada; pruebas asociadas y conteo por RF registrados |

## Reanudación y aceptación

Última acción: ajuste Tailwind 4 y documentación verificados el 2026-09-22. Siguiente paso: revisión/aceptación funcional del propietario. No hay bloqueos técnicos. La aprobación previa de la documentación y del trabajo no se interpreta automáticamente como aceptación de los resultados finales.
