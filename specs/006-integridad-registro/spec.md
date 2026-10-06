# 006 — Permisos e integridad de Registro y Perfil

Fecha: 2026-10-02. Implementación autorizada después de entregar spec/plan/tasks: «Sí, implementar la spec 006 con la regla confirmada».

## Necesidad y alcance

La auditoría reprodujo un alta ADMIN realizada por MANAGER cuando el identificador ADMIN no es 1, y un fallo de Profile.save que deja User creado sin perfil. La edición de perfil también guarda User antes de fallar la fotografía. Reutilizar UsuarioApp y sus formularios/vistas; corregir estos fallos sin nuevas apps, dependencias, tablas ni migraciones.

## Requisitos

- **RF-006-01:** autorizar Registro y cargos asignables por permission_code y actor vigente, nunca por identificador numérico. Rechazar POST manipulado, cargos ausentes/desconocidos, anónimo, inactivo, RESTRICTED y cuentas sin cargo/perfil. Exigir cargo incluso al superusuario si así se confirma P-006-01. Menú y servidor deben coincidir.
- **RF-006-02:** regla P-006-01 confirmada: ADMIN asigna solo MANAGER/RESTRICTED; MANAGER solo RESTRICTED; únicamente superusuario con cargo ADMIN asigna ADMIN. Cargo requerido incluso al superusuario. No cambiar activar/desactivar/restablecer de 004 ni el helper global para otras acciones.
- **RF-006-03:** alta User + Profile indivisible; fallos de validación, DB o procesamiento/almacenamiento de imagen no dejan cuentas ni archivos nuevos huérfanos. Mensaje de éxito únicamente tras confirmar la escritura.
- **RF-006-04:** actualización de datos propios y foto indivisible; conservar datos/foto anterior ante fallo. No borrar foto anterior antes de confirmar transacción. Procesar nueva foto antes de persistirla; no reprocesar fotos existentes al guardar otros atributos. Eliminar archivo nuevo si falla la escritura; limpieza anterior posterior a commit.
- **RF-006-05:** pruebas de cargos con IDs arbitrarios, POST manipulado y fallos antes/después de escritura, imágenes ficticias y almacenamiento local aislado. Preservar las regresiones 002–005 y verificar UI/errores sin exponer detalles internos.

## Decisión crítica y aceptación

P-006-01 confirmada por el propietario: opción B; ADMIN solo inferiores, MANAGER solo RESTRICTED y root con ADMIN puede crear ADMIN. Confirmación independiente de la autorización posterior de implementar 006. No se dedujo del ZIP ni de los permisos de activación.

Fuera de alcance: cifrado MFA, nuevas políticas antiabuso/auditoría, límites adicionales de imágenes, SMTP, producción, datos reales, commits/push y migraciones reales. Sin aceptación funcional automática. La limpieza de archivos tras commit puede fallar: conservar referencia/estado válido, registrar error técnico sin datos sensibles y documentar mantenimiento manual; no afirmar transacción distribuida DB/almacenamiento.
