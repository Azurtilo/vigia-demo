# Tareas — 006

Fecha: 2026-10-02. Tareas técnicas ejecutadas después de autorización; spec → plan → tasks creados en este orden. [Evidencia](validation.md); aceptación funcional pendiente.

- [x] T-006-01: confirmar P-006-01 e instrucción posterior a documentos; registrar matriz aprobada. RF01/02.
- [x] T-006-02: preservar cambios/snapshot y aplicar política compartida/form/vista/menú. RF01/02/05; depende 01.
- [x] T-006-03: alta y edición transaccionales, preparación/compensación de foto y borrado posterior. RF03/04; depende 02.
- [x] T-006-04: probar matriz y fallos DB/storage/imagen, regresión/UI, sin datos reales. RF01–05; depende 03.
- [x] T-006-05: registrar resultados, cierre justificado de AUD-004/005 y actualizar docs/estado. RF05; depende 04.

Documentación entregada; propietario confirmó P-006-01 (solo root con ADMIN crea ADMIN) y autorizó posteriormente implementar 006. No se repitieron preguntas de 004. Snapshot/entorno comparten preparación de 005. Trece pruebas nuevas cubren matriz/CSRF/cargos vigentes y fallos de DB/imagen/storage, en suite de 76 métodos. Navegador Registro/listado/MFA/móvil; guardado de credencial nueva por UI queda manual debido a la política de la herramienta. Sin migraciones ni datos reales.
