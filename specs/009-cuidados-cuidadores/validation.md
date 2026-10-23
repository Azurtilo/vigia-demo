# Validación — 009 / CuidadosApp

2026-10-06. Alcance completo autorizado posteriormente: «te doy permiso de implementar specs 009 alcanse completo». Código implementado; aceptación funcional del propietario pendiente. La reanudación confirmó archivos/cambios locales y corrigió documentos que todavía reflejaban DOCUMENTAR.

## Resultado técnico

**158 pruebas Django OK (14,126 s)**: 31 nuevas de cuidados y 127 de UsuarioApp/homeApp/PlanesApp, con las expectativas de catálogo y entrada cliente actualizadas al nuevo requisito. Configuración `core.test_settings`, SQLite en memoria, identidades/contactos/medicamentos ficticios. No lectura de .env, DB de desarrollo o media personal; no migración real, despliegue, commit/push ni dependencias añadidas.

| Comando / ensayo | Resultado real |
|---|---|
| `.venv/Scripts/python.exe manage.py test UsuarioApp homeApp PlanesApp CuidadosApp --settings=core.test_settings` | 158 / OK, 14,126 s |
| `manage.py check --settings=core.test_settings` | Sin problemas |
| `manage.py makemigrations --check --dry-run --settings=core.test_settings` | No changes detected |
| `manage.py tailwind --settings=core.test_settings build` | Standalone 4.3.0, OK, 79 ms; @source de CuidadosApp y exclusiones existentes |
| Ruff sobre CuidadosApp y código de negocio integrado | OK; formato aplicado al alcance |
| Node bundled `--check CuidadosApp/static/CuidadosApp/care.js` | OK, sin instalar Node ni paquetes |
| Carga de Django Templates | 89 HTML sin errores de sintaxis |
| JPEG de navegador | 13 archivos válidos, dimensiones registradas |
| Ensayo de esquema/catálogo en memoria | Avance, reversión y reaplicación correctos; catálogo previo personalizado recuperado, snapshots/importes/fechas comerciales intactos |

[Resultados estructurados](evidencia/verificacion.json), [migraciones](evidencia/migraciones.json), [navegador](evidencia/navegador.json). Cuatro observaciones SIM117 de PlanesApp/tests.py reproducidas también en HEAD, anteriores al alcance; se conservan sin limpieza general. La suite pasó después de corregir una fixture que anclaba medianoche a UTC en lugar de Santiago; las pruebas ya no dependen de que el día UTC coincida con el local.

## Cobertura por requisito

| RF | Evidencia / comportamiento |
|---|---|
| 01 | Matriz ADMIN/MANAGER/RESTRICTED/root/sin perfil; listas, hijos, fichas y POST ajenos 404; anónimo/inactivo/CSRF/cache privada; modelos sensibles fuera de Django Admin y eliminación de cuenta protegida sin nombre clínico |
| 02 | Catálogo activo Free/Plus/Premium 0/4990/9990 y cupos 1/3/null; Hogar histórico sin nueva contratación/renovación; reversión recupera beneficios anteriores y no modifica snapshots comerciales |
| 03 | Campos/contactos/fechas, propietario ignorado en payload, versión obsoleta, alta y reactivación con cupo; archivo conserva eventos y pausa timer. Carrera real de dos transacciones SQLite observando el último cupo: una alta y una escritura rechazada recuperable |
| 04 | Horarios diarios múltiples/únicos, fechas, versiones y omisión con motivo; replay/duplicado rechazado. Editar dosis no reabre la toma ni cambia el texto aplicado; horarios nuevos pasados no inventan pendientes |
| 05 | Cuatro SVG originales locales, alt/fuente/versión, tres posiciones y preparación; navegador inspecciona imágenes y textos en ambos modos. Superposición de línea/texto de supina corregida. Referencias educativas; sin evaluación de postura del paciente |
| 06 | 60/90/120, instante servidor, replay/generación obsoleta, cambio de intervalo, pausa/reanudación; recarga conserva estado; reanudar no crea una postura realizada |
| 07 | Ventana de diez minutos, vencimiento/atraso, claim firmado/CSRF/unique; dos pestañas y recarga no repiten el aviso; nueva generación invalida el viejo; acuse no es CareEvent |
| 08 | Agenda propia hoy/yesterday reciente, tareas diarias/manuales y estados; actividades nuevas/reactivadas no generan avisos de horarios anteriores a programación vigente |
| 09 | Snapshots de dosis/postura/intervalo y autor/fecha visibles; corrección vinculada conserva original y no altera reloj |
| 10 | Selección propia obligatoria en reducción; pago rechazado/rollback sin archivo; cancelación futura, cambio de selección y retiro; fin efectivo sin escritura GET y materialización POST; expiración sin selección deja consulta y pide elegir; retiro del último método usa misma regla |
| 11 | Cliente Home→Mis cuidados, interno mantiene agregados comerciales; cuatro SVG/nav, selector compartido, tokens/modos, panel y guías responsive; formularios HTML operativos sin scripts |
| 12 | Regresión aislada, restricciones/atomicidad, horas conscientes, DST inexistente/repetido y medianoche; check/esquema/build/JS/templates y evidencia real |

La carrera SQLite prueba que no se excede el cupo en ese backend. No certifica el bloqueo de filas de una instalación distinta: `select_for_update` de User compartido con suscripciones deberá comprobarse en el backend elegido antes de producción.

## Navegador y artefactos

Preview temporal loopback con WSGI y SQLite en memoria. Autenticación exclusiva de fixtures del helper descartable; ninguna ruta de acceso de prueba incorporada al producto. Cinco anchos **360/390/768/1024/1440**, claro/oscuro: `scrollWidth <= innerWidth` en los diez casos; captura móvil adicional real a 390. Una segunda pestaña verificó deduplicación y se cerró antes de continuar los cambios de viewport.

Flujos ejecutados: postura/60 minutos y pausa persistente; alta del tercero Plus, rechazo del cuarto; horarios duplicados y múltiples, omisión; preaviso y vencido con tiempo de fixture del servidor; otra cuenta y ficha ajena; Inicio interno y cuidados propios vacíos; cancelación a término con elección; Free inmediato con dos archivos; guía completa; corrección, archivo y reactivación con historial/reloj pausado. La sesión sintética expiró durante la interrupción; se renovó solo en el helper y se completó la prueba, sin alterar la política de sesiones del producto.

Fallback probado mediante respuesta del preview que retira scripts y despliega noscript; **cero scripts en DOM**. Menú móvil nativo y formularios de postura/corrección/archivo/reactivación funcionan; horarios visibles y explicación de actualización manual. No se cambió la preferencia global de JavaScript del navegador. Tab desde Registrar postura alcanzó Cancelar; no se afirma una auditoría completa con lector de pantalla.

| Captura | Evidencia |
|---|---|
| [Panel claro](evidencia/panel-light-1440.jpg), [oscuro](evidencia/panel-dark-1440.jpg) | Dos pacientes, próximos cambios, agenda y referencia |
| [Móvil claro](evidencia/panel-mobile-light.jpg), [oscuro](evidencia/panel-mobile-dark.jpg) | Orden de acciones, botones y guía en una columna |
| [Preaviso](evidencia/aviso-postura.jpg) | Paciente/acción y cierre que no registra cuidado |
| [Guías completas](evidencia/guias-light-completas.jpg) | Cuatro ilustraciones finales, instrucciones y fuentes |
| [Error de horarios](evidencia/medicamento-error.jpg) | Validación en servidor sin falso guardado |
| [Reducción](evidencia/reduccion-pacientes.jpg) | Un activo elegido y dos archivados con fichas conservadas; captura de panel del navegador recorta el borde derecho |
| [Fallback](evidencia/fallback-mobile.jpg), [corrección](evidencia/historial-correccion.jpg), [reactivación](evidencia/reactivacion-sin-scripts.jpg) | Formularios y estados sin scripts |

Preview detenido, pestañas temporales cerradas y viewport restaurado. Helpers/logs de trabajo retirados al cierre; evidencia se conserva aquí. Verificación documental de 14 Markdown y enlaces locales sin faltantes, diff --check correcto con avisos LF/CRLF; [resultado](evidencia/documentos.json). Autenticación, dependencias, tokens, helper interno y test_settings sin cambios Git.

## Límites y siguiente paso

- T-009-01–11 completas; T-009-12 parcial: zoom nativo 200%, preferencia nativa de movimiento reducido, offline y suspensión real no emulados por las capacidades disponibles. CSS y listeners implementados; probar manualmente. No se garantiza alerta con pestaña suspendida/web cerrada.
- T-009-13 documentada y entregada; cierre total depende de los puntos manuales y aceptación del propietario. Suite verde no equivale a aprobación visual/clínica ni a producción.
- Migraciones nuevas **no aplicadas a la DB existente**. Identificar entorno/respaldo y autorizar esa operación antes de usar la demo allí. [Guía de desarrollo](../../docs/CUIDADOSAPP_DESARROLLO.md). OAuth Google real sigue pendiente de las credenciales/callback de 007.
- Guías breves basadas en la [International Guideline, Repositioning](https://www.internationalguideline.com/repositioning), edición 2026 consultada el 2026-10-06. El intervalo lo elige el cuidador según su plan individual; las imágenes son orientativas. IA/cámaras permanecen futuras conforme al alcance humano.

## Ajuste de imágenes solicitado — T-009-14, 2026-10-06

Cuatro PNG nuevos generados con image_gen y dirección visual frontend-design, integrados en [assets](../../web/CuidadosApp/static/CuidadosApp/guides) mediante CareGuide.illustration y guide.html. Serie con persona mayor/cama/apoyos y cuidadora en preparación. Laterales revisados y asignados según el lado anatómico apoyado; los prompts originales tienen la orientación solicitada invertida y se conservan como evidencia de generación, no como validación de anatomía. Alt actualizado, revisión de caché y fallback a las imágenes personalizadas existentes. Textos/fuentes/versión clínica/SVG previos intactos; no cambios de DB ni migraciones nuevas.

- `.venv/Scripts/python.exe manage.py test CuidadosApp --settings=core.test_settings`: **31 OK, 0,915 s** tras el último ajuste. Prueba existente de restricciones/assets verifica ambos recursos SVG/PNG y alt. No se reutiliza el resultado histórico de 158 como ejecución actual.
- Ruff de models.py, `manage.py check` y `makemigrations --check --dry-run`, todos con test_settings: correctos/sin cambios. No clases/CSS/fuentes nuevas; build previo sigue vigente para el CSS sin modificaciones.
- Navegador aislado en memoria: 390/1440 px en claro/oscuro, cuatro imágenes completas por caso (`naturalWidth > 0`), alt visibles y `scrollWidth <= innerWidth`. Biblioteca y componente del panel observados. [Mediciones](evidencia/imagenes-v2-navegador.json), [assets y comprobaciones](evidencia/imagenes-v2-verificacion.json), [prompts exactos y asignación final](evidencia/prompts-imagenes-v2.json).
- Capturas finales: escritorio [claro](evidencia/guias-v2-light-1440.jpg)/[oscuro](evidencia/guias-v2-dark-1440.jpg), móvil [claro](evidencia/guias-v2-light-390.jpg)/[oscuro](evidencia/guias-v2-dark-390.jpg). Evidencia anterior conservada como histórico de implementación.

Preview detenido, pestaña temporal cerrada, viewport restaurado y helpers retirados. T-009-14 completa técnicamente; revisión visual del propietario pendiente, igual que los límites operativos/manuales anteriores.

## Corrección de selectores — T-009-15, 2026-10-06

Reproducción en postura con cuenta/paciente ficticios: ambas flechas SVG medían **240×240** debajo de selectores de 45 px. El template crispy del paquete dependía de utilidades ausentes del escaneo Tailwind propio. Override local [select.html](../../web/templates/tailwind/layout/select.html), CSS semántico/tokens compartidos y revisión del recurso; no cambios de formularios/servicios/DB ni paquete instalado.

Navegador después: **20×20**, completamente dentro de cada selector; cuatro casos claro/oscuro 390/1440 sin overflow. ArrowDown elige supina; obligatorio vacío bloquea envío con mensaje nativo; seleccionar lateral izquierdo/90 minutos y enviar confirma el reloj en ficha. [Mediciones antes/después](evidencia/select-navegador.json); [antes](evidencia/select-antes-dark.jpg), después [oscuro escritorio](evidencia/select-despues-dark-1440.jpg)/[móvil](evidencia/select-despues-dark-390.jpg), [claro escritorio](evidencia/select-despues-light-1440.jpg)/[móvil](evidencia/select-despues-light-390.jpg).

Render sintético aislado conserva id/name/disabled/aria-describedby, grupos/selección y múltiples/size; múltiples sin flecha decorativa. [Contratos](evidencia/select-contratos.json). Tailwind standalone 4.3.0 **86 ms**, check sin problemas, diff --check correcto (avisos LF/CRLF previos). Suite final `.venv/Scripts/python.exe manage.py test UsuarioApp homeApp PlanesApp CuidadosApp --settings=core.test_settings`: **158 OK, 15,142 s**.

Primera ejecución: 157 pasan y el ensayo previo test_simultaneous_last_slot_never_exceeds_capacity falla porque cuenta cero altas (ambos escritores SQLite pueden recibir bloqueo y pedir reintento). Aislado posteriormente: 1 OK, 0,025 s; suite final completa OK sin alterar código de negocio/test de carrera. Registrar como intermitencia del ensayo SQLite pendiente de estabilización, no atribuirlo a selectores ni ocultarlo bajo la suite final verde. [Resumen de verificación](evidencia/select-verificacion.json).

Preview en memoria detenido/pestaña cerrada/viewport restaurado/temporales retirados. T-009-15 técnicamente completa; límites manuales/operativos anteriores y aceptación del propietario conservados.
