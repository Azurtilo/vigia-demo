# Tareas — 008 / Dashboard y navegación

Spec: [spec.md](spec.md). Plan: [plan.md](plan.md).
Estado: tareas técnicas completas. Autorización posterior: alcance completo confirmado el 2026-10-06. Aceptación y revisión manual visual pendientes.

- [x] T-008-01 — Completar SVG y visibilidad de Inicio en el menú compartido.
  - RF: 01/02. Depende de: autorización posterior de 008.
  - Archivos: templates/components/navbar/nav.html; processor/helper solo si la inspección justifica ajuste mínimo.
  - Hecho cuando: seis iconos de línea accesibles y flag coherente en escritorio/móvil; matriz conserva root y redirecciones de clientes.
- [x] T-008-02 — Extraer y reutilizar selector de modo visual.
  - RF: 05/06. Depende de: autorización posterior de 008.
  - Archivos: nuevo componente propuesto components/visual_mode.html; index y mi_suscripcion existentes.
  - Hecho cuando: mismos SVG sol/luna, labels, POST/CSRF y destino; guardado propio y retorno actual comprobados sin JS.
- [x] T-008-03 — Implementar agregados del dashboard de solo lectura.
  - RF: 03/04. Depende de: autorización posterior de 008.
  - Archivos: nuevo PlanesApp/dashboard.py; homeApp/views.py.
  - Hecho cuando: población/estados/snapshots/fechas cumplen spec, guard antes de consultar, cero/catálogo vacío correctos, sin GET con escritura ni consultas por usuario.
- [x] T-008-04 — Componer index con resumen de planes y accesos existentes.
  - RF: 03/04/06. Depende de: 02/03.
  - Archivos: templates/pages/index.html, static/js/grafico_home.js y estilos/layout pertinentes.
  - Hecho cuando: métricas y distribución reales visibles en HTML; gráfico opcional con tokens/json_script, sin series de ejemplo; aviso mensual de simulación y accesos preservados.
- [x] T-008-05 — Verificar permisos, cálculos, selector y regresiones.
  - RF: todos. Depende de: 01–04.
  - Archivos: homeApp/tests.py, PlanesApp/tests.py si corresponde; UsuarioApp suite vigente.
  - Hecho cuando: escenarios/límites de spec comprobados con fixtures y core.test_settings; suite/check/esquema registrados, sin DB real.
- [x] T-008-06 — Compilar e inspeccionar navegación y dashboard en navegador.
  - RF: 01/02/03/05/06. Depende de: 04/05.
  - Hecho cuando: Tailwind standalone compilado; cinco anchos, modos, teclado, menú móvil y fallback sin JS/CDN con evidencia; limitaciones de zoom/reducido explícitas.
- [x] T-008-07 — Cerrar documentación técnica y entregar para aceptación.
  - RF: todos. Depende de: 05/06.
  - Hecho cuando: validation.md con evidencia real, estados/decisiones/trazabilidad actualizados y revisión solicitada al propietario. No marcar aceptación hasta respuesta expresa.

## Autorización y ejecución

2026-10-06: instrucción posterior del propietario: «implementa specs 8 Dashboard de suscripciones y navegación coherente alcance completo». Autoriza T-008-01–07 y el plan revisable entregado; no migración real, commit/push ni despliegue. Las menciones anteriores a autorización pendiente describen la fase documental previa.

Antecedente DOCUMENTAR, 2026-10-06: pedido recibido, inspección y spec→plan→tasks realizados. Ninguna tarea de código ejecutada en esa fase. La autorización anterior D-032 sigue aplicando a 007; no se presentó como autorización posterior de estos documentos.

Verificación documental: diez documentos con 165 enlaces locales válidos; 338 archivos no-Markdown conservan hashes, sin archivos añadidos/eliminados. git diff --check sin errores; avisos LF/CRLF de código anterior conservado. No pruebas funcionales de 008 ejecutadas.

## Reanudación

Última acción: implementación y verificación tras autorización explícita de 008. Siguiente: revisión del propietario y comprobación manual de zoom 200%/preferencia reducida, no disponibles nativamente en la herramienta. Migraciones reales, commit/push y despliegue no forman parte de estas tareas.

## Ejecución posterior comprobada

| Tareas | Resultado |
|---|---|
| 01/02 | SVG compartidos, visibilidad coherente con servidor y selector POST/CSRF propio; matriz y navegador correctos |
| 03/04 | Servicio de cuatro consultas, clasificación/volumen correctos, gráfico opcional y HTML accesible, accesos preservados |
| 05 | Diez tests nuevos, 127 en suite completa; 15 Home tras último ajuste, check/esquema/Ruff/JS/77 HTML OK |
| 06 | Build Tailwind, cinco anchos/dos modos/menús/teclado/fallback/vacío; límites manuales declarados, 18 capturas |
| 07 | [Evidencia y límites](validation.md), índices/estado/decisiones/trazabilidad actualizados; aceptación separada pendiente |

Ninguna tarea pendiente de implementación. La revisión manual/aceptación se conserva como pendiente explícito; no se marca realizada por suite verde. Preview temporal en memoria eliminado, pestaña cerrada y viewport restaurado.

## Aceptación del propietario

Pendiente. Tests verdes y entrega de documentos no equivalen a aceptación estética/funcional.
