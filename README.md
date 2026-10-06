# Base Django reutilizable con SDD

Base personalizada para iniciar plataformas y añadir módulos progresivamente. Conserva usuarios, perfiles/cargos, autenticación allauth, MFA, inicio, navegación y diseño Tailwind/crispy. La spec transversal CalidadBase añadió configuración aislada y pruebas iniciales; todavía no existe un módulo de negocio.

**Para comenzar:** lee [MANUAL_SDD.md](MANUAL_SDD.md). Indica primero el nombre del módulo (por ejemplo `NuevaAPP`) y después tus requisitos. La primera respuesta debe crear especificación, plan y tareas **sin código**.

Esta copia Base-2 incorpora la [renovación visual integral 002](specs/002-renovacion-visual/spec.md): espacio claro, navegación compacta, formularios/cuenta/MFA coherentes y colores centralizados. Para cambiar la marca, edita [static/css/tokens.css](static/css/tokens.css) siguiendo la [guía de personalización](docs/PERSONALIZACION_VISUAL.md). Implementación autorizada y ejecutada; 27 pruebas Django y compilación correctas. [Validación y límites](specs/002-renovacion-visual/validation.md): quedan revisión de zoom/preferencia reducida en navegador y aceptación del propietario. No contiene un módulo de negocio nuevo.

## Documentos

Ampliación [003 — Modo claro/oscuro por usuario](specs/003-modo-visual-usuario/spec.md) autorizada e implementada: botón de sol/luna en Inicio y preferencia persistente por cuenta. 43 tests, build y 180 contrastes correctos; [validación visual parcial y aceptación pendientes](specs/003-modo-visual-usuario/validation.md). Migración 0002 creada/probada solo en SQLite efímero: **no aplicada a la base existente**, necesita autorización separada de entorno/respaldo antes de usar allí el guardado. Marca clara/oscura configurable en el único archivo de tokens.

UsuarioApp incorpora [004 — Restablecimiento administrativo y jerarquía](specs/004-administracion-usuarios/spec.md): ADMIN restablece contraseñas de inferiores sin correo; ADMIN activa/desactiva MANAGER/RESTRICTED y MANAGER solo RESTRICTED. Superusuario también requiere cargo para estas acciones. Implementación autorizada, 57 tests y build correctos; [validación y revisión manual pendiente](specs/004-administracion-usuarios/validation.md). Sin migraciones nuevas ni cambios a registro/correo/MFA/modo visual.

| Necesidad | Archivo |
|---|---|
| Principios generales reutilizables | [constitution.md](constitution.md) |
| Instrucciones del agente y convenciones Django | [AGENTS.md](AGENTS.md) |
| Manual con mensajes listos para usar | [MANUAL_SDD.md](MANUAL_SDD.md) |
| Selección de prompts o uso paso a paso | [prompts/README.md](prompts/README.md) |
| Identidad y alcance del proyecto derivado | [docs/PROYECTO.md](docs/PROYECTO.md) |
| Estado y punto de reanudación | [docs/ESTADO_PROYECTO.md](docs/ESTADO_PROYECTO.md) |
| Mapa técnico de la base | [docs/ARQUITECTURA_BASE.md](docs/ARQUITECTURA_BASE.md) |
| Cambiar colores y reutilizar componentes | [docs/PERSONALIZACION_VISUAL.md](docs/PERSONALIZACION_VISUAL.md) |
| Entorno y comprobaciones | [docs/ENTORNO_Y_VERIFICACION.md](docs/ENTORNO_Y_VERIFICACION.md) |
| Observaciones de la base recibida | [docs/OBSERVACIONES_BASE.md](docs/OBSERVACIONES_BASE.md) |
| Ideas futuras no autorizadas | [docs/ROADMAP.md](docs/ROADMAP.md) |
| Registro resumido de verificaciones | [docs/VERIFICACION.md](docs/VERIFICACION.md) |
| Requisitos por módulo y plantillas | [specs/README.md](specs/README.md) |
| Decisiones y relación requisitos/pruebas | [docs/DECISIONES.md](docs/DECISIONES.md), [docs/TRAZABILIDAD.md](docs/TRAZABILIDAD.md) |
| Verificación documental inicial y validación de CalidadBase | [docs/VALIDACION_SDD.md](docs/VALIDACION_SDD.md), [spec 001](specs/001-calidad-seguridad-base/validation.md) |

## Uso repetido

Conserva esta copia como base maestra y crea un proyecto/carpeta independiente para cada producto. Mantén constitución, convenciones, manual y plantillas. En cada derivado completa su identidad, estado, decisiones y specs con los requisitos de ese producto.

No reutilices entre clientes bases de datos, secretos, archivos personales, historial funcional ni reglas de negocio. No sobrescribas documentación ya personalizada al actualizar la base.

## Alcance de la entrega

La base incorpora documentación SDD y la spec transversal 001-CalidadBase. Esta última no agrega migraciones ni despliegue: separa configuración común/pruebas, agrega casos funcionales, alinea el enlace Registro con el servidor y amplía el escaneo Tailwind. No incluye secretos, bases de prueba persistentes, dependencias instaladas ni subidas personales. Se conserva `media/profile.webp` como recurso predeterminado.

Dependencias actuales: Django 5.2.17 LTS, allauth 65.19.7, django-tailwind 4.5.0 y Tailwind 4.3.0 standalone, sin Node.js. Entradas clasificadas y lock con hashes: [guía de dependencias](docs/DEPENDENCIAS.md). Correcciones 005/006 autorizadas y verificadas con 76 pruebas; permisos de Registro por cargo y guardado transaccional de usuario/perfil/fotografía. Migraciones solo ensayadas con datos ficticios; ninguna aplicación a la base real.

django-axes y preventconcurrentlogins siguen desactivados aunque estén declarados. Las pruebas cubren la spec 001 y no certifican módulos futuros: ver observaciones. No trasladar aquí reglas de otro sistema.

## Flujo

Nombre del módulo y requerimiento → spec → plan → tareas → revisión del usuario → autorización de código → implementación → validación → actualización documental.

Puedes usar un único prompt para coordinar la fase documental o pasar cada fase por separado. El manual explica ambos casos. No es necesario instalar un framework SDD.
