# Identidad del proyecto

**VIGIA** apoya el cuidado domiciliario de personas con dependencia (Proyecto de Título, INACAP). Componentes: portal y backend Django (`web/`), app Flutter (`mobile/`: Android primero e iOS en el alcance por D-068, compilado en macOS) y nodo Edge con MediaPipe (`edge/`), que envía solo metadatos.

| Campo | Valor actual (2026-10-25) |
|---|---|
| Nombre del producto | VIGIA |
| Specs vigentes | [010 app móvil](../specs/010-aplicacion-movil/spec.md), [011 ecosistema instalable](../specs/011-ecosistema-instalable/spec.md), [012 detección de caídas](../specs/012-deteccion-caidas/spec.md). Base 001–009 conservada |
| Usuarios | Hoy una cuenta dueña configura y opera sus pacientes. Decidido (D-050, sin implementar): familiar que configura y supervisa, cuidador que ejecuta, con vínculo por código |
| Alcance funcional | Planes Free/Plus/Premium con pagos simulados; pacientes, medicamentos, agenda, posturas, reloj, historial; avisos locales y push (Firebase solo simulado); detección de postura, inmovilidad y caídas en el nodo (Premium, 1 nodo por paciente, D-055) |
| Pendientes principales | Familiar/cuidador (D-050), privacidad (D-052), push de caída inmediato (D-051), Firebase real (D-054), protocolo de caídas y mediciones RNF (D-053), pruebas en Android físico (011). Detalle en [ESTADO_PROYECTO](ESTADO_PROYECTO.md) |
| Requerimientos | HU-01..07, RT-01..03 y no funcionales del informe; matriz en [TRAZABILIDAD](TRAZABILIDAD.md#matriz-hurtrnf-vigente). Los no funcionales son objetivos, ninguno medido |
| Idioma / zona horaria | es-CL / America/Santiago |
| Hosting e integraciones | Hosting por definir; SQLite en desarrollo; disponibilidad declarada como objetivo no medido (D-060). Google OAuth y Firebase requieren credenciales externas |

Las secciones siguientes son antecedentes históricos y se conservan sin cambios; ante diferencias rige la tabla anterior.

## Antecedente — 009

Evolución: **VIGIA para cuidadores**, [009 / CuidadosApp](../specs/009-cuidados-cuidadores/spec.md) implementada tras autorización posterior completa. Pacientes propios para todos los cargos, medicamentos/horarios, guías visuales, registro manual, historial y avisos con la web abierta. Free $0/un paciente, Plus $4.990/tres y Premium $9.990/ilimitados; IA/cámaras futuras. [Validación](../specs/009-cuidados-cuidadores/validation.md): 158 pruebas OK, migraciones ensayadas en memoria y navegador. Revisión manual, aceptación y aplicación de migraciones en DB existente pendientes.

Estado: copia de la base con PlanesApp y CuidadosApp implementadas tras autorización explícita; aceptación funcional e instalación en DB existente pendientes.

Evolución anterior: [008 — Dashboard y navegación](../specs/008-dashboard-navegacion/spec.md), implementada tras instrucción posterior de alcance completo. Seis SVG de menú, Inicio visible según permisos internos, dashboard de suscripciones para ADMIN/MANAGER y selector sol/luna compartido. Conserva PlanesApp/homeApp y reglas 007. [Validación](../specs/008-dashboard-navegacion/validation.md): 127 tests, build, 77 HTML y navegador correctos; zoom/movimiento reducido manuales y aceptación pendientes. Sin nueva app/modelos/migraciones.

| Campo | Valor actual |
|---|---|
| Nombre del producto | Por definir; carpeta de esta copia: Planes-pagina; los planes se llaman Vigía según referencias confirmadas |
| Módulo solicitado | CuidadosApp 009 integrada con PlanesApp 007, implementadas y autorizadas. Evoluciones de base 001–006 preservadas |
| Objetivo y usuarios finales | Cuidadores que se registran con Google o correo/contraseña, quedan RESTRICTED y contratan planes; pacientes/cuidados propios implementados en 009; operadores mantienen gestión interna |
| Alcance de negocio vigente | Suscripciones simuladas y cuidados propios: pacientes/medicamentos/agenda/guías/posturas/relojes/historial; sin IA/cámaras operativas |
| Alcance técnico recibido | Base Django con usuarios, perfiles/cargos, autenticación, tema, configuración aislada y pruebas iniciales |
| Idioma / zona horaria | es-cl / America/Santiago, sujetos al contexto acordado |
| Responsable de decisiones | Quien solicita el proyecto; registrar identidad si la proporciona |
| Módulos implementados de negocio | PlanesApp y CuidadosApp; base 001–006 conservada |
| Hosting e integraciones | Hosting por definir; Google OAuth integrado mediante allauth, credenciales/callback externo pendientes; sin pasarela real |

## PlanesApp solicitado — 2026-10-06

Primera fase DOCUMENTAR: [spec 007](../specs/007-planes-app/spec.md), [plan](../specs/007-planes-app/plan.md), [tareas](../specs/007-planes-app/tasks.md). El propietario confirmó registro Google y correo/contraseña, cuatro planes/precios/beneficios de las imágenes, mensualidad simulada, cambio inmediato sin prorrateo y cancelación a término; confirmó correo verificado antes de contratar, probado localmente. Capturas son referencias funcionales; diseño conservará la base con skill frontend-design y tarjeta única que refleja datos/gira al CVC.

007 implementa aprovisionamiento RESTRICTED/Free y privacidad del cliente, sin modificar reglas administrativas 004/006. 117 tests y build correctos; migraciones creadas/ensayadas solo con datos ficticios. [Validación](../specs/007-planes-app/validation.md) y [guía](PLANESAPP_DESARROLLO.md). Cámaras, app móvil, notificaciones, almacenamiento y facturación/pagos reales quedan fuera. Nombre comercial definitivo por definir; no asumir que el sitio debe renombrarse Vigía. El alcance completo recibió autorización posterior explícita. Google real y revisión/aceptación manual pendientes; sin despliegue ni migración de DB existente.

## Renovación solicitada el 2026-10-02

El propietario quiere diferenciar esta copia de su base principal y mejorar diseño, animaciones y transiciones. Se usa la skill local frontend-design. La propuesta cubre las pantallas existentes y un sistema central de colores; no agrega un negocio ni reconstruye autenticación.

Documentos: [spec](../specs/002-renovacion-visual/spec.md), [plan](../specs/002-renovacion-visual/plan.md), [tareas](../specs/002-renovacion-visual/tasks.md), [validación](../specs/002-renovacion-visual/validation.md). Tras DOCUMENTAR, el propietario autorizó explícitamente el alcance completo el 2026-10-02 y se implementó. Marca inicial petróleo con ciruela/cobre verificadas; colores en un único archivo y [guía reutilizable](PERSONALIZACION_VISUAL.md). Sin nuevos datos/modelos/rutas ni negocio. Regresión y build correctos; revisión de zoom/preferencia reducida en navegador y aceptación estética/funcional pendientes.

## Modo claro/oscuro solicitado el 2026-10-02

El propietario pidió botón de sol/luna y elección individual, revisó [spec](../specs/003-modo-visual-usuario/spec.md)/[plan](../specs/003-modo-visual-usuario/plan.md)/[tareas](../specs/003-modo-visual-usuario/tasks.md) y autorizó después el alcance completo de 003. Implementado: preferencia de cuenta en tabla propia de UsuarioApp, POST/CSRF y tokens claros/oscuros; perfiles/permisos de otras acciones preservados. Migración aditiva creada/probada/revertida solo en SQLite efímero, no aplicada a la base existente. [Validación](../specs/003-modo-visual-usuario/validation.md): 43 tests, build, 180 contrastes y navegador; verificaciones visuales restantes y aceptación pendientes.

## Gestión de cuentas solicitada el 2026-10-02 — 004

El propietario pide restablecer contraseñas desde el listado únicamente por administradores, sin dependencia de correo; comparte UsuarioApp.zip de otro proyecto como guía. Solicita ADMIN > MANAGER > RESTRICTED y confirma que la jerarquía aplica tanto a activar como a desactivar: ADMIN gestiona MANAGER/RESTRICTED; MANAGER solo RESTRICTED.

[Spec](../specs/004-administracion-usuarios/spec.md), [plan](../specs/004-administracion-usuarios/plan.md), [tareas](../specs/004-administracion-usuarios/tasks.md) y [validación](../specs/004-administracion-usuarios/validation.md). El propietario revisó documentos y después autorizó explícitamente el alcance completo de 004; implementado en UsuarioApp sin nueva app/tablas/migraciones ni cambios a registro, recuperación por correo/MFA/modo visual. Incluso superusuario requiere cargo ADMIN para restablecer o ADMIN/MANAGER para gestionar inferiores por estas acciones; helper global preservado. 57 tests/check/esquema/build/60 HTML OK y navegador cinco anchos/ambos modos; envío válido de nuevas credenciales por interfaz y aceptación funcional pendientes. Guardado/sesiones/MFA ya verificados en servidor. Sin datos reales, despliegue, commit/push.

## Auditoría de base y actualización solicitada — 2026-10-02

El propietario pide revisar la seguridad y antigüedad de las dependencias para reutilizar la base, aunque esta copia no pase directamente a producción. Se aplicó validar-produccion-sdd: [informe independiente](VALIDACION_PREPRODUCCION.md), con bloqueadores y evidencia operativa insuficiente; 57 pruebas actuales correctas no eliminan los hallazgos de dependencias/Registro/integridad.

Se documentó [005](../specs/005-actualizacion-dependencias/spec.md) para actualizar Python/JavaScript y asegurar instalación/mantenimiento, conservando la base y permisos actuales. P-005-01 (migraciones allauth con efectos sobre correos/principales) pendiente; implementación sin autorizar hasta instrucción posterior. Hallazgos de asignación de cargos/guardado parcial quedan fuera de 005 y requieren alcance propio. No hubo código, versiones cambiadas, datos reales ni despliegue por esta auditoría.

## Al reutilizar esta base

Completar con información conocida del nuevo pedido. Si falta un dato que no bloquea la especificación, dejar «por definir», no interrumpir con una entrevista ni inventar un cliente.

Registrar aquí objetivos y contexto general; los detalles funcionales van en specs. No escribir credenciales, URL con tokens ni datos reales de clientes.

## Correcciones de validación — 2026-10-02, autorizadas y ejecutadas

005 instala versiones mantenidas, lock/hashes, scripts CDN exactos/SRI y compatibilidad de autenticación; allauth/efectos de datos confirmados, solo ensayados con fixtures. 006 aprobada después de documentación corrige Registro e integridad sin migraciones propias. Regla confirmada: ADMIN solo inferiores, MANAGER RESTRICTED, únicamente root con ADMIN registra ADMIN. Axes/concurrentlogins permanecen instalados/comentados. 76 tests y verificaciones actuales; [detalle](DEPENDENCIAS.md). Aceptación manual/operación de cada futuro producto pendientes, sin tocar datos reales ni producción.


## Aplicación móvil solicitada — 2026-10-19

[010 — Aplicación móvil VIGIA](../specs/010-aplicacion-movil/spec.md), [plan](../specs/010-aplicacion-movil/plan.md) y [tareas](../specs/010-aplicacion-movil/tasks.md): solo DOCUMENTAR. Informe aportado propone Flutter/Android, familiar/cuidador, push y Edge. Se propone reutilizar Django/PlanesApp/CuidadosApp, conservando portal y suscripciones simuladas. La arquitectura React/microservicios/NoSQL del informe no coincide con esta base; no se adopta automáticamente. Aclaración humana posterior: iOS y Android, funciones por plan y detección de posición con MediaPipe incluidos. Matriz de funciones nuevas propuesta; colaboración y ubicación/hardware de detección pendientes. Sin nombre técnico confirmado ni código autorizado.


## Aplicación móvil — actualización 2026-10-19

Implementación 010 autorizada y demo disponible: Flutter Android/iOS, API Django y nodo local MediaPipe. Ver [guía móvil](MOVIL_DESARROLLO.md) y [validación](../specs/010-aplicacion-movil/validation.md). El estado documental previo es antecedente; siguen pendientes integraciones externas y validación real.

## Evolución solicitada22/10/2026

[011](../specs/011-ecosistema-instalable/spec.md) propone instalación Android/iPhone, reloj con creación/avisos locales, identidad índigo web/app y organización web/mobile/edge. Diseño móvil aceptado por usuario; aceptación no certifica cámara/alarma/dispositivos. Fase documental, no implementada.
