# Plan técnico — 007 / PlanesApp

[Spec](spec.md). Fecha: 2026-10-06. Estado: **alcance completo autorizado posteriormente e implementado**. [Validación](validation.md).

Este documento conserva la inspección y propuesta escritas en DOCUMENTAR antes del permiso. Las expresiones «previsto», «no ejecutado ahora» y «propuesta» en esa descripción corresponden a aquella fase. El resultado actual, archivos efectivos, comandos y límites están en validation.md; no modifican los RF para legitimar errores.

## Inspección real y conservación

Git inicial limpio, HEAD `69b2eb4` (`feat: base`). No existe carpeta PlanesApp ni colisión encontrada en archivos propios. Siguiente número libre comprobado: 007; usar nombre solicitado con esa capitalización. No se leyó .env, bases de datos ni media personal. Capturas examinadas como referencias del pedido.

Leídos constitución, README, proyecto/estado/índice, arquitectura, decisiones, observaciones, entorno, trazabilidad, specs 001/006 y contratos visuales 002/003; guías `00-orquestador`, `01-especificar`, `02-planificar`, `03-tareas` y skill frontend-design. Fases aplicadas en orden: especificar → planificar → tareas, exclusivamente Markdown.

Hallazgos estáticos:

- `UsuarioApp/adapters.py`: NoSignupAccountAdapter devuelve False. `templates/account/signup.html` también muestra cierre. Login ya incluye snippet social condicionado a SOCIALACCOUNT_ENABLED, pero socialaccount no está activado.
- `core/settings.py` importa `common_settings.py`. **LOCAL_APPS real está en common_settings**, no duplicar listas en settings normal. `core/urls.py` ya incluye allauth bajo `/accounts/`.
- User estándar; Profile.user_FK OneToOne; Position.user_position único y permission_code no único. Perfil ausente/cargo nulo son válidos en esquema. No usar IDs mágicos ni asumir único Position RESTRICTED.
- `UsuarioApp/permissions.py`: Registro interno y gestión son políticas independientes con cargo incluso para root. `core/mixins.py` conserva excepción root para helper general.
- `UserListView` y `HomeView` solo LoginRequiredMixin: lista y accesos recientes exponen otras cuentas a cualquier autenticado. El menú Usuarios es incondicional aunque existe flag puede_gestionar_usuarios.
- `ProfileUpdateView` puede crear perfil sin cargo: para cuentas existentes no convertir ese GET en aprovisionamiento de cliente ni cambiar cargos; el registro nuevo sí asigna RESTRICTED explícito.
- Tokens y layouts compartidos operativos en fuente; `@source` solo incluye apps actuales. Selector visual POST vuelve a Home; documentar su uso desde área cliente sin romper ese contrato.
- `.venv-actualizada` mencionada en documentos previos **no existe en esta copia**. Existe `.venv`, sin runtime comprobado. Lecturas de metadatos de paquetes en la ruta histórica fallaron por inexistencia; sin instalación, importación Django ni tests en DOCUMENTAR. Preparar entorno aislado después de autorización conforme a [guía](../../docs/ENTORNO_Y_VERIFICACION.md).

## Responsabilidades y archivos

Crear PlanesApp para catálogo, suscripción, método ficticio y operaciones. Ampliar UsuarioApp para aprovisionamiento público y adapters allauth; reutilizar usuarios, permisos internos, preferencias y fotos predeterminadas. Reglas de compra en servicio pequeño por necesidad de transacciones/idempotencia, sin una arquitectura genérica extra.

| RF | Archivos existentes a modificar | Archivos nuevos previstos | Evidencia prevista |
|---|---|---|---|
| 01–03 | `UsuarioApp/adapters.py`, `forms.py`, `core/common_settings.py`, `core/settings.py`, `requirements.in`, `requirements.txt`, plantillas account | `UsuarioApp/services.py`, `UsuarioApp/tests_registro_publico.py`; plantillas socialaccount necesarias | Alta/rollback/verificación/colisión/OAuth simulado |
| 04/05 | `core/urls.py`, `common_settings.py` | `PlanesApp/apps.py`, `models.py`, `admin.py`, `urls.py`, `views.py`, `services.py`, `forms.py`, `migrations/`, inicializadores | Catálogo/Free/propiedad/fechas |
| 06/07 | Fuentes Tailwind y tokens solo si hace falta token semántico | `PlanesApp/simulator.py`, `PlanesApp/static/PlanesApp/card.js`, `planes.css`, plantillas métodos | Lista cerrada, no PAN/CVC, interacción navegador |
| 08–11 | Layouts/componentes reutilizados, sin reconstrucción | Servicios/formularios/vistas y plantillas de checkout/resultado/cancelación/historial | Atomicidad, precio, idempotencia, estados y meses |
| 12 | `UsuarioApp/views.py`, `homeApp/views.py`, `core/context_processors.py`, `templates/components/navbar/nav.html` | Política de cliente en `PlanesApp/permissions.py` | Matriz URL/HTML; no consultas ajenas |
| 13 | `theme/static_src/src/styles.css`, CSS generado tras build, tests pertinentes de UsuarioApp/homeApp | `PlanesApp/tests.py`, evidencia documental posterior | Suite/check/esquema/build/navegador |

Todas las rutas nuevas de esta tabla son **previstas** y no enlaces a archivos existentes. No crear tests ejecutables ni migraciones durante DOCUMENTAR.

## Registro y Google

1. Sustituir adapter cerrado por adapter público local con save_user transaccional. Servicio UsuarioApp crea solo el Profile faltante de un **usuario nuevo** con Position público designado; exige permission_code RESTRICTED. Inicializar Free mediante servicio PlanesApp dentro de la misma transacción. No asignar cargo en cada login ni modificar perfiles de cuentas existentes.
2. Alta pública fuerza `is_staff=False`/`is_superuser=False`, no acepta position/id propietario del navegador. Formulario allauth mantiene campos locales/validadores de Django. Google resuelve username único y correo; no importar avatar por URL ni usar la contraseña local para OAuth.
3. Position propuesta de nombre reservado `Cliente público`, código RESTRICTED. Migración de datos inicial crea si falta; si el nombre existe con otro código, detener y resolver colisión sin modificar cargos reales. Relaciones se resuelven por nombre/código, nunca pk. Servicio falla cerrado si cargo/catalogo inicial no disponible.
4. Activar `allauth.socialaccount` y `allauth.socialaccount.providers.google` en THIRD_APPS. Registrar PlanesApp en LOCAL_APPS de common_settings; settings normal la hereda. Mantener backends/MFA. Cambiar entrada a `django-allauth[mfa,socialaccount]==65.19.7`, resolver únicamente dependencias extra necesarias y regenerar lock/hashes según [DEPENDENCIAS](../../docs/DEPENDENCIAS.md); no upgrade general. La [instalación oficial](https://docs.allauth.org/en/latest/installation/quickstart.html) identifica el extra socialaccount.
5. Google usa OAuth con PKCE, scopes profile/email, acceso online. Credenciales en variables de entorno de settings normal; fixtures inocuos en test_settings. Una sola fuente de configuración del proveedor (APP por entorno); no duplicar con SocialApp. Callback esperado `/accounts/google/login/callback/`; dominio real queda pendiente. [Proveedor Google oficial](https://docs.allauth.org/en/latest/socialaccount/providers/google.html).
6. Adapter social personalizado permite alta nueva y reutiliza mismo servicio/transacción; incluye SocialAccount/EmailAddress en la unidad de alta. Auditar implementación instalada de save_user para ubicar atomic correctamente; no duplicar mediante signals. [Contrato oficial del adapter](https://docs.allauth.org/en/latest/socialaccount/adapter.html).
7. Mantener `SOCIALACCOUNT_EMAIL_AUTHENTICATION=False` y auto-connect False; conectar desde sesión autenticada con allauth cuando correo coincide, sin fusión ni cargos alterados. OAuth se inicia por POST/CSRF, sin tokens OAuth persistidos. Proteger callback/estado mediante allauth. [Configuración oficial](https://docs.allauth.org/en/latest/socialaccount/configuration.html).
8. Proponer `ACCOUNT_EMAIL_VERIFICATION='optional'` para que allauth envíe confirmación sin bloquear el login de operadores heredados; el servicio de métodos/contratación exige dirección verificada. Google solo admite condición verificada comprobada por proveedor. Así se cumple «confirmar antes de contratar» sin hacer globalmente obligatorio el correo para MFA/login interno. Mantener MFA_ALLOW_UNVERIFIED_EMAIL para su contrato existente.
9. Backend consola/local para desarrollo y locmem en tests. Probar tokens de confirmación/reenvío/expiración, cambios de correo y Google sin correo verificado. Preservar recuperación/cambio/set-password/MFA; cuentas Google sin contraseña usan set-password allauth, sin contraseña ficticia en DB.
10. Enlaces Crear cuenta en login y Volver a iniciar sesión en signup; página de conexiones allauth accesible desde cuenta. Si no hay configuración Google, botón informa indisponibilidad; no simular login social como real. No aceptar destino next externo.

## Esquema propuesto

| Modelo nuevo | Campos/contratos principales |
|---|---|
| Plan | code SlugField unique ≤30; name ≤60; description ≤180; amount_clp entero ≥0; currency CLP; monthly; active; display_order; updated_at |
| PlanBenefit | FK Plan CASCADE; text ≤220; order entero; orden estable/único por plan |
| Subscription | OneToOne User CASCADE; FK Plan PROTECT; snapshot nombre/precio/moneda; start/end aware; cancel_at_period_end; canceled_at nullable; versión entera; created/updated |
| SimulatedPaymentMethod | FK User CASCADE; holder ≤100; fixture_code cerrado; brand; last4; month/year; default; active; created; unique usuario/fixture/vencimiento y default activo único |
| SimulatedOperation | UUID referencia; FK User CASCADE; FK Plan PROTECT; FK método SET_NULL; snapshot nombre/precio/moneda/máscara; tipo compra/cambio/renovación/Free/cancelación/revocación; resultado aprobado/rechazado; clave idempotencia; períodos anterior/nuevo; cancelación; fecha; código de error no sensible |

Checks: CLP y precio no negativo; start < end para pago y fechas nulas para Free; mes/año válidos; last4 de longitud/dígitos correctos; escenarios/estados/tipos finitos. Unicidad se aplica en DB además del formulario. No representar beneficios como permisos Django ni campo is_staff. Inactivación/eliminación lógica de método permite excluirlo de compras; historial conserva máscara aunque relación se retire. No crear columna PAN/CVC ni almacenar request.POST como JSON.

Carga inicial de catálogo: los cuatro planes y beneficios de spec con códigos `free`, `plus`, `pro`, `hogar`. Seed histórico solo al instalar; no sobrescribir ediciones posteriores al reiniciar. No agregar suscripciones a cuentas previas mediante backfill: GET muestra Free virtual, primer POST crea fila bajo bloqueo del User.

## Contratos de compra y fechas

- Formulario de método recibe PAN/CVC **solo** para validar fixture permitido; convierte a fixture_code/marca/last4 y descarta sensibles. sensitive_post_parameters/sensitive_variables y never_cache; errores no incluyen valor original. Preview escribe texto con textContent. El backend simulado elige resultado por fixture, sin SDK/red ni estado de éxito enviado por cliente.
- Checkout GET lee plan y método propios, muestra precio/fechas del servidor y emite propuesta firmada/limitada en tiempo con versión de suscripción, plan/precio, método, operación y nonce. No crea operaciones/suscripciones por GET; puede usar sesión/CSRF estándar. POST revalida propuesta y estado vigente; firma no sustituye validación de catálogo/precio.
- Bajo atomic bloquear User (también para primera suscripción), suscripción y métodos pertinentes con orden consistente; reevaluar cuenta activa, correo verificado, propiedad, plan activo/precio/version y método no vencido. Registro de operación con unique(user, idempotency_key) proporciona deduplicación durable. Repetición de clave con mismo payload devuelve operación propia original; misma clave con payload distinto se rechaza.
- Simulación aprobada y actualización quedan juntas. Rechazo esperado guarda solo operación rechazada y conserva suscripción; fallo técnico revierte todo, muestra error sin falso éxito y permite reintento. No atrapar excepciones generales para transformar errores en éxito. Concurrentes con versión antigua deben recargar/revisar, sin doble cobro/cambio.
- Cambio pagado inicia nuevo período en now y cobra total del destino. Cambiar a Free cuesta cero, termina período y anula renovación; no inventar devolución. Comprar plan actual se trata como acción sin cambio. Cancelar repetido no altera fecha; revocar tras end exige nueva contratación.
- Un mes calendario en America/Santiago conservando hora local y acotando día al mes destino; guardar UTC aware. Probar años bisiestos, fin de mes y transiciones horarias con regla explícita para hora inexistente/ambigua: avanzar al primer instante válido y usar primera ocurrencia respectivamente. Se usará librería de fechas ya declarada si está disponible; no agregar paquetes por rutina.
- Plan efectivo se calcula al leer: Free si cancelación cumplida; vencida si pago terminó sin renovar; Free inicial sin fechas. No mutaciones desde context processors/GET. POST posterior puede materializar el estado vencido antes de operar.
- Renovación propuesta vía POST de botón, solo período terminado no cancelado; desde now hasta now+un mes, sin cobrar atrasos. Misma clave/version/period_end impide repetir; éxito actualiza, rechazo no extiende. No Celery/cron ni cobro invisible. Rótulo claro «Simular renovación» y explicación en resumen.
- Eliminar último método de pago de plan pagado ofrece confirmación explícita conjunta de cancelación a término; DELETE lógico + cancelación en una transacción. Dejar de predeterminado exige reemplazo; asignación predeterminada concurrente protegida por constraints/bloqueo.

## Rutas y templates propuestos

Namespace `PlanesApp`, prefijo `/planes/`, sin colisión con Register `/registro/` ni Profile. Mantener allauth bajo `/accounts/`.

| URL propuesta | Nombre | Método / propósito |
|---|---|---|
| `/planes/` | catalogo | GET público |
| `/planes/mi-suscripcion/` | mi_suscripcion | GET propio |
| `/planes/metodos/` | metodos | GET listado / POST alta |
| `/planes/metodos/<pk>/predeterminado/` | metodo_predeterminado | POST propio |
| `/planes/metodos/<pk>/eliminar/` | metodo_eliminar | GET confirmación / POST retiro |
| `/planes/contratar/<code>/` | contratar | GET revisión / POST compra/cambio |
| `/planes/operaciones/<uuid>/` | resultado | GET propio, éxito/rechazo/detalle |
| `/planes/cancelar/` | cancelar | GET confirmación / POST |
| `/planes/retirar-cancelacion/` | retirar_cancelacion | POST |
| `/planes/renovar/` | renovar | GET revisión / POST simulación |
| `/planes/historial/` | historial | GET propio paginado |

CBV preferidas, consultas filtradas por propietario desde queryset. 404 para objetos ajenos, login para anónimo, 403 para usuario activo sin permisos internos, 405 para mutación por método incorrecto; formulario inválido presenta errores sin escritura. CSRF en todos los POST. Datos privados sin caché compartida.

Templates nuevos en `templates/pages/PlanesApp/`: catálogo, resumen, métodos/formulario, checkout, resultado, cancelación, eliminar e historial. Componentes de plan y tarjeta en `templates/components/PlanesApp/`. Catálogo anónimo extiende `components/Layout/base.html`; variantes privadas extienden `base_extendido.html`/content_main. Formularios acotados reutilizan `base_pages.html`/content_pages. Signup/social usa `account/Layout/base_simple.html`/content_account. No inventar `base_extendida.html`.

## Cliente e integración interna

Home conserva URL/nombre y dashboard para operador autorizado; redirige a Mi suscripción **antes de get_queryset/get_context_data** a RESTRICTED/sin cargo no root. UserListView añade autorización de lectura con helper general y denegación 403. Menú Usuarios condicional a puede_gestionar_usuarios; Registro y filas administrativas conservan 004/006. Cliente recibe enlaces Mi suscripción, Planes, Métodos e Historial junto a Perfil/seguridad existentes.

Selector de modo cliente envía al endpoint VisualMode ya existente; su vuelta a Home redirige a resumen del cliente. Así funciona con/sin JS sin introducir next arbitrario ni cambiar contrato de 003. Para root/ADMIN/MANAGER Home sigue disponible. Cuenta/contraseñas/conexiones sociales usan los flujos allauth, no páginas de autenticación nuevas propias de PlanesApp.

## Dirección visual — skill frontend-design

Reutilizar [guía visual](../../docs/PERSONALIZACION_VISUAL.md) y tokens; no copiar las capturas ni el gradiente morado. Público objetivo: cliente que compara planes y administra suscripción, sin operar vigilancia real. Identidad actual y foco visual de esta ampliación: **una tarjeta que responde al formulario**, con checkout sobrio y consecuencias visibles.

Paleta existente de referencia, sin nuevos hex en componentes: petróleo marca `#0f766e`; acento oscuro `#5eead4`; fondo claro `#f2f5f8`; superficie `#ffffff`; tinta `#182536`; fondo oscuro `#101923`. Consumir --brand/--surface/--ink/--muted/--border y variantes, incluyendo reverso con contraste medido. Tipografía --font-ui (Segoe UI/sistema), misma escala/jerarquía actual; numeración legible, sin nuevas fuentes remotas. Alinear textos/campos a izquierda; precio destacado sin decoración excesiva.

Composición: catálogo en cuatro columnas amplias cuando quepan y una columna móvil, beneficios ordenados y acciones alineadas; resumen con plan como elemento principal y método/fechas al lado; checkout en dos columnas con resumen estable. No envolver cada texto en panel ni animar todos los planes.

```text
Escritorio: métodos                   Móvil: métodos
Título + aviso de simulación          Título + aviso
[tarjeta visual, frente/reverso]       [una tarjeta]
                       [titular]      [titular / número]
                       [número]       [MM/AA / CVC]
                       [MM/AA][CVC]    [Guardar tarjeta de prueba]
                       [Guardar]

Checkout: [plan y consecuencias] | [total / método / confirmar]
Resumen:  [plan, beneficios y estado] | [renovación / método]
```

Tarjeta con proporción natural, acento de marca, últimos dígitos/fecha/titular y rótulo «De prueba». Preview puede mostrar número de prueba al escribir; al guardar solo máscara. Giro solicitado por foco CVC, 220ms usando contrato --motion-panel; no hover obligatorio, cursor no mueve toda la interfaz. CVC no se anuncia repetidamente a lectores de pantalla; cara visual decorativa/aria-hidden y formulario es fuente accesible. Movimiento reducido cambia cara sin transición; sin JS formulario completo y ayuda estática. Errores no se ocultan por animación.

Revisión de propuesta contra brief: se conserva tipografía/paleta por pedido expreso; se elimina gradiente ajeno, tarjetas animadas de catálogo y cifra «cámaras conectadas» sin datos reales. Interacción concentrada en métodos. Validación visual futura en ambos modos, 360/390/768/1024/1440 px, teclado/foco/zoom 200%/movimiento reducido, errores/vacíos y datos largos.

`@source` previsto: `../../../PlanesApp` para Python y estáticos de app; templates globales ya incluidos. Conservar exclusiones de migrations/__pycache__/staticfiles y excluir CSS generado. Registrar clases completas, compilar sin npm y revisar muestras de nuevas utilidades. CSS/JS propios acotados al módulo; versiones de caché actualizadas solo en recursos cambiados.

## Migraciones, instalación y reversión

Después de autorización: migración de esquema PlanesApp dependiente del User intercambiable; seed de catálogo/cargo dependiente de UsuarioApp 0002. Identificar migraciones oficiales socialaccount de versión instalada antes de ensayo; no afirmar que ya existen tablas ni que 0002 está aplicada a la base normal.

Solo ensayar migración/reversión en SQLite efímero/datos ficticios. Seed reverso no borra Position ni datos comerciales usados por perfiles/suscripciones (reverse no-op documentado); reversión de esquema elimina tablas/operaciones de PlanesApp, exige exportar/resguardar si se desea conservar. Revertir socialaccount puede perder vínculos Google y dejar usuarios sin contraseña local: documentar recuperación/versión compatible antes de cualquier reversión real. No borrar usuarios ni demover cargos como compensación de rollback.

Aplicación a esta DB existente o producción requiere autorización específica de entorno/respaldo, fuera de DOCUMENTAR. Credenciales OAuth y SMTP son dependencias externas; no guardarlas en spec/fixtures/commits. No migrar datos reales para verificar.

## Verificación prevista

Leer guía de entorno; preparar intérprete y dependencias con lock en fase autorizada, sin asumir disponibilidad del venv histórico. Comandos propuestos, **no ejecutados ahora**:

```text
python manage.py check --settings=core.test_settings
python manage.py makemigrations --check --dry-run --settings=core.test_settings
python manage.py test UsuarioApp homeApp PlanesApp --settings=core.test_settings
python manage.py tailwind --settings=core.test_settings build
```

Tests por RF: altas local/social+rollback, flags/cargos arbitrarios y ausencia de escalación, correo/confirmaciones/collisiones, IDs ajenos para cada operación, matriz completa (inactivo/sin perfil/sin cargo/staff/root), catálogo y GET sin escrituras, PAN/CVC no persistidos ni reflejados, fixture no permitido, vencimiento, default/último método, precio alterado, idempotencia/payload distinto, transacción/fallo y cambio/cancelación, meses/cancelación cumplida/renovación. Concurrencia real debe probarse con motor objetivo si se exige: SQLite no demuestra select_for_update.

Actualizar tests históricos del cierre y Home/listado con referencia a sustitución por RF-007-01/12; conservar la regresión de todo lo demás. No alterar spec para legitimar fallos. Tests Google con mocks no reemplazan un ensayo OAuth real con configuración legítima; si falta, reportar integración externa no verificada. UI exige navegador y evidencias aisladas, no capturas de datos reales. No crear PDF.

Al cierre documentar comandos/conteos/resultados, archivos reales por RF, lo no probado, tareas y aceptación separada. Ahora se comprueban únicamente enlaces, coherencia documental, orden spec/plan/tasks, diff y ausencia de cambios fuera de Markdown.

## Riesgos y revisión pendiente

Precisiones técnicas/comerciales propuestas en spec necesitan revisión; ninguna confirmación de reglas recibida autoriza código. Evitar abrir listado de clientes al abrir signup y evitar demover un operador al iniciar Google. API externa/credenciales, instalación de extra social, pruebas de concurrencia en motor final y entorno ausente son límites explícitos. No activación implícita de axes/concurrentlogins ni limpieza/dependencias ajenas.
