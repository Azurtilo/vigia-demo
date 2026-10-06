# Plan técnico — 008 / Dashboard y navegación

Spec: [spec.md](spec.md). Estado: ejecutado tras autorización posterior del alcance completo el 2026-10-06. [Validación](validation.md). Las secciones de inspección/propuesta conservan el diseño previo al código.

## Inspección real

Siguiente carpeta libre comprobada: 008. Git contiene cambios y archivos nuevos de la implementación autorizada 007; se preservan. HomeView en `homeApp/views.py` es ListView con LoginRequiredMixin y dispatch que ya impide lectura global a clientes/inactivos. `core/mixins.py` concede lectura a ADMIN/MANAGER/root activo; el processor de navegación expone `puede_gestionar_usuarios` con esa regla. No crear un permiso diferente solo para la apariencia.

`templates/pages/index.html` contiene selector SVG sol/luna, últimos cinco accesos y gráfico meteorológico de ejemplo. `static/js/grafico_home.js` suministra series fijas. `templates/pages/PlanesApp/mi_suscripcion.html` usa glifos para el selector; `templates/components/navbar/nav.html` muestra Inicio incondicional y seis enlaces sin SVG. Escritorio y móvil comparten ese menú.

Leídos modelos de PlanesApp, clasificación `summary` en services.py, tests de Home, specs 003/007, arquitectura/decisiones/observaciones, guía visual y entorno. Los tokens actuales y @source son reutilizables. Skill frontend-design aplicada a esta propuesta; ninguna modificación Python/HTML/JS/CSS realizada.

## Responsabilidades e integración

Ampliar homeApp para su dashboard existente; PlanesApp conserva las reglas del negocio. Proponer `PlanesApp/dashboard.py` como servicio de agregados de solo lectura, sin endpoints propios ni dependencias nuevas. Home mantiene su guard antes de llamar a ese servicio. Mantener consulta acotada de cinco accesos en Home; no cargar todas las tarjetas ni recorrer usuarios para generar cada indicador.

Clasificación agregada con filtros ORM y agrupación condicional, basada en la misma referencia temporal de summary. No llamar ensure_subscription ni summary por usuario, pues generaría consultas repetidas y dependería de Free existente. La equivalencia con summary se prueba con escenarios controlados. Si el catálogo está vacío, el servicio devuelve resumen vacío sin crear planes ni suscripciones; si hay filas históricas, preservar su distribución aunque el plan esté inactivo.

| RF | Archivos existentes / propuestos | Integración y evidencia |
|---|---|---|
| 01–02 | Existentes: templates/components/navbar/nav.html, core/context_processors.py, homeApp/views.py | Seis SVG inline; envolver Inicio y evitar sección principal vacía según flag existente. No cambio necesario al helper. Tests por actor y menú compartido |
| 03–04 | Nuevo propuesto: PlanesApp/dashboard.py; existentes: homeApp/views.py, PlanesApp/models.py/services.py como referencia | Agregados de solo lectura con now único y fechas conscientes; tests de clasificación, sumas, límite mensual y consultas acotadas |
| 03/06 | Existentes: templates/pages/index.html, static/js/grafico_home.js | Sustituir demostración por distribución real, mantener accesos. Información numérica HTML accesible aun sin gráfico/CDN/JS |
| 05 | Nuevo propuesto: templates/components/visual_mode.html; existentes: index.html y mi_suscripcion.html | Extraer formulario actual de Inicio y reutilizarlo con mismos paths/clases/aria/CSRF; evitar IDs duplicados |
| 06 | Existentes: theme/static_src/src/styles.css, theme/static/css/dist/styles.css, layout/cache de estáticos si corresponde | Estilos semánticos acotados, build standalone y versión de recursos cuando cambien; escaneo actual cubre templates |
| Todos | Existentes: homeApp/tests.py, PlanesApp/tests.py, UsuarioApp/tests.py como regresión | Tests significativos y suite aislada; navegador en ambos modos y fallback |

## Diseño visual propuesto

Mantener Segoe UI del token `--font-ui`, lectura alineada a la izquierda y números tabulares. Escala: título 30–32 px, sección 20 px, cifra 28 px, cuerpo 16 px, ayuda 14 px; adaptar título/cifras en móvil sin reemplazar sistema tipográfico. Colores de referencia existentes: petróleo #0f766e, petróleo claro #5eead4, fondo claro #f2f5f8, superficie #ffffff, tinta #182536 y fondo oscuro #101923. Consumir variables semánticas, no copiar hexadecimales en componentes.

El foco es la distribución de los cuatro planes Vigía y el estado de sus períodos, con nombres y cantidades visibles. Resumen compacto mediante una franja de métricas con separadores; un panel principal ancho de distribución y una columna de estado/volumen mensual, seguida de accesos. Así la jerarquía responde al producto: planes como información principal, cuentas como soporte operativo. No añadir una cuadrícula de tarjetas idénticas, degradados ni crecimiento ficticio.

```text
Resumen de suscripciones                    Modo / Ver usuarios
Actualizado ... · explicación breve de simulación
[Registradas]    [Períodos vigentes]    [Vencidas]
Distribución por plan (ancho principal) | Cancelaciones programadas
Free / Plus / Pro / Hogar y cantidades  | Volumen simulado del mes
Últimos cinco accesos y actividad aproximada
```

En móvil seguir el mismo orden en una columna. Reutilizar panel/page-heading/badge/icon-button/nav-link de la base. Gráfico opcional de barras horizontales con etiquetas legibles y tabla/lista HTML equivalente siempre visible; ECharts ya existe y usa tokens, ResizeObserver y movimiento reducido. Serializar datos con json_script, nunca interpolar nombres como JavaScript. Si ECharts falla, dejar todas las cifras legibles sin dependencias del gráfico. No cargar series meteorológicas en el nuevo index.

Revisión frente al brief: se conserva la identidad y la familia SVG existente. Se descartó una cabecera con cifra grande decorativa y tarjetas repetidas porque la distribución y vencimientos explican mejor el trabajo del operador. El único punto visual destacado será la mezcla de planes; estados y controles tendrán el tratamiento sobrio de la base.

## Datos, permisos y reversión

Servicio lector sin transacciones de escritura, backfill, caché compartida de datos privados ni migraciones. La fecha se captura en servidor una vez; ventana mensual local desde el primer día a las 00:00 hasta now inclusive. Volumen usa snapshots de operaciones aprobadas de compra/cambio/renovación; no importes de catálogo ni suma de cancelaciones. La población de suscripciones usa cuentas activas con fila, también operadores con fila; no contar Free virtual.

Conservar root activo y permisos de escritura 004/006. El dashboard no ofrece enlace al historial o métodos ajenos. Las acciones propias de suscripciones y cuentas se mantienen. Selector conserva POST/CSRF y retorno actual de VisualMode; root/Admin/Manager vuelven a Inicio, clientes pasan a Mi suscripción por la redirección existente. No añadir redirección abierta.

Reversión: retirar servicio/componente nuevos y restaurar solo archivos de esta evolución desde respaldo/diff acotado; compilar si se revierten clases. No revertir cambios 007 ni tocar preferencias o suscripciones existentes. Sin migraciones ni paquetes nuevos previstos.

## Verificación después de autorización

- Datos ficticios: Free explícito, cuenta sin fila, vigentes/vencidas, cancelación antes/en/después de end, inactivos, planes inactivos y catálogo vacío. Total/distribución reconciliados y GET sin nuevas filas/cambios.
- Matriz de spec: ADMIN/MANAGER, root sin perfil/con RESTRICTED, cliente, staff sin cargo, sin perfil, anónimo e inactivo. Guard comprobado antes de llamar al servicio global.
- Operaciones: snapshot distinto al precio actual, rechazadas, límites de mes local, renewal/change y eventos sin cargo. Consultas sin crecimiento lineal por usuario.
- Selector en ambas páginas: mismo sol/luna, estado/action correctos, sin JS y rechazo de POST inválido/CSRF según base; menú con texto y SVG decorativo.
- `.venv/Scripts/python.exe manage.py test UsuarioApp homeApp PlanesApp --settings=core.test_settings`; check y makemigrations --check --dry-run con esos settings. No importar configuración de DB real.
- `.venv/Scripts/python.exe manage.py tailwind --settings=core.test_settings build`; HTML, datos json_script y fallback del gráfico/CDN bloqueado.
- Navegador 360/390/768/1024/1440 px, claro/oscuro, teclado, menú móvil, tabla, cambios de modo, estados vacíos, sin JS; zoom 200% y movimiento reducido con evidencia si herramienta permite, límites explícitos si no.

## Documentación y límites

Actualizar índice, proyecto, estado, arquitectura propuesta, decisiones y trazabilidad. En implementación registrar comandos reales en validation.md, sin reutilizar los 117 tests de 007 como evidencia nueva. No se ejecutan suite/build/migraciones en DOCUMENTAR. No se leen .env, DB ni media personal; no commit/push/despliegue.

Sin decisión crítica pendiente. La entrega documental terminó antes del código según AGENTS.md; el propietario autorizó después el alcance completo de 008. Implementación ejecutada; aceptación y revisión manual de zoom/movimiento reducido pendientes, sin repetir permisos ya recibidos.

## Ejecución posterior y ajustes acotados

Creado PlanesApp/dashboard.py, componente visual_mode.html y pruebas agrupadas en homeApp/test_dashboard.py (en lugar de mezclar diez casos nuevos en tests.py). tests.py conserva regresiones anteriores y sustituye dos expectativas del gráfico de ejemplo autorizado. Home usa un servicio lector de cuatro consultas.

CSS específico integrado en static/css/styles.css y su versión en el layout; @source existente ya cubre las fuentes nuevas y se recompiló Tailwind. Durante navegador se detectó que el sidebar podía dejar últimos enlaces fuera de una ventana baja: overflow interno acotado. Para cumplir RF-008-06, base_extendido incorpora fallback móvil details/noscript; todos sus enlaces reutilizan nav.html y la misma política. Sin reconstruir autenticación ni menú paralelo con reglas distintas.

Resultados: 127 tests, check/esquema/build, Ruff, sintaxis JS, 77 HTML y 18 capturas correctos; detalles/limitaciones en [validation.md](validation.md). Preview en memoria retirado y controles del navegador restaurados.
