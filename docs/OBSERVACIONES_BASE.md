# Observaciones del código recibido

Inspección estática del 2026-09-20. Estas observaciones no son tareas autorizadas ni una auditoría completa. No se modificó el código para resolverlas.

| Observación contrastada                                                                              | Consecuencia para un proyecto nuevo                                                                                       |
| ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| UsuarioApp y homeApp tienen 15 pruebas funcionales de CalidadBase                                    | Extenderlas por cada módulo; esta cobertura no sustituye pruebas de requisitos futuros                                    |
| core/test_settings.py aísla DB, correo, caché, hashers, hosts, seguridad HTTP y archivos temporales | Ejecutar siempre las pruebas con `--settings=core.test_settings`                                                           |
| django-axes y preventconcurrentlogins figuran en dependencias pero están comentados en configuración | No afirmar que esas protecciones están activas por estar instaladas                                                       |
| El correo usa backend de consola y ACCOUNT_EMAIL_VERIFICATION es none                                | Definir correo real/verificación cuando el producto los necesite                                                          |
| El helper de cargo y el enlace Registro comparten política mediante un context processor             | Conservar la fuente única y probar vista/HTML al cambiar roles o navegación                                                |
| El gráfico del inicio contiene datos de ejemplo                                                      | No presentarlo como información real del módulo nuevo                                                                     |
| Tailwind 4 standalone escanea HTML, JavaScript y Python propios mediante `@source`                    | Registrar raíces de apps futuras; usar clases completas o `@source inline()` finito y excluir generados/dependencias       |

MFA está configurado mediante allauth; eso no demuestra que todos los usuarios lo tengan activado. La base contiene mecanismos de seguridad y decisiones pendientes de cada instalación, no una certificación de estar lista para cualquier despliegue.

Si una observación entra en el alcance de un pedido, abrir/actualizar su spec, plan y tareas. No «corregir todo» durante la creación de otro módulo.

El `.venv` inspeccionado el 2026-09-20 apunta a una instalación Python 3.12 inexistente. La validación de CalidadBase usó el runtime Python de Codex y dependencias temporales instaladas desde requirements.txt; esa carpeta se eliminó al terminar. Reparar o recrear el entorno virtual local es una tarea de entorno, no un cambio funcional de la spec 001.

## Inspección de Base-2 — 2026-10-02

Observaciones estáticas para la [spec 002](../specs/002-renovacion-visual/spec.md), sin ejecución funcional ni auditoría nueva:

| Observación | Tratamiento propuesto |
|---|---|
| Esta copia no contiene repositorio Git | Preparar recuperación acotada antes de implementar; no afirmar que se dispone de diff contra la base principal |
| Paleta repartida entre HTML, CSS, widget de cargo y gráfico | Centralizar tokens y probar cambio completo de marca |
| Mensajes tienen selector global button y colores propios; el gráfico fija texto claro | Acotar estilos y consumir tokens compartidos |
| Desplegable de cuenta tiene aria-expanded fijo y enlaces con tabindex=-1 | Revisar patrón de teclado/estado/foco, sin declarar accesibilidad verificada por inspección |
| Panel móvil incluye transiciones y x-cloak, sin gestión completa de foco visible en el layout | Verificar y completar foco, Escape, fondo inerte y liberación de scroll |
| Visibilidad de activar/desactivar compara RESTRICTED; autorización del servidor usa helper/mixin | Alinear controles con la política existente sin cambiar privilegios |

La inspección anterior pertenece a DOCUMENTAR. Después de la autorización posterior se implementaron tokens, estilos acotados, gestión de foco y controles con el helper. Suite ampliada: 27 pruebas correctas. [Resultados y límites](../specs/002-renovacion-visual/validation.md); aceptación del propietario pendiente.

La limitación de `.venv` se reprodujo: apunta a Python 3.12 inexistente. La verificación usó runtime disponible de Codex y dependencias aisladas exactas de requirements.txt. No se reparó el entorno del propietario ni se actualizaron dependencias. En aquella fase la copia no tenía Git; snapshot acotado en `.recovery-002/`.

## Inspección inicial para 003 — 2026-10-02, antecedente documental

- Ahora Git está disponible en main con numerosos cambios locales de 002 y archivos sin seguimiento. Esta observación posterior sustituye la ausencia de Git como descripción del estado actual, conservando la evidencia histórica anterior.
- No existe selector claro/oscuro ni persistencia de modo. El nuevo pedido está solo documentado en [003](../specs/003-modo-visual-usuario/spec.md); estaba excluido de 002.
- Profile.save procesa la foto también al guardar atributos, y hay cuentas que pueden carecer de perfil. La propuesta separa su preferencia visual en UsuarioApp, sin disparar ese guardado ni crear perfiles.
- El gráfico lee tokens al inicializar y styles.css fija color-scheme light. El plan reutiliza esos contratos y propone variantes oscuras; no se han modificado ni comprobado funcionalmente en esta fase.

Después de la instrucción posterior explícita se implementó 003: preferencia propia, POST/CSRF, selector y tokens. Suite 43 OK, 180 contrastes y navegador; gráfico reutilizado sin cambios. Hover ciruela oscuro y QR corregidos tras medir/inspeccionar. [Evidencia y pendientes](../specs/003-modo-visual-usuario/validation.md). La migración solo se aplicó/revirtió en SQLite efímero; no sobre la base existente. `.venv` sigue roto y no se reparó.

## Inspección para 004 — 2026-10-02, DOCUMENTAR

- Git main/8f9adda, árbol limpio al comenzar; esta observación sustituye como descripción actual los estados anteriores, conservados como históricos.
- Activar/desactivar aún autorizan al actor con PermitsPositionMixin, sin comparar jerarquía del destinatario. Desactivar protege propia cuenta/root; activar no tiene esas comprobaciones. No existe restablecimiento administrativo local.
- En el ZIP de referencia, permissions.py exige cargo incluso al root; difiere del helper de esta base. P-004-01 consultada y confirmada por el propietario: exigir cargo incluso al superusuario para restablecer/activar/desactivar. No se adopta por lectura del ZIP ni modifica todavía el código/globales.
- Referencia contiene formulario con reconfirmación del operador, auditoría, cambios de registro/fotos/perfil/recuperación pública y dependencia FruticulaApp. Solo se toma la guía del flujo solicitado; los otros cambios se excluyen.
- Propietario confirmó P-004-01/02: cargo incluso al root y misma jerarquía al activar/desactivar. Nueva política documentada en [004](../specs/004-administracion-usuarios/spec.md), todavía sin código ni pruebas funcionales. Privilegios de otras superficies no se alteran por esta propuesta.

## Auditoría independiente — 2026-10-02, estado posterior a 004

Las descripciones documentales anteriores son históricas. En main/6bc1bd4 están implementadas 001–004 y sus 57 pruebas pasan actualmente. [Informe vigente](VALIDACION_PREPRODUCCION.md): dependencias antiguas/fuera de soporte; MANAGER crea ADMIN si el cargo no tiene pk=1; fallo de Profile deja alta parcial. Reproducido solo con datos ficticios, sin correcciones. Aislamiento limpio confirma Argon2 y ausencia de bcrypt para el hasher configurado; no reproduce el conflicto del entorno global de verificaciones previas.

005 documenta actualización de dependencias con P-005-01 pendiente por migraciones de allauth. No modifica permisos de Registro ni integridad de fotos/perfiles. No confundir 57 tests verdes, resolución de candidatas o documentos nuevos con seguridad integral, implementación de 005 o aceptación del propietario.

Después de revisar documentos, autorizó por instrucción posterior el alcance completo y se implementó 004. 57 tests/check/esquema/build/60 HTML OK; listado/formulario cinco anchos/claro/oscuro, gestión de RESTRICTED por MANAGER y ausencia de acciones root sin cargo en navegador. Envío válido de nueva contraseña por interfaz y aceptación funcional pendientes; guardado/sesiones/MFA comprobados en servidor. [Detalle](../specs/004-administracion-usuarios/validation.md).

La nueva prueba de reingreso MFA expuso un efecto de allauth 0.62.1: su Login.deserialize importa SocialLogin y registra modelos de socialaccount desactivado, afectando una cascada posterior de la suite. El caso se verifica en proceso aislado con core.test_settings para no contaminar otros modelos; no se habilitó integración ni cambió configuración/dependencias. La prueba de eliminación histórica de 003 se preservó. .venv sigue roto; verificación mediante dependencias exactas temporales/runtime, sin tocar bases reales.

## Estado después de correcciones autorizadas — 2026-10-02

Las observaciones anteriores son históricas. 005 actualiza dependencias y completa bcrypt/lock/SRI; 006 corrige Registro por cargos e integridad User/Profile/fotos con regla y alcance confirmados. 76 tests actuales correctos; OSV de 52 paquetes Python/tres JS no devuelve coincidencias. .venv original sigue intacto/roto, alternativa .venv-actualizada verificada. Core/settings normal y capacidades opcionales comentadas preservados. Ver [estado](ESTADO_PROYECTO.md), [guía](DEPENDENCIAS.md) y validaciones 005/006; no implica producción ni aceptación.

## Inspección de esta copia para 007 — 2026-10-06

Git limpio inicial HEAD 69b2eb4; PlanesApp no existe, siguiente libre 007. Adapter y signup bloquean alta pública; common_settings mantiene socialaccount desactivado y es la fuente real LOCAL_APPS. Home/listado solo requieren autenticación y el menú Usuarios es incondicional: abrir registro obliga a definir privacidad del cliente en [007](../specs/007-planes-app/spec.md), todavía propuesta.

La ruta histórica `.venv-actualizada` **no existe en esta carpeta** (lecturas de archivos de paquetes fallidas); solo se observó `.venv`, sin importación ni runtime comprobado. Evidencia de 76 tests/dependencias pertenece a la entrega anterior, no una ejecución aquí. En DOCUMENTAR no se instalaron paquetes ni se ejecutaron tests/build/migraciones; no se leyó .env/DB/media personal. Diseño reutilizará tokens/tema existentes conforme a frontend-design. No interpretar este diagnóstico como autorización de corregir todo o implementar 007.

## Resultado posterior de 007 — 2026-10-06

La inspección anterior pertenece a DOCUMENTAR. El propietario autorizó después todo 007 y confirmó .venv como entorno. Implementadas alta pública RESTRICTED/Free, Google, privacidad y suscripciones simuladas; 117 tests OK, check/esquema/pip/build/76 HTML y navegador parcial. .venv copiado apuntaba a Python ausente; reconstruido conservando paquetes, configuración original resguardada. HEAD contenía 51 pins sin hashes, distintos del relato histórico de la entrega 005; lock actual de 54 paquetes con hashes conserva versiones y añade extra socialaccount/pip declarado. [Evidencia y límites](../specs/007-planes-app/validation.md). No leída/migrada DB real; OAuth real, revisiones manuales/aceptación pendientes.

## Inspección para 008 — 2026-10-06, DOCUMENTAR

Git tiene cambios locales implementados en 007 que se preservan; carpeta siguiente libre 008. Inicio redirige clientes antes de consultar datos, pero nav aún muestra el enlace. Los cuatro enlaces de suscripciones y Correo/Google carecen de SVG; selector en Mi suscripción usa glifos, distinto del sol/luna SVG de index. Home conserva accesos reales y gráfico meteorológico demostrativo. Estos hechos motivan [008](../specs/008-dashboard-navegacion/spec.md), todavía sin código.

El dashboard agregado es una ampliación funcional documentada por separado, no un cambio de las reglas comerciales 007. No se ejecutaron suite/build/migraciones ni se leyó DB/.env/media personal; los resultados anteriores no verifican esta propuesta. Las capturas aportan ejemplos de controles solicitados, sin instrucciones independientes del pedido humano.

## Resultado posterior de 008 — 2026-10-06

El antecedente DOCUMENTAR anterior se conserva; el propietario autorizó después la implementación completa. Se corrigieron seis enlaces sin SVG, Inicio visible a clientes y glifos del selector; Home reemplaza datos meteorológicos por agregados reales del prototipo. Navegador expuso la necesidad de scroll interno para últimos enlaces en ventanas bajas; ajuste acotado más details/noscript móvil para RF-008-06. Reglas de cuentas/planes anteriores preservadas.

127 tests OK, check/esquema/Ruff/JS/build/77 HTML correctos; cinco anchos/dos modos, permisos, teclado y fallback/vacío con 18 JPEG válidos. [Resultados y límites](../specs/008-dashboard-navegacion/validation.md). No usar inspección estática del modo reducido ni cambio de viewport como evidencia de zoom nativo: ambos pendientes manuales. Preview en memoria y temporales retirados, sin datos reales/migración/commit/push/despliegue.
