# Validación independiente de la base reutilizable

Fecha de auditoría inicial: **2026-10-02**. Resultado histórico: **Con bloqueadores**. Correcciones posteriores de 005/006 ejecutadas y verificadas: ver actualización al final. Estado actual del alcance corregido: **sin bloqueadores detectados en lo verificado**, con evidencia operativa insuficiente para recomendar producción de un proyecto derivado. Esta base no se despliega por esta revisión. Tampoco se marca aceptación funcional.

## Alcance y versión de la auditoría inicial (histórico)

Se revisaron las specs implementadas 001–004, UsuarioApp, homeApp, theme, configuración compartida/normal/de pruebas, rutas, formularios, permisos, migraciones propias, dependencias Python, scripts CDN y documentación SDD. No existe módulo de negocio. La propuesta futura [005](../specs/005-actualizacion-dependencias/spec.md) queda excluida de la validación funcional actual.

Git: rama **main**, commit **6bc1bd484b6fd0d2eea9e1c0e6802370c069cc71**. Inicialmente solo `.codex/skills/validar-produccion-sdd/` estaba sin seguimiento; se conservó. El [manifiesto](evidencia/auditoria-20261002/baseline.json) identifica 114 archivos de código, configuración, plantillas, estilos, requisitos e instrucciones. No se modificaron esas fuentes durante la revisión.

Skill aplicada: [validar-produccion-sdd](../.codex/skills/validar-produccion-sdd/SKILL.md). Autoriza comprobaciones aisladas y documentación; establece «No implementar correcciones funcionales, modificar pruebas versionadas». AGENTS exige spec → plan → tasks antes de actualizar dependencias. Por eso esta entrega contiene diagnóstico y propuesta concreta, sin cambiar versiones ni reglas del producto.

No se abrió `.env`, DB existente, media personal ni datos reales. No hubo despliegues, commits, push, migraciones reales, SMTP o APIs de clientes. Las consultas externas enviaron únicamente nombres/versiones públicos a PyPI, npm y OSV.

## Entorno y comandos ejecutados

El Python de `.venv` no inicia porque apunta a Python312 ausente. Se creó un venv temporal **sin paquetes globales** con CPython **3.12.14** del runtime local de Codex; se instalaron exclusivamente las **47 versiones actuales de requirements.txt**. La primera descarga falló por restricción de sockets; la repetición con acceso de red revisado terminó correctamente. Este fallo inicial no demuestra que falte una versión en PyPI.

La configuración de aplicación fue exclusivamente `core.test_settings`: SQLite en memoria, correo/caché locales, media/static temporales y datos ficticios. El MD5 usado por la suite pertenece solo a ese settings. Para el diagnóstico criptográfico se sustituyeron temporalmente los hashers por los declarados en settings normal. [Versiones instaladas](evidencia/auditoria-20261002/instaladas.json).

En los siguientes comandos `python` representa el intérprete del venv temporal, no el `.venv` roto:

| Comprobación actual | Resultado | Salida / evidencia |
|---|---|---|
| `python -m pip install -r requirements.txt` en venv limpio; `python -m pip check` | Instalación correcta; sin requisitos rotos | 0; 47 paquetes de aplicación instalados |
| `python manage.py check --settings=core.test_settings` | Cero problemas | 0; [check](evidencia/auditoria-20261002/check.txt) |
| `python manage.py test UsuarioApp homeApp --settings=core.test_settings --verbosity=1` | **57 aprobadas, 0 fallidas, 0 omitidas**, 5,076 s; incluye caso MFA en subprocess | 0; [suite completa](evidencia/auditoria-20261002/tests.txt) |
| `python manage.py makemigrations --check --dry-run --settings=core.test_settings` | No changes detected; no archivos generados | 0; [esquema](evidencia/auditoria-20261002/migraciones.txt) |
| Compilar todas las plantillas de `templates/` mediante loader Django | **60 correctas** | 0; [inventario](evidencia/auditoria-20261002/plantillas.json) |
| Tailwind `build` mediante call_command, sobre copias de fuentes y AppConfig de theme apuntando a la copia | **v4.3.0**, 79 ms, **13.829 bytes idénticos** al CSS del proyecto | 0; [build](evidencia/auditoria-20261002/build-completo.txt), [hashes](evidencia/auditoria-20261002/build.json) |
| `check --deploy` mediante call_command con configuración normal reproducida en memoria | Dos advertencias: security.W005 y W021 | 0; [diagnóstico](evidencia/auditoria-20261002/diagnostico.json) |
| Diagnóstico sintético de Registro/perfil/hashers | Elevación de cargo y escrituras parciales reproducidas; Argon2 funciona, bcrypt ausente | 0; [resultados](evidencia/auditoria-20261002/diagnostico.json), [salida](evidencia/auditoria-20261002/diagnostico.txt) |
| PyPI + npm + OSV; consultas por versión exacta | 47 pins Python inventariados; avisos deduplicados y condiciones evaluadas | 0; [inventario y referencias](evidencia/auditoria-20261002/INVENTARIO_DEPENDENCIAS.md) |
| `pip install --dry-run --ignore-installed -r <candidatas-temporales>` | 47 candidatas resuelven sin conflicto en Python 3.12; **no instaladas** | 0; [resolución](evidencia/auditoria-20261002/resolucion-candidatas.txt) |
| OSV sobre esas 47 candidatas y tres versiones frontend propuestas | Sin avisos devueltos en esa consulta; no certifica seguridad ni transitivas futuras | [consulta](evidencia/auditoria-20261002/candidatas-audit.json) |
| Lectura del wheel oficial de allauth candidato, SHA-256 contrastado con PyPI | Cinco migraciones nuevas identificadas; **no ejecutadas** | [comparación](evidencia/auditoria-20261002/migraciones-allauth.json) |

El primer build aislado omitió el SVG del logo y produjo 469 bytes menos, asociados a `transform` y sus propiedades. Se corrigió únicamente el diagnóstico para incluir esa fuente; segundo build idéntico. No se reparó ni reescribió CSS de producto. Los mensajes 403/500 de la suite y del diagnóstico corresponden a denegaciones/fallos sintéticos esperados; no se confunden con tests fallidos.

Procedimientos temporales conservados como texto de evidencia, fuera de módulos/pruebas de producto: [diagnóstico](evidencia/auditoria-20261002/procedimiento-diagnostico.txt), [consulta pública](evidencia/auditoria-20261002/procedimiento-dependencias.txt) y [build aislado](evidencia/auditoria-20261002/procedimiento-build.txt). No ejecutar sobre settings normal ni datos reales.

El deploy check no importó settings normal: reprodujo DEBUG=False, host ficticio, clave sintética suficientemente larga, HTTPS obligatorio, proxy/header declarados, cookies Secure, HSTS=3600 y hashers normales. W005/W021 reflejan subdominios/preload deliberadamente desactivados; **no se recomienda activarlos sin conocer dominio y proxy**. No se probó TLS, la autenticidad del header en hosting ni configuración real de entorno.

## Navegador y evidencia anterior

Se ejecutó un preview local en `127.0.0.1:8765`, con SQLite en memoria y cuentas ficticias del helper ya existente `.recovery-004/preview.py`, inspeccionado antes de iniciarlo. Sus rutas de preparación no pertenecen al producto. Navegador en segundo plano, 1280 px:

- ADMIN abre Usuarios e Inicio; selector claro → oscuro guarda por POST, recargar mantiene oscuro; no desbordamiento de página (scrollWidth 1265, viewport 1280). [Captura sintética actual](evidencia/auditoria-20261002/inicio-oscuro.png).
- ADMIN abre formulario administrativo para RESTRICTED, con destinatario y tres campos obligatorios visibles; Cancelar vuelve a Usuarios sin introducir contraseñas.
- MANAGER no ve restablecimiento ni gestión de ADMIN/MANAGER; URL directa de restablecimiento muestra 403. Root sin cargo no tiene controles de esas acciones; Registro sigue accesible por su excepción global documentada.
- Logout vuelve al login público, con mensaje de cierre y sin navegación privada. No se ingresaron nuevas credenciales mediante navegador.

Se conservaron los resultados históricos de [002](../specs/002-renovacion-visual/validation.md), [003](../specs/003-modo-visual-usuario/validation.md) y [004](../specs/004-administracion-usuarios/validation.md). Sus capturas/contrastes sirven como antecedente; no se presentan como una nueva ejecución completa ni se cierran sus tareas pendientes. La suite actual vuelve a verificar la lógica de servidor de todas ellas. El manifiesto de esta auditoría vincula los resultados nuevos al commit indicado.

Pendientes visuales anteriores: zoom real 200 %, movimiento reducido activado en navegador, autofill, estados alternativos exhaustivos y aceptación del propietario. Envío válido de nueva contraseña por navegador requiere intervención manual conforme a la política de la herramienta; guardado, sesiones y TOTP sí pasan en servidor. No se usó esa limitación para asumir aceptación.

## Trazabilidad RF/RNF vigente

Las asociaciones no son porcentajes de cobertura. «Servidor OK» refiere a la suite actual, no a ausencia de vulnerabilidades.

| Requisito | Implementación real | Evidencia y estado |
|---|---|---|
| RF-001-01 | common_settings/test_settings | ConfiguracionAisladaTests + venv limpio; servidor OK |
| RF-001-02 | NoSignupAccountAdapter y allauth | RegistroPublicoTests GET/POST; servidor OK |
| RF-001-03/05 | mixins/processor/nav/Registro | PermisosRegistroInternoTests/NavegacionRegistroTests; acceso por actor OK; asignación de cargo no protegida, AUD-004 |
| RF-001-04 | UserCreateForm/ProfileCreateForm/UserCreateView | CreacionUsuarioTests: entradas válidas/inválidas OK; fallo posterior de perfil produce alta parcial, AUD-005 |
| RF-001-06 | theme/styles.css, @source, standalone | Build actual idéntico; OK |
| RF-001-07 | Ajustes opcionales, consola, home | Configuración/suite/Inicio actual; preservados, no activación automática de opciones |
| RF-002-01/04 | Layouts, cuenta/MFA, usuarios/errores | 60 plantillas + RenovacionUsuariosTests/RenovacionCuentaTests; UI actual acotada, revisión integral pendiente |
| RF-002-02/09 | tokens.css, guía de personalización | Código/guía inspeccionados; recoloración histórica no repetida; aceptación pendiente |
| RF-002-03/06 | nav/interfaz/foco/responsive | Navegador actual 1280 + antecedentes cinco anchos; zoom/estados exhaustivos pendientes |
| RF-002-05 | CSS/JS con prefers-reduced-motion | Inspección actual; preferencia real en navegador pendiente |
| RF-002-07 | Permisos/auth/perfil/gestión | Suite actual; acciones sustituidas por 004 verificadas según 004 |
| RF-002-08 | Home y gráfico demostrativo | RegresionInicioTests + navegador; CDN con aviso, AUD-003 |
| RF-003-01/02 | Selector/UserVisualPreference | ModoVisualTests + guardado/recarga actual; OK |
| RF-003-03/06 | VisualModeUpdateView/Form | Matriz, CSRF, propiedad, fallos/constraints; servidor OK |
| RF-003-04 | processor/base/tokens | Servidor/pantallas/MFA y navegador actual; OK en casos ejecutados |
| RF-003-05 | Paletas/contraste/QR/accesibilidad | Antecedentes preservados; revisión visual restante pendiente |
| RF-003-07 | 0002 de preferencia, regresión | MigracionModoVisualTests en DB efímera + suite; no instalación real |
| RF-004-01/05 | AdministrativePasswordForm/View/URL | Guardado sin correo, validadores/reconfirmación/CSRF/caché; servidor OK; envío válido por UI pendiente |
| RF-004-02/03/04 | permissions.py/vistas/flags | Matriz actor/destinatario actual + 403 en navegador; OK |
| RF-004-06 | atomic/update_fields/sesiones | Rollback, atributos, sesiones A/B y nuevo login/TOTP; servidor OK |
| RF-004-07 | Listado/formulario/layout/tokens | Suite/60 HTML + abrir/cancelar/roles; visual completa/aceptación pendientes |
| RNF comunes | Aislamiento, integridad, seguridad, accesibilidad y compatibilidad de 001–004 | Aislamiento confirmado; seguridad/integridad con bloqueadores; accesibilidad parcial; no certificación operativa |

## Hallazgos confirmados y riesgos

| ID | Severidad / certeza | Evidencia, condición e impacto | Corrección propuesta y bloqueo |
|---|---|---|---|
| AUD-001 | Alta; soporte/versiones confirmados | `requirements.txt` fija Django 5.1.2. Serie 5.1 fuera de soporte desde 2025-12-03; OSV devuelve 22 coincidencias distintas. Algunas requieren funciones no usadas (GeoDjango/Oracle/SQL dinámico/cache middleware). No se probó explotación de ninguna CVE | **Bloquea recomendar esta versión como base segura para derivados.** Actualizar a parche vigente de 5.2 LTS y adaptar/validar; 005 |
| AUD-002 | Alta para procesamiento de archivos; versiones confirmadas, alcance de explotación condicionado | Once paquetes Python con avisos por versión, incluyendo Pillow 11.3.0 (18), Jinja2 3.1.4 (3), requests 2.32.3 (2), urllib3 2.2.3 (8), sqlparse 0.5.1 (6). Pillow procesa imágenes subidas en `ProfileUpdateForm`/`utils/customer_img.py`; CVE-2026-25990 afecta PSD. Jinja2/cookiecutter no renderizan plantillas arbitrarias de usuarios en la web; otros avisos dependen de APIs concretas | **Pillow vulnerable en frontera de archivos bloquea recomendar la base sin remediación.** Actualizar/revisar parsers y transitivas; regresión con archivos ficticios acotados, sin payloads de corrupción nativa. No afirmar que todos los avisos son alcanzables; 005 |
| AUD-003 | Media; versiones/URLs confirmadas; XSS no demostrado | `base.html:17–18`: Alpine `3.x.x` flotante y DOMPurify 3.1.5, sin integrity. `index.html:42`: ECharts 6.0.0. OSV: 20 coincidencias DOMPurify y una ECharts. El gráfico usa datos estáticos; modal.js conserva sanitize pero no se carga en los layouts inspeccionados | Actualizar/fijar versiones y procedencia; SRI con bytes exactos o recursos locales verificados. **Bloquea cerrar la cadena de suministro de la base**; no se atribuye XSS activo sin entrada controlable. 005 |
| AUD-004 | Alta; reproducido | `UsuarioApp/forms.py:102` excluye solo pk=1; `views.py:182–201` admite MANAGER. Con ADMIN pk=2, POST de MANAGER crea usuario de cargo ADMIN (302), sin staff/root pero con facultad de restablecer cuentas inferiores | **Bloqueador de privilegios.** Política de cargos asignables por actor, por código y servidor. 004 excluyó Registro: no alterar su spec ni asumir nueva política de altas; requiere alcance propio y acuerdo sobre quién puede crear ADMIN |
| AUD-005 | Alta para integridad de alta; reproducido | `views.py:198–201`: fallo sintético de Profile.save devuelve 500 y deja User sin Profile. `views.py:231–239`: fallo al guardar foto conserva cambios de User y vuelve con 302/error. Guardados secuenciales sin atomicidad; límite ya documentado en 001 | **Alta parcial bloquea recomendar integridad completa de la base.** Especificar transacción User/Profile y ciclo de archivos/recuperación; no basta envolver imágenes en atomic. Fuera de 005; diagnóstico no es regresión introducida por 004 |
| AUD-006 | Media; biblioteca ausente confirmada, uso heredado desconocido | `core/settings.py:40` ofrece BCryptSHA256PasswordHasher, pero instalación limpia no contiene bcrypt. Diagnóstico lanza ValueError; Argon2 sí verifica correctamente. No se inspeccionaron hashes reales | Bloquea compatibilidad **si hay hashes bcrypt heredados**; no falla el alta Argon2 comprobada. Declarar bcrypt compatible y probar todos los hashers normales sin retirar soporte; 005 |
| AUD-007 | Media; estático confirmado | common_settings usa DefaultMFAAdapter; allauth 0.62.1 encrypt/decrypt devuelven texto sin cifrar. Una copia de DB expuesta puede revelar semillas TOTP. No se accedió a semillas reales | Definir protección de DB/backups/semillas y manejo de claves por producto. No cambiar adapter ni migrar secretos automáticamente en 005; riesgo dependiente del entorno |
| AUD-008 | Media; riesgo de arquitectura/abuso por verificar | allauth conserva rate limits (login_failed 5/300s/key y 10/m/ip); axes desactivado no significa ausencia total de protección. Caché normal por defecto local por proceso; formulario administrativo propio no añade límite de reconfirmación. Proxy/worker reales desconocidos | Verificar IP fiable, caché compartida y límites por acción según hosting. No activar axes por inferencia. Compatibilidad del nuevo allauth con proxy debe documentarse en 005; protección de abuso adicional requiere alcance propio |
| AUD-009 | Media; ausencia de política observable | LOGGING normal WARNING/consola; 004 excluye historial persistente. No se acreditan eventos de éxito de login/restablecimiento con actor/destinatario, retención o alertas; errores/403 sí salen en diagnósticos | Definir eventos sin credenciales, acceso/retención y alertas por producto. **Pendiente operativa**, no incumplimiento inventado de RF-004 ni permiso para crear módulo de auditoría |
| AUD-010 | Media; reproducido | `.venv/pyvenv.cfg` apunta a Python312 inexistente; comandos del intérprete no inician. El venv limpio de auditoría sí funciona | Documentar/recrear entorno propio después de autorización, conservando el anterior hasta verificar. 005; no confundir con fallo del código ni con conflicto cffi/cryptography global: ese conflicto no apareció en aislamiento limpio |

Además: cargas tienen límite de 5 MiB, pero no un presupuesto explícito de dimensiones/tiempo de decodificación; Pillow tiene controles propios y aquí no se certifica resistencia a agotamiento. Upload/storage utiliza `.path` y procesamiento local: no acredita S3. User email y EmailAddress tienen flujos distintos; no se establece una política nueva de unicidad/edición/identidad por esta auditoría. Revisar estos contratos en alcance propio antes de reutilizar en proyectos sensibles.

## Dependencias: resultado y propuesta

**47 pins Python, 38 con una versión publicada posterior.** OSV devolvió 146 registros brutos; al unir aliases y excluir retirados quedan **88 coincidencias distintas por paquete/versión**: 67 Python, 21 JavaScript. No son 88 fallos explotables confirmados. En particular los tres avisos de allauth coinciden por rango, pero sus condiciones (SAML/IdP/Okta/NetIQ) no están habilitadas en esta base; dos afectan funcionalidades incorporadas después de 0.62.1. Se proponen actualizaciones por mantenimiento/compatibilidad y avisos oficiales adicionales, no por fingir esos ataques en el proyecto.

Candidatas principales: Django **5.2.17 LTS**, allauth **65.19.7**, Pillow **12.3.0**, requests **2.34.2**, urllib3 **2.8.0**, Jinja2 **3.1.6**, sqlparse **0.6.0**, crispy-forms **2.7**, environ **0.14.0**; DOMPurify **3.4.16**, ECharts **6.1.0**, Alpine **3.17.4**. Detalle de todos los pins, herramientas/opcionales y referencias en el inventario. Tailwind standalone **4.3.0**, django-tailwind **4.5.0** y crispy-tailwind **1.0.3** se conservan al no detectarse necesidad de cambiarlos en esta consulta.

Las 47 candidatas resuelven y su consulta OSV no devuelve avisos; **no se instalaron ni se ejecutó la suite con ellas**. El plan incorpora bcrypt y evaluación de los extras realmente necesarios de MFA; todas las nuevas transitivas deberán revisarse antes de cerrar versiones. Un lock reproducible, separar instalación de aplicación de herramientas/opcionales y revisar mensualmente avisos son propuestas de 005, no tareas programadas ni actualización automática de proyectos ya derivados.

**Decisión crítica P-005-01:** allauth 65.19.7 incorpora `account.0006` (correos en minúsculas, reversión noop), `0007` (índice/campo), `0008` (elige principal y desmarca extras, reversión noop), `0009` (único principal por usuario) y `mfa.0003` (restricción condicional por tipo). Esto afecta datos, no solo librerías. No ejecutar el cambio hasta revisar/aceptar esos efectos y ensayar colisiones/duplicados en datos sintéticos. Revertir código o hacer migrate backwards no recupera mayúsculas ni las selecciones anteriores; se necesita respaldo/restauración del entorno autorizado. No se inspeccionaron datos reales para resolverlo.

## OWASP Top 10:2025 y ASVS

Se usaron [Top 10:2025 oficial](https://top10.owasp.org/2025/) y [ASVS **5.0.0**, CSV de la etiqueta estable](https://github.com/OWASP/ASVS/raw/v5.0.0/5.0/docs_en/OWASP_Application_Security_Verification_Standard_5.0.0_en.csv). Los IDs siguientes se contrastaron con esa edición. Se seleccionan controles pertinentes; no se afirma cumplimiento integral ni nivel ASVS.

| Categoría | Estado | Evidencia y límites |
|---|---|---|
| A01 Control de acceso | Parcialmente revisada; hallazgo | Matriz 004 en servidor/403 navegador; Registro permite elevar cargo (AUD-004). ASVS v5.0.0-8.2.1/8.2.2 |
| A02 Configuración | Parcialmente revisada | Deploy simulado, DEBUG/hosts/cookies/middleware; proxy/TLS real sin comprobar. v5.0.0-13.4.2 |
| A03 Cadena de suministro | Revisada en dependencias declaradas; bloqueadores | Versiones/avisos/build y resolución; sin lock de integridad ni runtime de producción. v5.0.0-15.1.1/15.1.2/15.2.4 |
| A04 Criptografía | Parcialmente revisada | Argon2 sintético OK; bcrypt ausente, semillas MFA sin adapter de cifrado; claves/TLS externos no comprobados. v5.0.0-11.4.2 |
| A05 Inyección | Parcialmente revisada | Consultas ORM y escaping/HTML de suite; sin SQL manual/eval/deserialización insegura observados en código propio; avisos de parsers/JS. No pentest exhaustivo |
| A06 Diseño inseguro | Parcialmente revisada; hallazgos | Separación de roles por acción y recuperación segura; asignación de cargo, guardados parciales y límites de recursos por precisar. v5.0.0-15.3.3 |
| A07 Autenticación | Parcialmente revisada | Login/reset/TOTP/sesiones actuales; allauth con límites propios inspeccionados; abuso/proxy/caché multiproceso no comprobados |
| A08 Integridad | Parcialmente revisada; hallazgos | Rollback 003/004, migración propia efímera, checksum wheel y build; Registro parcial, CDN sin integridad y migraciones de datos futuras |
| A09 Registros y alertas | Parcialmente revisada | Errores sensibles protegidos en 004; consola actual; eventos/alertas/retención por definir. v5.0.0-16.3.1/16.3.3 |
| A10 Condiciones excepcionales | Parcialmente revisada; hallazgo | Rollback y mensajes 003/004 OK; fallo posterior de Registro/perfil reproducido; límites de archivos/DB real sin estrés. v5.0.0-16.5.1/16.5.3 |

ASVS v5.0.0-14.3.2 respalda la revisión de no-store del formulario administrativo (suite); v5.0.0-15.4.2 orienta la revisión de atomicidad. SQLite no comprueba select_for_update ni revocación de cargos concurrente con otros escritores. No hay tenants, pagos, exportaciones PDF, colas, API de negocio ni SSO activo: no se inventan escenarios de esas funciones.

## Preparación operativa y cierre

| Área | Situación / criterio pendiente |
|---|---|
| Migraciones | 0002 propia probada/revertida solo en DB sintética. Estado instalado real desconocido. Migraciones futuras allauth requieren acuerdo/ensayo; no se ejecutan por esta revisión |
| Estáticos/media | Build reproducido y CSS idéntico. collectstatic/servidor de archivos/permisos HTTP de media sin probar en hosting; cargas acotadas y librería vulnerable requieren remediación |
| HTTPS/proxy/cookies | Defaults normales razonables y deploy simulado; trust boundary, certificados y cabeceras reales pendientes |
| Respaldos/restauración/reversión | No se ensayó recuperación de DB/media de un entorno de destino. Snapshot de código no restaura contraseñas/correos/archivos. Definir procedimiento por derivado |
| Observabilidad/abuso/recursos | No pruebas de carga, memoria de decodificación, concurrencia multiproceso, caché compartida, alerta o timeouts de hosting |
| Correo/MFA | SMTP no configurado y verificación none son decisiones opcionales existentes, no defectos automáticamente. Probar proveedor y política de autenticación cuando se habiliten |
| Accesibilidad/aceptación | Mantener tareas parciales 002/003/004; no dar aceptación del propietario ni dar por completo el envío de credenciales en navegador |

La auditoría termina **Con bloqueadores** (AUD-001 a AUD-005 según condiciones indicadas), además de evidencia operativa insuficiente. No se recomienda congelar esta versión como base segura para nuevos productos hasta corregirlos y repetir la revisión pertinente. No se infiere que un proyecto derivado desplegado esté comprometido.

Siguiente paso: revisar [spec 005](../specs/005-actualizacion-dependencias/spec.md), [plan](../specs/005-actualizacion-dependencias/plan.md) y [tareas pendientes](../specs/005-actualizacion-dependencias/tasks.md), resolver P-005-01 y autorizar posteriormente su implementación. AUD-004/005 requieren un alcance funcional independiente; actualizar librerías no los corrige. No repetir P-004-01/02 ya resueltas.

Fuentes primarias: [soporte Django](https://www.djangoproject.com/download/), [avisos Django](https://docs.djangoproject.com/en/5.2/releases/security/), [allauth 2026](https://docs.allauth.org/en/dev/release-notes/recent.html), [allauth 2025](https://docs.allauth.org/en/latest/release-notes/2025.html), [Pillow/PSD](https://github.com/python-pillow/Pillow/security/advisories/GHSA-cfh3-3jmp-rvhc), [bcrypt](https://pypi.org/project/bcrypt/). El inventario conserva enlaces por paquete y aviso con rangos/referencias en JSON. La vigencia de las consultas queda limitada al 2026-10-02.

Cierre: preview detenido (sesión de ejecución finalizada por interrupción controlada), pestaña temporal cerrada y venv/copia de build/diagnósticos temporales retirados tras verificar su ruta dentro del workspace. Se conserva evidencia sintética y Markdown. [Conservación y enlaces](evidencia/auditoria-20261002/cierre.json); no se modificó la skill nueva del propietario.

## Actualización posterior: correcciones autorizadas 005/006 — 2026-10-02

Esta sección corresponde a implementación posterior, autorizada por el propietario después de la revisión; no modifica la evidencia ni las conclusiones históricas sobre 6bc1bd4. P-005-01 y P-006-01 resueltas expresamente; 006 documentada/entregada antes de su autorización de código. Opcionales instalados/comentados según instrucción explícita.

| Hallazgo estable | Estado después de corrección | Evidencia / límite |
|---|---|---|
| AUD-001 | Corregido: Django 5.2.17 LTS | Lock/hashes/instalación y suite actual; soporte consultado en fuente oficial |
| AUD-002 | Corregido para versiones instaladas verificadas | 52 paquetes Python con hashes, transitivas/extras/instalador incluidos; OSV sin coincidencias actuales, no garantía futura |
| AUD-003 | Corregido | Tres JS exactos/SRI, descarga/verificación de bytes; gráfico/menú y fallo CDN en navegador |
| AUD-004 | Corregido en Registro de UsuarioApp, con regla aprobada | Matriz 35 POSTs/IDs arbitrarios/root por cargo, formulario y menú coherentes; no redefine Django admin |
| AUD-005 | Corregido en alta/edición y fotos evaluadas | Transacciones, compensación, foto anterior tras commit; fallos DB/storage/imagen y caso inesperado, longitud máxima; limpieza caída/storage externo tiene límites operativos documentados |
| AUD-006 | Corregido | bcrypt instalado y cinco hashers con Unicode/longitud/actualización Argon2; MD5 solo test |
| AUD-007 | Pendiente de decisión por producto | Cifrado/rotación de semillas, custodia DB/backups; no alterar MFA existente por inferencia |
| AUD-008 | Pendiente del despliegue/producto | Rate limits allauth existentes, cache compartida/proxy y limitación adicional del reset; no activar axes contra preferencia del propietario |
| AUD-009 | Pendiente de política operativa | Autor/retención/alertas/registro de acciones; sin crear módulo adicional |
| AUD-010 | Mitigado con entorno alternativo | .venv-actualizada Python 3.12.14 limpio listo; .venv roto conservado, seleccionar intérprete nuevo |

**76 tests correctos**, cero fallidos/omitidos: 57 recibidos + 6 dependencias + 13 integridad. Login/MFA/recovery/correo/permisos/sesiones/modo conservados, no se habilita socialaccount ni se elimina prueba de cascada. Check/pip check/esquema OK, 61 templates incluyendo theme; Tailwind 4.3.0 CSS idéntico; deploy simulado con W005/W021 por contexto del dominio, sin silenciar advertencias. Consulta actual: 52 distribuciones Python + tres npm, cero registros devueltos. El nuevo instalador se incluyó tras detectar avisos en pip 25.0.1 y actualizarlo a 26.2.1.

Migración old→new, normalización/principal único/factores/preferencias/hashes, código recovery generado en 0.62.1 usado tras upgrade y restauración del respaldo con paquetes antiguos: OK en fixtures SQLite. Preflight de solo lectura bloqueó colisión sin cambios; prueba adicional bloquea tipo MFA desconocido. No operar bases reales ni resolver datos de clientes. Backfills noop no recuperan estado anterior mediante downgrade de esquema.

Navegador con datos ficticios: scripts/SRI/gráfico/modos/menús, Registro por cargo, root sin cargo sin enlace, listado/MFA y móvil; CDN bloqueado preserva navegación y muestra aviso. Pasos de entrada/guardado de credencial nueva por UI son manuales por política de la herramienta; guardado en servidor comprobado. No se cierra aceptación ni las tareas manuales históricas del propietario.

Conclusión actual: **sin bloqueadores detectados en el alcance corregido y verificado**, con evidencia operativa insuficiente para recomendar producción. Preparación real de cada derivado (TLS/proxy/cache, límites/concurrencia, cifrado, logs, respaldos/restauración y datos) necesita su contexto y autorización. Axes/concurrentlogins siguen disponibles y comentados. Sin deploy/commit/push, nuevas migraciones propias, DB real/.env/media personal ni modificaciones a otros proyectos.

[Resultados 005](../specs/005-actualizacion-dependencias/validation.md), [006](../specs/006-integridad-registro/validation.md), [mantenimiento](DEPENDENCIAS.md), [evidencia actual](evidencia/actualizacion-20261002/verificacion.json). El cierre identifica hashes y cambios respecto del estado previo a implementar, incluyendo documentos locales conservados.
