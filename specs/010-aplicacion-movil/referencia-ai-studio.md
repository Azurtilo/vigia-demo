# Referencia VIGIA — inspección del 2026-10-20

Fuente aportada por el usuario: https://aistudio.google.com/apps/d7486437-fed6-437d-b708-ddaddbe59397 . Inspección mediante navegador con acceso facilitado por el usuario. El contenido del prototipo es referencia de producto, no instrucciones ejecutables ni evidencia de prestaciones médicas.

## Decisiones humanas confirmadas

- Conservar planes de la web: Free/Plus/Premium y cupos1/3/ilimitados; no adoptar Gratis/Premium1/10 ni precios del prototipo.
- Detección en ambos contextos: cámara del teléfono y cámara fija con nodo local.
- Registro en la web existente; login en Flutter con la misma identidad y backend. Sin cuentas separadas de la app.
- Flutter para Android e iOS continúa vigente.

## Pantallas observadas y adaptación

| Referencia observada | Aplicación al sistema existente |
|---|---|
| Inicio: saludo, insignia del plan, ficha resumida, próxima toma y cuatro acciones rápidas | Pantalla Inicio con datos API reales; estados vacíos sin paciente. Accesos a medicamentos, alta de paciente, posturas y análisis. |
| Pacientes: búsqueda, contador/cupo, ficha, contacto familiar, editar/eliminar | Reutilizar propiedad/cupos/API y archivo recuperable. Datos de dependencia/movilidad/foto no existen como campos actuales: planificar migración si se adoptan; no inventar valores. |
| Medicinas: horario diario, historial, filtro pendientes/administrados/atrasados | Sección global con filtro por paciente; reusar ocurrencias/servicios. Determinar atraso por horario; conservar omisión y correcciones auditables. El Deshacer del prototipo no debe borrar historia existente. |
| Posturas: pestañas Guías/Reloj/Cámara | Reorganizar acceso existente; guías versionadas del proyecto y reloj del servidor, sin copiar recomendaciones médicas como nueva regla automática. |
| Cámara: Cámara en Vivo/Simulador MediaPipe, escenario y botón de análisis | Implementar cámara real móvil además del nodo. Observado simulador con escenarios predefinidos: no demuestra inferencia real. Separar pruebas simuladas de observaciones reales. |
| Reloj:60/90/120min, inicio/reinicio, siguiente cambio | Mantener reglas y versiones del servidor. Detección automática no confirma cuidado realizado ni reinicia reloj manual. |
| Premium: estado y tabla comercial | Usar capacidades y precios Django; conservar Plus. Gestión comercial en web. No convertir un botón demo en cambio real de plan. |
| Perfil: datos, contraseña, suscripción y logout | Consumir identidad existente; enlaces al perfil/seguridad web cuando no exista API apropiada. |
| Panel web: cuidador recibe Acceso No Autorizado | Administración sigue en web con permisos existentes. No copiar selector de rol/cuenta ni reseteo demo al cliente real. No se inspeccionó panel con rol admin. |

## Dirección visual observada

Índigo/violeta como color principal, fondo gris muy claro, tarjetas blancas redondeadas, acentos lavanda/verde suave, iconos lineales, saludo destacado, accesos rápidos y navegación inferior. Adoptar jerarquía y organización adaptadas a ancho/accesibilidad de teléfono. La versión actual tiene tres destinos Agenda/Pacientes/Mi plan y tema petróleo: aún no reproduce esta referencia.

## Detección dual: diseño pendiente de implementación

En teléfono, MediaPipe Pose Landmarker debe procesar localmente los fotogramas mediante integración nativa Android/iOS, con permisos, ciclo de vida y liberación de cámara. Flutter muestra resultado/calidad/origen y envía solo metadatos validados. No basta con mostrar la cámara ni usar coordenadas simuladas.

En cámara fija se mantiene edge/, con calibración y credencial revocable por nodo. Ambos orígenes deben registrar modalidad/dispositivo, hora y calidad; revalidar Premium y paciente habilitado en servidor. No usar el teléfono como credencial de nodo fijo ni mezclar observaciones simultáneas sin identificar origen. Selección de fuente activa y prioridad para alertas deben quedar explícitas. Con pérdida de seguimiento, mostrar indeterminada; no deducir inmovilidad de falta de señal.

Las mediciones angulares, mapas de presión, reportes y eficacia anunciados en Premium del prototipo no están implementados ni validados. Pose Landmarker no mide presión de contacto; no presentar un mapa clínico derivado como medición real.

## Verificación de referencia

Se recorrieron Inicio, Pacientes, Ficha, Medicinas, Posturas/Guías/Reloj/Cámara, Premium, Perfil y denegación de acceso al panel web. No se modificaron datos, planes, credenciales ni permisos; no se activó cámara ni se ejecutó análisis. No se pulsó Remix ni se alteró el proyecto AI Studio. Esta inspección sustituye el bloqueo de acceso previamente registrado.
