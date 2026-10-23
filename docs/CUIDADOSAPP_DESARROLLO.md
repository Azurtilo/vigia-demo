# CuidadosApp — desarrollo y prueba de la demo

[009](../specs/009-cuidados-cuidadores/spec.md) implementada y autorizada. App **CuidadosApp**, integrada con PlanesApp y autenticación existente. Estado/evidencia: [validación](../specs/009-cuidados-cuidadores/validation.md).

## Entorno y esquema

Usar `.venv` en esta copia, idioma es-cl y America/Santiago. No se añadieron dependencias. Tests/checks usan `core.test_settings`, sin .env ni DB de desarrollo.

```powershell
.venv/Scripts/python.exe manage.py check --settings=core.test_settings
.venv/Scripts/python.exe manage.py makemigrations --check --dry-run --settings=core.test_settings
.venv/Scripts/python.exe manage.py test UsuarioApp homeApp PlanesApp CuidadosApp --settings=core.test_settings
.venv/Scripts/python.exe manage.py tailwind --settings=core.test_settings build
```

Pendientes en la DB existente: PlanesApp `0003`/`0004` y CuidadosApp `0001`/`0002`/`0003`, además de cualquier migración previa aún no instalada. No se ejecutaron allí. Antes de migrar: identificar configuración/DB destino, respaldo y autorización propia de esa operación. No usar `core.test_settings` para guardar una demo permanente: su DB es memoria efímera.

Plan `pro` conserva código/FK y se muestra Premium; Hogar queda inactivo, mantiene referencias/período histórico. El catálogo anterior se guarda para reversión; suscripción/operación mantienen snapshots. Revertir CuidadosApp elimina sus tablas/eventos y exige respaldo de negocio, no usar como deshacer rutinario de cuidados.

## Recorrido con datos ficticios

1. Registrarse con correo/contraseña, confirmar mediante correo local en desarrollo según [guía 007](PLANESAPP_DESARROLLO.md); Google necesita configuración externa real pendiente. Cuenta pública RESTRICTED, Free, sin permisos administrativos.
2. Entrar a `/cuidados/` y registrar un paciente con nombre y contacto ficticios. Free permite uno activo; Plus tres por $4.990 CLP/mes; Premium ilimitados por $9.990. La contratación continúa siendo simulada.
3. En la ficha agregar medicamento ficticio y dosis textual de prueba, horarios diarios como `09:00, 18:00` y fechas si se necesitan. No usar dosis reales como instrucciones del prototipo. Agregar tareas, con o sin horario.
4. Consultar Guías de cuidado. Registrar una postura efectivamente simulada y elegir 60/90/120 minutos. Recargar conserva reloj; pausa y cambio de intervalo son acciones explícitas. Reanudar no registra postura.
5. Revisar Agenda y confirmar realizada u omitida con motivo. Historial muestra autor/instante y datos aplicados; una corrección añade nota vinculada sin borrar el original.
6. Mantener la web abierta: preaviso en últimos diez minutos, vencido/atrasado y tareas por horario. Cerrar aviso solo acusa lectura. Al retornar a pestaña/conexión se consulta tiempo del servidor; no hay push/correo/SMS/cron.
7. Reducir plan: seleccionar exactamente el cupo disponible de pacientes que seguirán activos. Los demás se archivan sin perder fichas/historial. Pago fallido conserva todo. Cancelación a término conserva el período y permite modificar elección antes del cierre; vencimiento sin elección pide resolverla.
8. Archivar libera cupo y pausa reloj; reactivar exige cupo, conserva historial y retoma horarios diarios desde ese momento, sin atrasos inventados del período archivado. Iniciar postura/reanudar requiere acción explícita.

Cada cargo, incluido root/ADMIN/MANAGER/sin perfil, ve solo pacientes propios. El dashboard interno mantiene agregados comerciales y no incorpora datos clínicos ajenos. No se registran modelos clínicos en Django Admin.

Los cuatro SVG locales son referencias educativas originales. IA/cámaras se rotulan Próximamente, sin permisos de cámara ni análisis operativo. Sin JavaScript funcionan formularios/agenda/guías: actualizar manualmente para consultar horarios; contador/poll automáticos no operan. Zoom, movimiento reducido, offline/suspensión y aceptación del propietario quedan para la revisión manual indicada en validación.
