# Validación — 007 / PlanesApp

Fecha: 2026-10-06. Implementación completa autorizada por instrucción posterior: «te doy permsio de implementar todo la specs 007 alcanse completo». El propietario aclaró que el entorno se llama .venv. [Spec](spec.md), [plan](plan.md), [tareas](tasks.md), [guía para probar/configurar](../../docs/PLANESAPP_DESARROLLO.md).

Resultado: funcionalidades implementadas y pruebas de servidor correctas; validación visual ejecutada con límites manuales explícitos. **Aceptación del propietario pendiente**, sin despliegue, commit/push ni migración sobre la DB existente.

## Evidencia ejecutada

[Verificación estructurada](evidencia/verificacion.json) y [mediciones del navegador](evidencia/navegador.json). Python 3.12.14 en .venv, settings aislado core.test_settings. No se importó la entrada normal para probar ni se leyó .env/DB/media personal.

| Comando / comprobación | Resultado |
|---|---|
| `.venv/Scripts/python.exe manage.py test UsuarioApp homeApp PlanesApp --settings=core.test_settings` | **117 métodos**, 11,865 s, OK; SQLite en memoria/locmem |
| Regresión adicional del último ajuste no-store de catálogo | Un método de catálogo OK, 0,024 s |
| `manage.py check --settings=core.test_settings` | Cero problemas |
| `manage.py makemigrations --check --dry-run --settings=core.test_settings` | No changes detected |
| `python -m pip check` | No broken requirements found |
| `manage.py tailwind --settings=core.test_settings build` | Standalone **4.3.0**, OK, última compilación 69 ms |
| Ruff de PlanesApp/adapters/services/signup_forms/processor/Home | OK; N999 exceptuado por nombre solicitado y SIM117 en bloques anidados de pruebas |
| Compilación de templates y descubrimiento static | **76 HTML** cargados; card.js/planes.css encontrados |
| Migración/reversión/reaplicación aisladas | Cuatro planes / 19 beneficios; reverse seed no-op; esquema eliminado; cargo conservado; colisión bloqueada sin modificación |
| Diff y documentación | Sin errores de espacios; [16 documentos / 217 enlaces locales](evidencia/documentacion.json), cero destinos inexistentes |

Las primeras regresiones históricas esperaban signup cerrado, Home con usuarios y listado para cualquier autenticado. Se adaptaron únicamente esas expectativas por RF-007-01/12: actores operadores siguen probando dashboard/listado; cliente redirige a su resumen y recibe 403 al abrir usuarios. El resto de 004/006, MFA, fotos, jerarquía, hashing y modo persistente siguen pasando. Los errores 403/401 y fallos técnicos inyectados en logs de pruebas son escenarios esperados.

## Implementación y pruebas por requisito

| RF | Archivos y evidencia concreta |
|---|---|
| 01 | UsuarioApp/services.py, adapters.py, signup_forms.py; alta local real vía cliente Django: flags ignorados, RESTRICTED+Free+correo no verificado, duplicados/contraseña y rollback después de Profile |
| 02 | Adapters sociales/configuración/template connections; callback Google con state/PKCE real de allauth y token/perfil mock: alta, ingreso repetido conservando MANAGER, colisión sin fusión/autenticación, cancelación/error/estado inválido; SocialToken vacío. OAuth real pendiente |
| 03 | permissions.py y EmailAddress; confirmación HMAC válida/inválida/expirada/reenvío, gate de métodos/compra/renovación. TOTP/login históricos conservados |
| 04 | Plan/PlanBenefit y 0002; cuatro valores/19 beneficios, público/current/inactivo; precio no recibido desde navegador; admin conserva Free activo/cero y valores pagados positivos |
| 05 | Subscription/services.summary; Free nuevo/virtual, GET sin filas nuevas, cancelación cumplida efectiva Free, vencimiento leído por fechas |
| 06 | simulator/forms/services; lista cerrada, titular Unicode/fecha/CVC, errores sin repoblar PAN/CVC, máscaras, default único, duplicado, IDs ajenos y retiro de último método/cancelación atómicos |
| 07 | Componente tarjeta, card.js/planes.css: entrada en vivo, una tarjeta, giro al foco CVC y regreso al Tab, contraste de tokens/foco, móvil y nombre largo; formulario válido/errores con scripts bloqueados. Regla CSS de movimiento reducido inspeccionada; preferencia real pendiente |
| 08 | execute/proposal/CheckoutView; firma/actor/precio/versión/propiedad, CSRF, nonce durable/payload distinto, reenvío, fallo parcial revierte, rechazo no modifica suscripción. Navegador: Plus aprobado y Hogar rechazado conservando Plus |
| 09 | Servicios y confirmaciones; Plus→Pro y Free, plan actual no cobra; cancelación/revocación/fecha vigente, tarjetas vencidas impiden revocación. Navegador cancelación y retiro sin cambiar término |
| 10 | month_after/renovación; fin de mes, bisiesto y DST Santiago, vencimiento, idempotencia, rechazo no extiende, renovación desde now sin atrasos. Sin scheduler ni cobros por GET |
| 11 | SimulatedOperation/historial/resultado; snapshots/máscara propia, ID ajeno 404 aun root, paginación y conservación al retirar método; referencia y simulación en UI |
| 12 | Home/UserListView/helper/nav; matrices anónimo/inactivo/roles/sin perfil/cargo/root; Home redirige antes de consultar usuarios, listado 403 cliente; selector POST/CSRF persiste y vuelve a resumen |
| 13 | Registro app/rutas/@source, build, suite y estos documentos; plantilla/caché coherentes, sin servicios de vigilancia presentados como operativos |

La propuesta técnica se ajustó a archivos reales: formulario de alta transaccional en UsuarioApp/signup_forms.py, pruebas de alta/social en PlanesApp/tests.py en lugar del archivo separado previsto. Admin administra el catálogo inicial mediante permisos existentes, sin alta/borrado de planes ni nuevo panel comercial. El editor de tarjetas pasa a una columna a 1100 px para evitar comprimir la tarjeta/campos junto al menú.

## Navegador y capturas

Preview exclusivo con core.test_settings y SQLite ficticio separado, ligado a **127.0.0.1:8007**. Cuenta cliente_demo y Ana Demo, correo example.test. Sin datos personales/servicios externos. Pestaña temporal cerrada, viewport restaurado y servidor detenido al terminar.

Catálogo y métodos comprobados en modos claro/oscuro a **360, 390, 768, 1024 y 1440 px**. En todos, scrollWidth = clientWidth (restando scrollbar nativo); rejilla 1/2/4 columnas. Tarjeta a esos tamaños: datos inferiores dentro de sus bordes, nombre largo truncado solo en preview, campo completo editable. Foco y Tab verificaron giro/regreso y botón accesible. No se recibió excepción de app en esos flujos.

Con `script-src 'none'` aplicado únicamente por helper de preview ignorado, el formulario muestra errores y guarda una Mastercard. Preview permanece estático y el backend funciona sin JS; el middleware QA no se instala en la aplicación. No se probó un lector de pantalla. Giro sin transición al preferir movimiento reducido está implementado en CSS, **no probado activando esa preferencia**. La superficie de navegador no permite configurar esa preferencia/zoom: zoom 200% sigue manual, no se equipara ancho reducido con zoom.

Las capturas fullPage iniciales de la herramienta deformaban el ancho al capturar; se descartaron y reemplazaron por capturas de viewport inspeccionadas. No se atribuye ese artefacto de captura a la UI ni se entregan como evidencia visual válida.

- [Catálogo claro](evidencia/catalogo-claro-1440.png) y [oscuro](evidencia/catalogo-oscuro-1440.png).
- [Tarjeta de frente](evidencia/tarjeta-frente-oscuro.png) y [reverso](evidencia/tarjeta-reverso-oscuro.png).
- [Suscripción](evidencia/suscripcion-oscuro.png), [compra aprobada](evidencia/compra-aprobada.png), [rechazo](evidencia/compra-rechazada.png).
- [Errores móviles sin scripts](evidencia/errores-sin-js-390.png).

## Entorno, dependencias y conservación

.venv copiado no ejecutaba porque pyvenv.cfg apuntaba a Python ausente. Se conservó el archivo original en .recovery-007 y se regeneró el entorno en su ruta con runtime Python 3.12.14 disponible, sin borrar sus paquetes. pip se alineó a 26.2.1 ya declarado en requirements.in.

En el HEAD recibido de esta copia, requirements.txt contenía **51 pins sin hashes**, aunque documentación histórica de 005 describía otra entrega con 52. Se regeneró desde requirements.in con pip-tools 7.6.1 en un compilador separado ignorado: **54 paquetes con hashes**, conserva las 51 versiones previas y añade oauthlib 4.0.0, PyJWT 2.15.1 (extra socialaccount) y pip 26.2.1 del archivo fuente. Versiones instaladas coinciden exactamente con el lock. No actualización general de librerías ni auditoría nueva de vulnerabilidades; evidencia histórica OSV no certifica los dos paquetes nuevos.

No se modificaron tokens globales/tema ni políticas 004/006; solo integración cliente y estilos propios. No nueva fuente remota, Node/npm, pasarela de pago ni datos de tarjeta reales. .work-007 y el compilador temporal se retiraron al cerrar, verificando sus rutas dentro del workspace; .venv y respaldo se conservaron. La evidencia permanente está en esta spec.

## Límites y siguiente paso

1. Configurar Google con credenciales propias y ensayar OAuth real/conexión autenticada. Las pruebas mock no acreditan consentimiento, red ni configuración del proyecto Google.
2. Completar manualmente zoom 200%, preferencia reducida y aceptación del propietario. T-007-15 conserva esos pendientes; T-007-16 conserva aceptación, documentación técnica entregada.
3. Autorizar e instalar migraciones en la base de desarrollo elegida después de identificarla/resguardarla. Esta entrega no aplica migraciones reales.
4. SQLite no demuestra select_for_update/concurrencia en PostgreSQL. Hay constraints/idempotencia y conflictos/rollback cubiertos, sin prometer bloqueos no probados en otro motor.

Reversión: 0002 conserva seed/cargo por no-op; 0001 elimina tablas/historial propios. Socialaccount hacia atrás pierde vínculos Google; requiere recuperación coherente, no compensar borrando usuarios. Producción/SMTP/hosting/pagos reales necesitan otro alcance. Finalización técnica no equivale a aceptación funcional ni despliegue.
