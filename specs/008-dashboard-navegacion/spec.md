# 008 — Dashboard de suscripciones y navegación coherente

Estado: implementada y verificada técnicamente; aceptación del propietario pendiente. Fecha: 2026-10-06.
Apps afectadas: homeApp, PlanesApp y componentes compartidos; no se solicita una app nueva.
Autorización posterior de implementación: alcance completo confirmado el 2026-10-06. La autorización de 007 se conserva para su alcance anterior. [Resultados y límites](validation.md).

## Necesidad y fuente

El propietario pide SVG para «Correo y verificación», «Cuenta de Google» y los cuatro enlaces de suscripciones; ocultar «Inicio» a RESTRICTED; un dashboard acorde al producto en index para ADMIN/MANAGER; y usar los mismos SVG de sol/luna de Inicio en el selector de Mi suscripción. Las cinco capturas identifican controles y diferencias existentes, no contienen instrucciones adicionales ni autorizan copiar otra identidad visual.

Inicio ya redirige a clientes, pero el menú todavía lo muestra. Su gráfico contiene datos meteorológicos demostrativos. Esta evolución sustituye esa demostración por información del prototipo de planes, conservando la base visual y la gestión de cuentas.

## Alcance

Incluye los seis SVG del menú, visibilidad de Inicio, resumen operativo de suscripciones en Home, distribución de planes, volumen mensual de operaciones monetarias simuladas y selector visual reutilizable. Mantiene los últimos cinco accesos y su definición de actividad aproximada.

No incluye modificar cargos, precios, reglas de contratación, renovación/cancelación, gestión administrativa 004/006, registro, MFA, modelos ni migraciones. No agrega pasarela, facturación, exportaciones, filtros por cliente, lista de tarjetas ajenas ni acceso al historial privado de otros usuarios. Google real y aceptación de 007 conservan sus pendientes.

## Permisos

| Actor | Inicio en menú / dashboard directo | Suscripción y cuenta propias | Cambio de modo propio |
|---|---|---|---|
| Anónimo | No; URL lleva a login | Autenticación según vistas existentes | No |
| Activo ADMIN o MANAGER | Sí, resumen global de solo lectura | Sí, contratos 007 | Sí |
| Activo RESTRICTED, sin perfil o sin cargo, sin superusuario | No; URL redirige a Mi suscripción antes de consultar agregados o usuarios | Sí, contratos 007 | Sí |
| Activo staff sin cargo y sin superusuario | No; staff no concede acceso | Sí | Sí |
| Superusuario activo, con cualquier cargo o sin perfil | Sí; conserva la excepción del helper existente | Solo sus objetos, incluso root | Sí |
| Inactivo | No; acceso directo denegado por servidor | Denegado según vistas actuales | No |

Ocultar Inicio a RESTRICTED se interpreta conforme a la política vigente de lectura: la excepción del superusuario se preserva. El nuevo resumen global solo expone agregados a lectores internos; no amplía los permisos de escritura ni la propiedad de objetos de 007.

## Requisitos funcionales

- RF-008-01: los seis enlaces señalados muestran SVG de línea, con tamaño y color coherentes con Inicio/Perfil. Correo usa sobre, Google una conexión de cuenta, Mi suscripción una credencial, Planes capas, Métodos de prueba una tarjeta e Historial un reloj. Cada icono acompaña texto visible; no se usan glifos Unicode ni imágenes externas.
- RF-008-02: Inicio solo aparece para actores autorizados por la misma política de Home, tanto en navegación de escritorio como móvil. El acceso por URL conserva login, rechazo de inactivo y redirección de clientes antes de cualquier consulta global.
- RF-008-03: index presenta «Resumen de suscripciones», fecha de actualización, aviso de simulación, métricas de suscripciones registradas de cuentas activas, períodos pagados vigentes y períodos vencidos sin cancelación; distribución por plan efectivo y volumen monetario simulado del mes actual. Los últimos accesos siguen disponibles. No se inventan porcentajes de crecimiento ni datos de ejemplo.
- RF-008-04: el resumen global respeta las fechas y cancelación de 007, usa datos persistidos de solo lectura y no crea suscripciones para cuentas antiguas. Las métricas explican su población y período; cifras cero y catálogo vacío tienen estados comprensibles.
- RF-008-05: Inicio y Mi suscripción usan los mismos SVG existentes de sol/luna y el mismo componente de formulario: estado actual, acción accesible, POST con CSRF y destino explícito light/dark. Continúa guardando exclusivamente la preferencia de la cuenta; el retorno conserva la política actual del servidor.
- RF-008-06: dashboard, menú y selector conservan tokens/layouts, foco, texto legible, funcionamiento sin JavaScript y adaptación móvil en claro/oscuro. Las acciones de usuarios mantienen flags y permisos de 004/006.

## Datos y definiciones implementadas para el dashboard

Lectura de Subscription, Plan, SimulatedOperation y los usuarios/perfiles ya usados por Home. No cambia esquema. Capturar una sola referencia temporal por respuesta, consciente de zona America/Santiago; no persistir vencimientos durante GET.

| Indicador | Definición |
|---|---|
| Suscripciones registradas | Filas Subscription cuyo usuario está activo, incluidas cuentas operadoras si tienen suscripción. Cuentas sin fila se excluyen: su Free virtual no es un registro. Mostrar esta explicación |
| Períodos pagados vigentes | Población anterior con amount_clp > 0 y end > ahora. Incluye cancelaciones programadas que aún conservan período |
| Períodos vencidos | Población anterior con amount_clp > 0, end <= ahora y cancel_at_period_end=False |
| Cancelaciones programadas | Población anterior pagada, end > ahora y cancel_at_period_end=True; dato de apoyo junto al resumen |
| Distribución por plan efectivo | Misma población registrada. Cancelación con end <= ahora cuenta como Free; vencida sin cancelación conserva plan contratado y su estado. Otras filas usan su plan. Incluir planes históricos/inactivos referenciados, sin perder registros |
| Volumen simulado del mes | Suma amount_clp de SimulatedOperation aprobadas de kind purchase/change/renew, creadas desde el inicio del mes local hasta ahora, independientemente de actividad actual de la cuenta. No contar free/cancel/resume ni rechazos. No llamarlo ingresos reales, MRR o facturación |

Distribución y total registrado deben reconciliarse. Porcentajes, si se presentan, se calculan sobre ese total y manejan cero sin división. No sumar precio actual del catálogo en sustitución de snapshots. Mantener cinco últimos accesos habilitados y actividad aproximada de diez minutos; esa sección sigue la política ya autorizada, sin añadir datos de pago personales.

## Aceptación

| RF | Dado / cuando | Resultado |
|---|---|---|
| 01 | Menú de escritorio o móvil | Seis SVG consistentes, nombres y URLs originales, iconos decorativos ocultos a lectores de pantalla |
| 02 | Cada actor de la matriz solicita Home | Menú y respuesta coherentes; clientes no ejecutan consultas del dashboard |
| 03–04 | Free, Plus vigente, Pro vencido, Hogar con cancelación vigente y cancelación terminada | Totales y distribución exactos conforme a las definiciones; no escrituras durante GET |
| 03–04 | Cuenta inactiva, cuenta sin Subscription o catálogo sin filas | Población explicada, exclusiones correctas, cero sin errores ni datos ficticios |
| 03–04 | Operaciones aprobadas/rechazadas, cambios, renovación, cancelación y límites del mes local | Solo importes y tipos previstos entran al volumen; snapshots y fechas correctos |
| 05 | Selector en ambas páginas, claro/oscuro y sin JS | Mismos SVG y etiquetas; CSRF y preferencia propia preservados; ningún cambio de cargo |
| 06 | 360/390/768/1024/1440 px, teclado y modos | Sin desbordamiento global; foco visible y tabla/gráfico alternativo comprensibles |

## Compatibilidad y decisiones

Relacionada con [007](../007-planes-app/spec.md), [003](../003-modo-visual-usuario/spec.md), [004](../004-administracion-usuarios/spec.md) y [006](../006-integridad-registro/spec.md). La lectura global agregada es explícita en esta propuesta; los objetos privados de PlanesApp continúan filtrados por titular.

Indicadores y disposición se concretaron en la propuesta documental inicial y se implementaron tras la instrucción posterior explícita de alcance completo. No se atribuyen al propietario como texto original de su pedido. [Validación](validation.md): diez pruebas nuevas y suite de 127 OK; navegador con límites manuales de zoom/movimiento reducido. Aceptación estética/funcional pendiente.

## Revisión y cambios

2026-10-06: documentación spec→plan→tasks entregada antes de código. Instrucción posterior: «implementa specs 8 Dashboard de suscripciones y navegación coherente alcance completo». Se mantiene la historia de esa fase; esta autorización permite implementación, no migraciones reales ni despliegue.
