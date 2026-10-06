# Plan — 006

Fecha: 2026-10-02. Plan después de spec.md; P-006-01 confirmada y alcance autorizado por instrucción posterior a entrega documental. Implementación en UsuarioApp sin cambios de esquema. [Resultados](validation.md).

1. Reutilizar `UsuarioApp/permissions.py` para política de Registro separada de AccountManagementMixin; compartirla con `core/context_processors.py`. Mantener core.mixins para otros consumidores. `ProfileCreateForm` recibe actor y filtra Position por códigos autorizados; vista revalida actor y destinatario del cargo en servidor.
2. `UsuarioApp/views.py`: transacción para alta/edición; formar y validar sin escrituras previas. Evitar crear Profile en POST antes de validar; cubrir usuarios sin perfil. No capturar indiscriminadamente errores de programación ni imprimir excepciones/datos del formulario. Errores previstos con mensaje útil y respuesta sin éxito.
3. `UsuarioApp/models.py` y `utils/customer_img.py`: preparar recorte/redimensionado en memoria antes de guardar archivo nuevo, mantener nombre UUID y tamaño final actual 300×300; almacenamiento por API del campo, sin asumir path en operaciones de borrado. Preservar archivo viejo hasta commit; compensar archivo nuevo ante fallo de save/transacción en flujos afectados. No realizar migraciones ni renombrar campos.
4. Pruebas dentro de UsuarioApp: actualizar únicamente expectativas sustituidas por regla aprobada, conservar IDs/RF históricos de 001. Añadir matriz cargo→cargo/HTML/URL, IDs arbitrarios, anónimo/CSRF/inactivo/root; inyectar fallos reales en DB/imagen/storage y verificar datos y archivos, mensajes y fotos intactos. Regresión completa con core.test_settings y media temporal, build si cambian clases, navegador de Registro/Perfil.
5. Actualizar spec001 mediante nota fechada de sustitución de regla, decisiones/trazabilidad/estado y validation006 con ejecución real. AUD-004/005 solo se cierran con regresiones comprobadas. No operar base ni media real.

Archivos reales: UsuarioApp/forms.py, permissions.py, views.py, models.py, tests.py o tests_integridad.py; utils/customer_img.py, core/context_processors.py y plantillas existentes solo para errores si necesario. No crear infraestructura general por rutina.

## Ajuste de almacenamiento constatado al implementar

Un username permitido de 150 caracteres producía ruta de 197, incompatible con ImageField(max_length=100). Se verificó la excepción del almacenamiento local con ruta sintética. Nuevas fotos usan users/{user_id}/UUID.ext, manteniendo UUID y longitud de campo; no se mueve/referencia de nuevo ninguna foto existente ni cambia el esquema. Trece pruebas de integridad incluyen alta con username máximo/foto 300×300. Preparación de archivo se cierra también si falla la consulta de existencia en storage.
