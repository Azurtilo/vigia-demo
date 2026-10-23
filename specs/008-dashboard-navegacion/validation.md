# Validación — 008 / Dashboard y navegación

Fecha: 2026-10-06. Alcance completo autorizado por instrucción posterior: «implementa specs 8 Dashboard de suscripciones y navegación coherente alcance completo». Implementación técnica terminada; aceptación estética/funcional del propietario pendiente.

## Cambios entregados

Seis SVG de línea en navegación; Inicio condicionado por la política ADMIN/MANAGER/root activo del servidor. Ambos menús comparten nav.html, sin sección principal vacía para clientes. Correo/Google también identifican página activa.

Home incorpora [dashboard.py](../../web/PlanesApp/dashboard.py) con cuatro consultas independientes del número de usuarios. Cuenta filas de cuentas activas, períodos pagados vigentes/vencidos, cancelaciones pendientes y plan efectivo. La cancelación terminada entra en Free sin guardar cambios. Cuentas antiguas sin fila no se crean durante lectura. Volumen del mes usa snapshots de compras/cambios/renovaciones aprobadas, excluye rechazos/eventos sin cargo y respeta inicio de mes en Santiago. No muestra datos de métodos/historial ajenos.

Index sustituye meteorología demostrativa por gráfico opcional de distribución de planes y cifras HTML siempre disponibles. Mantiene cinco accesos y actividad aproximada de diez minutos. json_script evita inyección de nombres en JavaScript. No nuevas dependencias ni modelos/migraciones/rutas de producto.

[Selector compartido](../../web/templates/components/visual_mode.html) extraído de Inicio y usado en Mi suscripción; mismos SVG, estilos, labels y POST/CSRF. Preferencia propia y retorno del servidor conservados. Layout añade details dentro de noscript para menú móvil nativo cuando no hay JavaScript; oculta el botón de diálogo inoperante solo en ese caso. Sidebar de escritorio puede desplazarse para alcanzar los últimos enlaces en ventanas bajas. Colores/fuentes de la base preservados; versión de CSS/JS actualizada.

## Verificación ejecutada

Entorno: `.venv/Scripts/python.exe`, `core.test_settings`, SQLite en memoria y datos ficticios. No se importó core.settings normal, leyó .env/DB/media personal ni migró una base real.

| Comando / comprobación | Resultado |
|---|---|
| manage.py test UsuarioApp homeApp PlanesApp --settings=core.test_settings | **127 tests OK, 12,153 s**; diez nuevos de dashboard y dos regresiones Home actualizadas por la sustitución autorizada del gráfico |
| manage.py test homeApp --settings=core.test_settings, después del último cambio de templates y formato | **15 tests OK, 0,261 s** |
| manage.py check --settings=core.test_settings | Sin incidencias |
| manage.py makemigrations --check --dry-run --settings=core.test_settings | No changes detected |
| manage.py tailwind --settings=core.test_settings build | Tailwind standalone 4.3.0, correcto; compilación final 69 ms |
| python -m ruff check PlanesApp/dashboard.py homeApp/views.py homeApp/test_dashboard.py | Correcto; aliases re.S corregidos a re.DOTALL y archivos nuevos formateados |
| Node bundled --check static/js/grafico_home.js | Sintaxis correcta |
| Carga de plantillas mediante Django | 77 HTML, sin errores |
| Inspección de evidencias con Pillow, sin editar imágenes | 18 JPEG válidos, dimensiones registradas |
| Verificación documental final | 237 enlaces locales de trece documentos, todos válidos; git diff --check sin errores (avisos LF/CRLF de archivos preservados/documentación) |
| Hashes frente al estado anterior de 338 archivos no-Markdown | Sin eliminaciones; once archivos anteriores cambiados, todos del alcance 008. Dependencias/auth/servicios 007 preservados |

Suite incluye fallos sintéticos esperados, respuestas 400/403/404/500 y trazas de rollback de pruebas anteriores; el resultado final de la ejecución fue OK, no un fallo del producto. No nueva auditoría independiente de producción ni certificación de otro motor.

[Resultados estructurados](evidencia/verificacion.json), [navegador](evidencia/navegador.json) y registro documental `evidencia/documentacion.json`.

## Casos de servidor comprobados

- Matriz ADMIN/MANAGER/RESTRICTED, staff sin cargo, perfil ausente/sin cargo, root sin perfil/con RESTRICTED, anónimo e inactivo. Guard de Home evita llamar al agregado y consultar accesos globales para clientes; URL y visibilidad del menú coherentes.
- Free explícito, cuenta sin fila, cuenta inactiva, plan histórico inactivo, catálogo vacío, frontera exacta de cancelación, períodos vencidos. Distribución coincide con summary por cuenta y suma al total registrado. Filas no cambian al leer.
- Límite mensual local inclusive, un microsegundo anterior y posterior al instante actual, aprobada/rechazada, compra/cambio/renovación y free/cancel/resume. Operaciones históricas de cuentas ahora inactivas incluidas según spec; snapshot prevalece sobre precio actual.
- Cuatro consultas tanto con cero como con veinte suscripciones. Selector en ambas páginas, dos modos, persistencia exclusiva por actor, POST inválido y CSRF rechazados sin alterar preferencia. Nombres de plan con cierre de script serializados/escapados correctamente.
- Regresiones de usuarios, registro, MFA, Google y suscripciones 007 en suite completa. Propiedad de objetos y jerarquía administrativa no modificadas.

## Navegador y diseño

Preview local 127.0.0.1:8008 con core.test_settings y SQLite en memoria, retirado al terminar. Se crearon solo cuentas ficticias. Datos de demostración: 24 filas activas, 12 períodos pagados vigentes, tres vencidos, dos cancelaciones pendientes y $149.850 CLP simulado; luego se ensayó vacío con ceros.

Dashboard a **360/390/768/1024/1440 px, claro y oscuro**: sin desbordamiento horizontal de página, gráfico real visible, cuatro filas de planes, cifras legibles y orden móvil en una columna. La tabla conserva su desplazamiento contenido. Se inspeccionaron capturas, no solo medidas DOM. ADMIN/MANAGER acceden; cliente redirige a Mi suscripción y tiene cero enlaces nav «Inicio» en ambos modos. Sus SVG sol/luna son los del componente compartido.

Menú móvil: seis iconos y texto, foco inicial en Cerrar menú, Escape con cierre tras animación y foco devuelto a Abrir menú. Cifras/lista accesibles sin ECharts: preview sin scripts CDN provoca degradación visible. Preview sin recursos JavaScript y con marcado noscript activo conserva cantidades, permite POST de modo oscuro y menú details nativo con trece enlaces para ADMIN.

**Método del fallback:** se retiraron los scripts al servir HTML y se activó la rama noscript en el preview aislado. No se cambió una preferencia global JavaScript del navegador. No afirmar que se probó el motor con JavaScript deshabilitado nativamente; sí se verificaron los controles HTML sin ejecución de recursos de la app.

Capturas representativas: [dashboard final](evidencia/dashboard-final.jpg), [claro escritorio](evidencia/dashboard-claro-1440.jpg), [oscuro escritorio](evidencia/dashboard-oscuro-1440.jpg), [móvil](evidencia/dashboard-oscuro-390.jpg), [menú cliente](evidencia/menu-cliente-390.jpg), [cliente oscuro](evidencia/cliente-oscuro-1440.jpg), [sin CDN](evidencia/dashboard-sin-cdn-390.jpg), [sin recursos JS](evidencia/dashboard-sin-js-390.jpg), [estado vacío](evidencia/dashboard-vacio-1440.jpg).

## Conservación, cierre y pendientes

Cambios anteriores 007 preservados, sin commit/push/despliegue. Preview detenido, pestaña creada cerrada, viewport restaurado y .work-008 retirado comprobando ruta absoluta dentro del workspace. Dependencias y tokens no modificados; generado Tailwind actualizado.

La herramienta no ofrece emulación nativa de zoom 200% o prefers-reduced-motion; se mantienen reglas CSS y matchMedia/animación reactiva del gráfico, pero su inspección con esas preferencias queda manual. No sustituirla por cambiar solo el tamaño del viewport. Aceptación del propietario pendiente. Google real/migración real de 007 siguen fuera de esta entrega.

Reversión acotada: restaurar solo los once archivos anteriores afectados por 008 y retirar los tres archivos nuevos de producto (servicio, tests y componente), manteniendo 007; compilar si se revierten estilos. No revertir tablas ni borrar suscripciones/preferencias. Índice/estado/trazabilidad deben acompañar cualquier reversión.
