# 007 — PlanesApp: registro público y suscripciones simuladas

Fecha: 2026-10-06. Estado: implementada; servidor verificado y revisión visual con límites.
Módulo Django solicitado: **PlanesApp**. Implementación autorizada: **SÍ, alcance completo por instrucción posterior**; aceptación funcional del propietario pendiente. [Validación](validation.md).

## Necesidad y fuente

Convertir esta copia de la base en un prototipo donde cualquier persona pueda registrarse con Google o correo/contraseña, quede automáticamente con cargo RESTRICTED y contrate una suscripción. Reutilizar UsuarioApp, allauth, tema y navegación. Las cuatro capturas son referencias funcionales y de interacción, no instrucciones ni diseños para copiar.

El propietario confirmó el 2026-10-06: ambos medios de registro; planes/precios de las imágenes; mensualidad simulada, cambio inmediato sin prorrateo, cancelación al finalizar período; verificar correo antes de contratar y probar confirmación con correo local. Posteriormente autorizó explícitamente implementar todo 007 y aclaró que el entorno de esta copia se llama .venv. Esa instrucción incluye las precisiones técnicas de este alcance; no autoriza despliegue ni migraciones sobre la DB existente.

## Alcance

Registro/inicio/confirmación de correo y conexión explícita con Google mediante allauth; catálogo público; resumen propio; métodos de pago ficticios; tarjeta visual con datos en vivo y giro al CVC; revisión y confirmación de compra/cambio; resultado exitoso o rechazado; cancelación y retiro de cancelación antes del vencimiento; historial y detalle HTML de operaciones simuladas. Renovación mensual demostrable sin cargos reales. Configuración inicial de catálogo/cargo por migraciones propuestas, sin un nuevo panel comercial.

No incluye cámaras reales, eventos, detección, SMS, notificaciones push, almacenamiento, app móvil ni sincronización: los beneficios se muestran como contenido de catálogo del prototipo, sin afirmar que funcionan. No incluye pasarela, Stripe SDK, tarjetas reales, facturas tributarias, PDF, devoluciones reales, cupones, planes anuales, equipos familiares operativos, APIs móviles, correo SMTP de producción, despliegue, commits/push o aplicación de migraciones a la base existente. Un eventual pago real requiere otro alcance y no puede reutilizar el formulario simulado para captar tarjetas reales.

## Catálogo inicial confirmado

Moneda propuesta: CLP, coherente con precios y contexto es-cl. Valores enteros sin decimales. Son los totales de demostración: no calcular impuestos ni cargos adicionales no acordados.

| Plan | Valor mensual | Descripción | Beneficios mostrados |
|---|---:|---|---|
| Vigía Free | Gratis ($0) | Para empezar a vigilar lo esencial | 1 cámara conectada; alertas por correo electrónico; historial de eventos: 24 horas; acceso desde la app web |
| Vigía Plus | $4.990 | Monitoreo activo para tu día a día | Hasta 3 cámaras conectadas; notificaciones push instantáneas; historial de eventos: 7 días; detección de movimiento; acceso desde la app web y móvil |
| Vigía Pro | $9.990 | Vigilancia sin límites, con prioridad | Cámaras conectadas ilimitadas; notificaciones push + SMS; historial de eventos: 30 días; detección de personas y vehículos; soporte prioritario 24/7 |
| Vigía Hogar | $14.990 | Toda la familia, una sola torre de vigilancia | Todo lo incluido en Vigía Pro; hasta 5 perfiles familiares; almacenamiento en la nube: 60 días; panel de control compartido; soporte prioritario 24/7 |

No asumir que Vigía es el nombre comercial definitivo del sitio. Mostrar «Tu plan» según datos; Plus puede destacarse visualmente, pero no mostrar «Más elegido» como estadística real sin evidencia.

## Actores y permisos propuestos

Todas las acciones privadas requieren cuenta activa. «Propio» significa filtrar por usuario de sesión en servidor, aun para ADMIN/MANAGER/root. Cargo y plan son independientes: comprar nunca cambia RESTRICTED.

| Acción | Anónimo | RESTRICTED activo | ADMIN/MANAGER activos | Activo sin perfil/cargo | Superusuario activo |
|---|---|---|---|---|---|
| Consultar catálogo | Sí | Sí | Sí | Sí | Sí |
| Registro público | Sí, local o Google | No crear segunda cuenta autenticada | Igual | Igual | Igual |
| Resumen/historial propios | Login requerido | Sí | Sí, solo propios | Sí, sin crear perfil por GET | Sí, solo propios |
| Métodos, compra/cambio/renovación | No | Propios, correo verificado | Propios, correo verificado | Propios, correo verificado | Propios, correo verificado |
| Cancelar/retirar cancelación propia | No | Sí | Sí | Sí | Sí |
| Ver datos/operaciones de otro cliente | No | No | No en este módulo | No | No por las vistas de cliente |
| Listado Usuarios e Inicio con cuentas recientes | No | No | Sí | No, salvo root | Sí mediante helper actual |
| Registro interno/activar/desactivar/reset | No | No | Política 006/004 actual | No | Política 006/004: cargo requerido |

La fila de Usuarios/Inicio es un ajuste propuesto necesario al abrir la base: actualmente basta LoginRequiredMixin. RESTRICTED/sin cargo se redirigen desde Home a Mi suscripción antes de consultar cuentas; el listado devuelve 403 para autenticados sin permiso. La navegación debe coincidir. Root conserva la excepción de core.mixins para **lectura interna**, sin ampliar Registro/gestión de 004/006. is_staff por sí solo no concede esos permisos. Inactivos no leen/escriben datos privados; sesión rechazada puede redirigir a login.

## Flujos y páginas

1. Visitante abre catálogo, elige plan e inicia sesión o crea cuenta. Se conserva solo un destino local validado; nunca se contrata desde GET ni se redirige a sitios arbitrarios.
2. Alta pública crea User + Profile RESTRICTED + suscripción Free en forma indivisible. Local solicita username, correo y contraseña con validadores actuales; Google puede generar username único. Sin selector de cargo, flags staff/root ni imagen remota importada automáticamente.
3. Local confirma correo por enlace allauth probado en backend local. Cuenta Google nueva debe traer correo verificado por proveedor; de faltar, requiere confirmación local. Resumen/Free se pueden ver mientras se confirma; métodos y contratación se bloquean hasta entonces. Las cuentas internas existentes conservan login/MFA; para contratar aplican también verificación.
4. Cliente abre Mi suscripción: plan efectivo, valor, beneficios, estado, período y siguiente renovación/cancelación. Sin servicios de cámaras, no inventar cantidad de cámaras conectadas reales.
5. Agrega tarjeta **de prueba**: titular, número permitido, MM/AA, CVC; vista en vivo, giro y validación. Guarda solo representación enmascarada y escenario ficticio; no número completo/CVC.
6. Revisa plan, total, método y fecha en checkout. «Confirmar compra simulada» activa plan solo con resultado aprobado; rechazo conserva el anterior y ofrece cambiar método/reintentar. Resultado e historial son privados y recargables sin repetir cargo.
7. Cambiar a otro plan cobra su mensualidad completa simulada e inicia período nuevo de inmediato, sin prorrateo. Propuesta explícita: descenso también inmediato; elegir Free no cobra ni reembolsa y termina plan anterior. Confirmación muestra pérdida de período anterior. Elegir plan actual no genera cargo ni reinicia fechas.
8. Cancelar programa término al final del período pagado; no cambia beneficios antes. Retirar cancelación antes de fecha habilita la renovación futura. Al terminar, plan efectivo Free y no se renueva. Ningún cargo ni cambio de estado se crea por abrir una página.
9. Renovación simulada: propuesta técnica de botón propio disponible al vencer un período no cancelado. Crea una mensualidad desde el momento de simulación, sin cobrar meses atrasados; no es renovación automática real. Si falla, muestra vencida/pago rechazado sin extender período. No requiere scheduler externo en este prototipo.

## Requisitos funcionales

- **RF-007-01 — Registro público local.** Abrir allauth para correo/contraseña, validar servidor y crear cuenta/perfil RESTRICTED/Free atómicamente. Rechazar payload de elevación de privilegios, username/correo duplicados y contraseña inválida sin altas parciales. Nunca alterar cargos de cuentas existentes.
- **RF-007-02 — Google e identidad.** Habilitar Google sobre allauth, mismo aprovisionamiento de nuevas cuentas; login repetido no duplica ni reinicia perfil/suscripción. Si correo coincide con cuenta local, exigir iniciar sesión y conectar explícitamente Google; no fusionar ni cambiar rol automáticamente. Cancelación/error OAuth no crea cliente incompleto.
- **RF-007-03 — Verificación.** Exigir EmailAddress verificado de la cuenta antes de métodos/contratación/renovación; implementar confirmación/reenvío con límites allauth y prueba local. Correo verificado Google debe validarse por proveedor, no por un campo POST. Cambio de correo sin dirección verificada impide contratar; cancelación permanece disponible. Conservar cuentas internas/MFA.
- **RF-007-04 — Catálogo.** Mostrar los cuatro planes, valores CLP, beneficios, comparación y plan actual; catálogo visible anónimo. No ejecutar beneficios, simular métricas ni inventar popularidad. Un plan inactivo no admite contratación nueva; las operaciones previas conservan su precio/nombre histórico.
- **RF-007-05 — Mi suscripción.** Mostrar información solo del titular; alta pública empieza en Free sin renovación ni tarjeta necesaria. Para cuentas preexistentes sin suscripción, mostrar Free de forma virtual sin crear filas en GET; inicializar al primer POST autorizado. Plan/estado efectivo considera fechas aun antes de materializar el vencimiento.
- **RF-007-06 — Métodos de prueba.** Agregar/listar/seleccionar predeterminado/eliminar propios; permitir solo números de prueba enumerados abajo. Validar fecha no vencida (válida hasta cierre del mes, America/Santiago), mes 01–12, MM/AA, CVC de tres dígitos y titular de 2–100 caracteres con letras Unicode y signos comunes, sin números. No almacenar/loguear PAN/CVC ni repoblarlos en error. Método ajeno responde 404. No duplicar misma tarjeta de prueba/vencimiento; un solo predeterminado. Al eliminar el predeterminado, elegir sustituto o confirmar cancelación al término si era el último de plan pagado; impedir renovación aprobada sin método válido.
- **RF-007-07 — Tarjeta interactiva.** Una sola tarjeta refleja titular/número/fecha al escribir; enfocar CVC muestra reverso y salir devuelve frente. Tarjeta ficticia identificada como ejemplo; movimiento reducido cambia cara sin giro. Campos/errores siguen disponibles sin JS y no dependen del lado visible. Ningún dato en localStorage/sessionStorage/analítica.
- **RF-007-08 — Compra simulada.** Checkout privado calcula plan, valor y propietario en servidor; precio recibido del navegador no es confiable. Compra aprobada cambia suscripción e historial juntos; rechazo crea resultado de intento sin activar plan. POST con CSRF; doble click/reenvío usa idempotencia y no duplica. GET de resultado no cobra.
- **RF-007-09 — Cambio y cancelación.** Aplicar las reglas confirmadas de cambio inmediato sin prorrateo y cancelación al cierre; mostrar consecuencias antes de confirmar. Las precisiones de flujo 7/8 son propuestas para revisión. No hay reembolsos simulados automáticos ni cambios de cargo. Revocación válida solo antes del cierre.
- **RF-007-10 — Renovación mensual simulada.** Fechas por mes calendario en America/Santiago, ajustando día al último disponible (31 enero → último febrero). Botón demuestra renovación de período vencido elegible; reintentos no duplican período/cargo. Vencida/cancelada no se muestra como pagada activa. Free no renueva.
- **RF-007-11 — Historial y detalle.** Guardar fecha/actor, operación, plan/precio/moneda/período de esa operación, referencia y resultado simulado. Mostrar historial paginado y detalle HTML del titular con rótulo de simulación, nunca factura tributaria. Eliminar tarjeta no destruye el historial enmascarado.
- **RF-007-12 — Separación cliente/interno.** Proteger listado Usuarios y datos del Inicio por cargo/helper en servidor y menú. Cliente llega a Mi suscripción. Preservar Perfil, cambio de contraseña, confirmación, MFA y preferencia visual propia; dar acceso al selector de modo desde área cliente. Ninguna URL/filtro permite datos de otro usuario ni acciones administrativas de 004/006.
- **RF-007-13 — Integración y evidencia.** Mantener layouts reales, componentes, tokens claros/oscuros, es-cl/America/Santiago y Tailwind standalone. Pruebas aisladas por RF, regresión pertinente y navegador para tarjeta/checkout/teclado/móvil/ambos modos; evidencia y límites reales, sin aceptación automática.

## Datos de prueba

Lista cerrada para el simulador local. Números documentados para pruebas por [Stripe](https://docs.stripe.com/testing); no son tarjetas reales ni se conectará Stripe. Los resultados de nuestra aplicación se definirán localmente: también permitirá guardar escenarios de rechazo para probar compras.

| Número | Marca representada | Resultado local propuesto |
|---|---|---|
| 4242 4242 4242 4242 | Visa | Compra aprobada |
| 5555 5555 5555 4444 | Mastercard | Compra aprobada |
| 4000 0000 0000 0002 | Visa | Rechazo genérico |
| 4000 0000 0000 9995 | Visa | Fondos insuficientes simulados |

Titular ejemplo: Ana Demo. Vencimiento: **12/30** (válido en fecha de esta spec). CVC: **123**. Rechazar cualquier número fuera de la lista, aunque pase Luhn. Rechazar 13/30, fecha pasada y CVC inválido antes de guardar. Datos de prueba deben actualizarse cuando su vencimiento deje de ser futuro.

## Datos, integridad y conservación propuestas

Plan identificable por código único, orden, estado, precio y beneficios ordenados. Suscripción única por User, plan y snapshot vigente, inicio/fin aware, cancelación y versión para conflictos. Método con propietario, titular ficticio, marca, últimos cuatro, mes/año, identificador de escenario y estado predeterminado; ninguna columna de PAN/CVC. Operación conserva snapshot y referencia/idempotencia únicos por usuario. No usar floats para dinero.

Crear/editar catálogo solo mediante Django admin ya existente y su política staff/model permissions; no dar ese acceso por RESTRICTED ni ampliar privilegios de MANAGER. Datos demo iniciales no alteran cuentas existentes. Propiedad no se toma de hidden inputs. Escrituras relacionadas transaccionales; estado/catálogo/método/verificación se reevalúan al confirmar. Conflicto de versión muestra revisión requerida, sin pago con oferta obsoleta. Logs solo referencias/resultados; proteger parámetros sensibles del formulario y respuestas sin caché compartida.

No se fija una política legal de retención de clientes; prototipo usa datos ficticios y entorno separado. Historial persiste al retirar tarjeta; borrado de cuenta/retención comercial/operación de producción quedan fuera de este alcance.

## Aceptación observable

| RF | Caso | Resultado esperado |
|---|---|---|
| 01 | Alta válida y cargo/flags manipulados; fallo al crear Profile/Free | Un User+Profile RESTRICTED+Free sin privilegios, o ninguna alta ante fallo; manipulación no eleva |
| 02 | Google nuevo/repetido/correo coincidente/callback cancelado | Alta única; cuenta existente preservada; conexión explícita; sin alta incompleta |
| 03 | Local sin confirmar, confirmación válida/expirada, Google no verificado | Métodos/checkout bloqueados hasta confirmación; token inválido no verifica; MFA/login interno preservados |
| 04/05 | Catálogo anónimo; cliente nuevo y preexistente; fin de período | Cuatro planes exactos; datos propios/Free; fecha y estado correctos sin escrituras por GET |
| 06 | Tarjeta permitida/real ajena a lista/expirada/duplicada; ID ajeno | Guarda solo máscara y escenario; errores sin PAN/CVC; 404 para ajeno; default único |
| 07 | Escribir y enfocar CVC en móvil, teclado, sin JS y movimiento reducido | Vista coherente; giro solo solicitado; formulario utilizable y errores legibles en todos los casos |
| 08 | Comprar Plus con Visa éxito/rechazo, precio adulterado y doble POST | $4.990 desde servidor; un resultado y cambio atómico solo si éxito; sin cargo duplicado |
| 09 | Plus→Pro, Plus→Free, cancelar/repetir/revocar después de cierre | Efectos explicados y coherentes; repetición inocua; revocación tardía rechazada |
| 10 | Mes corto/año bisiesto/vencimiento; renovación fallida y reintento | Fechas aware correctas; rechazo no extiende; un período por acción idempotente |
| 11/12 | Abrir historial/resultado/método de B como A; cliente abre Usuarios/Home | Ningún dato ajeno; 404 objetos ajenos; 403 Usuarios; Home redirige sin consulta de cuentas |
| 13 | Suite/build/navegador y revisión de docs | Evidencia aislada real por RF, pendientes honestos y aceptación del propietario separada |

## No funcionales y compatibilidad

Móvil desde 360 px, tablet y escritorio; sin desbordamiento a 200% de zoom. Foco visible, etiquetas asociadas, errores junto a campos y resumen, iconos con texto accesible, estados que no dependen de color; texto normal ≥4,5:1. Animación local, sin bucles ni bloqueo al escribir. La skill [frontend-design](../../.codex/skills/frontend-design/SKILL.md) orienta integración, sin autorizar código.

007 sustituye **solo para este derivado** el cierre público RF-001-02 y amplía correo none de D-009 con confirmación previa a contratar. Mantener evidencia histórica de 001/005: adaptar tests del cierre a apertura segura con traza explícita. La lectura del listado/Inicio y destino cliente amplían permisos previos de 001–003; 004/006 siguen vigentes. No relajar MFA ni reconstruir User, Profile, tema o navegación.

## Decisiones autorizadas y límites externos

Confirmadas inicialmente: registro dual, catálogo de imágenes, mensualidad/cambio/cancelación y verificación. Las precisiones Free inicial, CLP, descenso a Free, reinicio de período, botón de renovación, privacidad interna y conexión explícita de Google quedaron incluidas en la autorización posterior del alcance completo. Se distingue esa autorización técnica de la aceptación funcional final.

Dependencia externa: proyecto OAuth, dominio/callback y credenciales Google fuera de documentos; no pedir secretos en chat. Pruebas mock verifican lógica, pero no acreditan login Google real. Marca definitiva, hosting, SMTP y política comercial/producto real quedan por definir fuera del prototipo. Implementación autorizada y entregada; OAuth real, revisión manual visual/propietario e instalación en la DB elegida siguen pendientes, según validation.md.
