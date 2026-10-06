# Plan — 003 / Modo visual por usuario

Fecha: 2026-10-02. [Spec](spec.md). Estado: alcance completo autorizado por instrucción posterior e implementado; [validación](validation.md) y aceptación pendientes en los aspectos indicados.
Guías aplicadas: 06-cambios, 01-especificar, 02-planificar, 03-tareas y frontend-design.

## Inspección inicial y conservación — antecedente documental

- Leídos AGENTS, constitución, README, proyecto/estado/índice, spec 002, arquitectura, decisiones, observaciones, guía visual y entorno; inspeccionados modelos, migración 0001, vistas/rutas/formularios, permisos/processor, middleware de actividad, layouts, Inicio, tokens y gráfico.
- 003 es el siguiente número libre. No hay módulo solicitado ni app nueva; se amplía UsuarioApp y presentación compartida. No existen UserVisualPreference ni ruta de modo en los archivos inspeccionados.
- Ahora `git status --short` funciona y la rama es main. Hay numerosos cambios de 002 y recursos nuevos sin seguimiento: se preservarán. El registro de «sin Git» de la entrega anterior queda como histórico; no se harán reset, checkout, stage, commit ni push.
- Antes de esta fase se inventariaron por SHA-256 105 archivos de código/recursos/dependencias. Esta fase modifica únicamente Markdown; comparación posterior en ESTADO_PROYECTO.
- Profile.save procesa la imagen incluso al guardar otros atributos. ProfileUpdateView crea perfil ausente; el middleware solo actualiza actividad de perfiles existentes. No reutilizar su save para guardar preferencias ni crear perfiles como efecto de esta función.
- tokens.css contiene un solo modo, styles.css declara color-scheme light y el gráfico lee tokens al inicializar. No existe selector persistente; esto estaba excluido de 002.

## Integración propuesta

Modelo pequeño `UserVisualPreference` en UsuarioApp, relacionado uno a uno con `settings.AUTH_USER_MODEL`. Su única preferencia será `mode`; no reconstruir User/Profile ni registrar una app adicional. El nombre es descriptivo y no colisiona con los modelos actuales.

Un processor nuevo `preferencias_visuales` expone `modo_visual` y `puede_cambiar_modo` desde la cuenta activa. Consulta exclusivamente la fila propia, devuelve light cuando no existe y **no crea datos en GET**. Registrar en core/common_settings.py junto a los processors actuales, sin alterar permisos_navegacion. Los contextos de error sin usuario se resuelven a claro.

El layout base emite un atributo `data-mode` seguro en html con light/dark elegidos por el servidor, antes del CSS. El token claro sigue como base y el selector dark redefine las mismas variables; controles nativos usan color-scheme acorde. No se necesita recordar una elección compartida en el navegador para pintar la primera respuesta.

En el encabezado de Inicio se añade un formulario POST con CSRF, modo destino explícito y botón de icono SVG. Después del guardado vuelve a Inicio y renderiza la elección confirmada. El envío normal funciona con JavaScript desactivado; la recarga reinicializa el gráfico desde los tokens correctos. Se evita un segundo estado de tema en JavaScript o un cambio visual optimista que pueda diferir del guardado.

## Dirección visual propuesta

Conservar composición, fuentes, anchuras y densidad de 002. El cambio es de luminosidad: fondo oscuro frío, superficies diferenciadas, texto claro y acento de marca suficientemente luminoso para enlaces/foco. Sin inversión automática de imágenes ni nuevas animaciones globales al cambiar tema.

| Token / uso | Claro existente | Oscuro propuesto |
|---|---|---|
| Página | #f2f5f8 | #101923 |
| Superficie | #ffffff | #182536 |
| Superficie secundaria | #eaf0f5 | #203044 |
| Texto | #182536 | #e8eef5 |
| Ayuda | #506177 | #b0becf |
| Separación | #d9e2ea | #33445a |
| Límite de control | #758599 | #7a8fa7 |
| Marca petróleo | #0f766e | #5eead4 |
| Texto sobre marca | #ffffff | #102124 |

Alternativas pares: ciruela #7e22ce / #c084fc; cobre #9a3412 / #fdba74. **No medidas ni aprobadas todavía**. El archivo de tokens documentará las variables de marca clara/oscura y sus respectivos textos; se cambian juntas en ese único archivo. Éxito/error/aviso/información necesitan variantes de fondo/texto propias; las acciones peligrosas conservan su token independiente. Colores de gráfico, tooltip, bordes, foco y sombras se revisan en cada modo. No fijar el mismo acento oscuro para todos los proyectos.

## Archivos por RF

| RF | Archivo real / propuesto | Intervención | Evidencia prevista |
|---|---|---|---|
| 02, 03, 07 | UsuarioApp/models.py (existente) | Nuevo modelo de preferencia, User/Profile/Position intactos | Propiedad, unicidad, valores válidos y perfiles ausentes |
| 02, 07 | UsuarioApp/migrations/0002_user_visual_preference.py (propuesto; confirmar siguiente número al implementar) | CreateModel aditivo | Esquema y reversión con SQLite de pruebas |
| 03, 06 | UsuarioApp/forms.py, views.py, urls.py (existentes) | Form de modo, CBV de guardado y ruta propia | POST/CSRF, matriz, entradas inválidas y aislamiento entre usuarios |
| 02, 04 | core/context_processors.py y common_settings.py (existentes) | Processor de lectura y registro | Default, propio modo y GET sin escritura |
| 04, 05 | templates/components/Layout/base.html (existente) | data-mode inicial y versión de recursos | HTML inicial y coherencia de páginas |
| 01, 05, 06 | templates/pages/index.html (existente) | Form/botón sol-luna junto a Ver usuarios | Navegador/teclado/móvil y JS desactivado |
| 04, 05 | static/css/tokens.css y styles.css (existentes) | Variantes, color-scheme y ajuste de controles si hace falta | Seis combinaciones de marca/modo y contraste |
| 04, 07 | static/js/grafico_home.js (existente, inspección; modificar solo si hay un fallo concreto) | Confirmar consumo de los nuevos tokens al recargar | Gráfico/resize, movimiento reducido y fallback |
| 03, 07 | UsuarioApp/tests.py y homeApp/tests.py (existentes) | Casos nuevos y regresión de 27 métodos recibidos | Suite aislada; conteos reales |
| 05, 07 | theme/static_src/src/styles.css (existente, si requiere clases nuevas); theme/static/css/dist/styles.css (generado) | Reutilizar puente y recompilar | Standalone, fuentes y clases completas |
| 07 | docs/PERSONALIZACION_VISUAL.md, índices/estado/trazabilidad (existentes); validation.md de 003 (futuro) | Guía y evidencia real | Enlaces y estados honestos |

No se prevén nuevas hojas/script de aplicación ni dependencia de UI; el comportamiento se resuelve con el flujo Django existente.

## Datos, endpoint y permisos

Propuesta de modelo: relación `user` única, on_delete CASCADE; `mode` CharField con choices light/dark y default light, limitado también por restricción de base de datos. Sin timestamps/historial por rutina. No añadirlo a admin ni formularios actuales de alta/perfil.

Ruta propuesta: `/preferencias/modo-visual/`, nombre `VisualMode`, CBV `VisualModeUpdateView` en UsuarioApp. No recibe PK ni identificador del propietario en URL. Form nuevo `VisualModeForm`, único campo mode; no ModelForm sobre los datos del usuario. Otros campos enviados no se utilizan para determinar propietario ni se guardan.

- LoginRequiredMixin y verificación de actividad; todos los cargos activos y superusuario pueden guardar su propio modo. **No** PermitsPositionMixin, porque excluiría RESTRICTED y cuentas sin cargo que sí deben usar esta función. No modificar ese mixin.
- Anónimo: redirigir al login, con retorno válido a Inicio (evitar next apuntando a esta URL solo POST, que produciría GET 405 después del login). Cuenta inactiva que llegase autenticada: 403. Rechazos del backend de sesión conservan su política previa.
- GET autenticado: 405, sin escritura. POST sin CSRF: 403. Modo vacío/inválido: 400 con presentación de error existente, sin modificar valor. POST válido: actualizar/crear exclusivamente `request.user`, regresar a Home y confirmar con el botón/tema. No seguir un next externo recibido.
- Guardado idempotente del destino explícito: enviar dark dos veces no vuelve a light. Usar `update_or_create` sobre el modelo de preferencias y la restricción uno a uno; el último guardado confirmado gana. Sin bloqueo/polling de otras pestañas; se actualizan al navegar/recargar.
- Si falla la persistencia, no confirmar éxito; conservar dato previo, manejar únicamente fallos de escritura previstos y devolver error legible. No imprimir datos de cuenta ni ocultar errores de programación con un catch genérico.

El selector no escribe Profile, imagen, cargo o preferencias ajenas. Su processor no ejecuta get_or_create. Un usuario sin perfil tendrá la misma experiencia y solo creará su fila de preferencia al guardar.

## Migración y reversión

Se propone una migración posterior a UsuarioApp/0001_initial, creando solo la tabla de preferencias con relación/unique/check. Dependencia del usuario intercambiable y migración anterior. No migración de datos, altas masivas ni lectura de fotos; ausencia de fila equivale a claro para cuentas recibidas y nuevas.

Durante implementación autorizada se podrá generar/revisar el archivo y aplicarlo en SQLite aislado para tests. **Aplicarlo a la base de desarrollo existente o producción requiere autorización del entorno concreto**, respaldo y ventana acordados; no hacerlo como efecto de revisar estos documentos. Antes de ejecutar código contra esa base debe existir la tabla.

Rollback elimina la tabla y pierde elecciones; no elimina cuentas/perfiles. Probarlo solo en base efímera. Para reversión real, respaldar preferencias y coordinar rollback del código antes de retirar esquema. Conservar los cambios locales actuales y snapshot/patch acotado cuando comience la implementación.

## Verificación planificada — resultados posteriores en validation.md

1. Verificar entorno antes de ejecutar. .venv estaba roto y las dependencias temporales de 002 se retiraron: no asumir que hoy hay Django ejecutable. Usar core.test_settings y cuentas sintéticas; nunca .env/base/media reales.
2. Datos: default sin fila, GET sin crear fila, primer guardado sin crear Profile, unicidad/reintento, independencia A/B, persistencia tras logout/login y nueva sesión/dispositivo.
3. Endpoint: matriz completa, inactivos incluido root, GET 405, CSRF 403, invalidación/vacío 400, parámetros de usuario ajeno ignorados y B intacto, error de guardado sin falso éxito.
4. Migración: CreateModel y restricciones, no alteraciones de cuentas/perfiles, rollback en SQLite de pruebas. Tras crear la migración autorizada, detección de migraciones debe quedar limpia.
5. Regresión actual: 27 tests recibidos; login/next, registro cerrado/interno, MFA, imágenes y actividad, cargos, búsqueda/filtros/paginación. No actualizar expectativas para legitimar un fallo nuevo.
6. Ejecutar check, makemigrations --check --dry-run y test UsuarioApp homeApp con --settings=core.test_settings. Build: `python manage.py tailwind --settings=core.test_settings build`; no Node/npm para el producto.
7. Navegador: sol/luna, ambos sentidos, teclado/foco, JS desactivado, recarga y distintas cuentas; perfil/usuarios/cuenta/MFA/errores/mensajes largos/carga/gráfico en ambos modos. Cinco anchos 360/390/768/1024/1440, zoom real 200 % y preferencia reducida. No afirmarlos si faltan capacidades.
8. Medir contrastes claros/oscuros para petróleo/ciruela/cobre, controles nativos/crispy, autofill y borde de foco. Registrar capturas sintéticas y consola en validation.md cuando se ejecuten. Pendientes de 002 continúan identificados aparte.

## Decisiones y alternativas

Tabla propia dentro de UsuarioApp frente a campo en Profile: evita procesar fotos al guardar y crea preferencias para quien no tiene perfil sin cambiar su estructura. localStorage o sesión por sí solos no recuperan la elección en otra sesión/dispositivo. Un toggle con AJAX añadiría sincronización/fallos al cliente; el POST confirmado satisface el pedido y reutiliza Django.

El modelo nuevo tiene efectos aditivos revisados y autorizados para implementación de 003. Aplicarlo a datos reales sigue excluido. No apareció una decisión crítica nueva ni efectos de esquema distintos de CreateModel.

## Implementación efectiva y ajustes verificados

Se implementó el mapa anterior; migración real generada `0002_user_visual_preference.py`. No se modificó grafico_home.js ni el puente Tailwind: al recargar consumen el nuevo modo. El build standalone regeneró dist/styles.css.

Para RF-003-06, 400.html y 500.html admiten un mensaje contextual de modo sin alterar su texto habitual. Valor inválido devuelve 400 y fallo previsto de escritura 500; el processor usa claro si falla solo la lectura de preferencias. No captura errores de programación ni certifica recuperación ante caída total de la base.

La auditoría detectó hover ciruela oscuro 4,34:1 con mezcla hacia negro; se corrigió a mezcla con blanco al 12 %. Los 180 pares finales superan sus umbrales. El QR negro de allauth perdía legibilidad sobre oscuro: `--qr-surface` blanco en ambos modos y padding acotado conservan el SVG y su función; imagen/flujo de MFA intactos.

Resultados reales: 43 tests Django, check y migraciones limpios, 59 HTML, build 4.3.0 y cinco contratos JS. Preview normal y preview con CSP `script-src 'none'` usan SQLite en memoria, cuentas sintéticas y settings aislados; no son endpoints del producto. Pendientes de navegador/aceptación y comandos exactos en validation.md.
