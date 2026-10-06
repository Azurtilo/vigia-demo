# Identidad del proyecto derivado

Estado: copia de la base principal destinada a ofrecer una segunda identidad visual reutilizable; todavía sin módulo de negocio.

| Campo | Valor actual |
|---|---|
| Nombre del producto | Por definir; Base-2 es el nombre actual de esta carpeta |
| Módulo solicitado | Ningún módulo de negocio nuevo; evolución UsuarioApp 004 implementada con revisión manual/aceptación pendientes; 002/003 conservados |
| Objetivo y usuarios finales | Disponer de otra base moderna para plataformas futuras, con identidad y colores fáciles de personalizar; usuarios de los flujos actuales de cuentas/seguridad, dominio comercial por definir |
| Alcance de negocio vigente | Ninguno todavía |
| Alcance técnico recibido | Base Django con usuarios, perfiles/cargos, autenticación, tema, configuración aislada y pruebas iniciales |
| Idioma / zona horaria | es-cl / America/Santiago, sujetos al contexto acordado |
| Responsable de decisiones | Quien solicita el proyecto; registrar identidad si la proporciona |
| Módulos implementados de negocio | Ninguno; spec transversal 001-CalidadBase verificada técnicamente |
| Hosting e integraciones | No definidos por esta documentación |

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
