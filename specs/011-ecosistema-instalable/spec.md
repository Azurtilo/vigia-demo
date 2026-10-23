# 011 — Ecosistema VIGIA instalable, reloj y organización

Fecha: 2026-10-22. Fase: DOCUMENTAR; propuesta pendiente de instrucción posterior de implementación. Amplía007/009/010, conserva sus RF y autorizaciones anteriores. Usuario acepta el estilo móvil y confirma prueba en **Android e iPhone**.

## Necesidad y evidencia

El reloj de mobile/lib/care.dart solo dibuja controles cuando patient.timer existe; configure_timer en CuidadosApp/services.py exige un reloj con last_event. Un paciente sin cambio registrado ve título sin acción. Es un fallo del estado vacío de RF-010-10; no debe legitimarse modificando ese requisito. Crear un reloj independiente y avisos locales amplía el contrato actual de RF-010-04/07: requiere implementación nueva.

Planes-pagina.rar se inspeccionó como referencia, sin ejecutar contenido ni sobreescribir proyecto. Coinciden byte a byte PlanesApp/models.py, services.py, views.py, templates/pages/PlanesApp/catalogo.html y static/css/tokens.css con la carpeta actual. El archivo core/urls.py del RAR no incluye API móvil y no contiene PlanesApp/entitlements.py: no sustituir la versión actual por el archivo antiguo.

## Requisitos

- RF-011-01: instalación de prueba Android e iOS con instrucciones, artefactos/versiones identificados y un backend alcanzable desde teléfono. Diferenciar demo LAN de uso remoto HTTPS. No llamar entregado a iOS por existir APK o build de simulador. Registro en web y login con misma identidad; no duplicar cuentas.
- RF-011-02: Reloj presenta estado vacío con «Crear recordatorio», paciente e intervalo60/90/120. Propuesta: comenzar desde confirmación del servidor sin inventar cuidado realizado; pausar/reanudar/cambiar intervalo y mostrar próximo vencimiento/estado. Mantener vínculo a registrar postura real, que reinicia reloj conforme009. Al cambiar intervalo, usar último evento real si existe; para reloj iniciado sin evento, usar su ancla de inicio. Cambio ya vencido se muestra vencido, no se oculta.
- RF-011-03: programar aviso local de próximo vencimiento en Android/iOS tras confirmación del servidor y autorización del SO. Mostrar permiso denegado, no programado, programado y vencido. Sonido sujeto a ajustes del sistema; no prometer alarma crítica ni eludir silencio. Un aviso no registra atención. Cancelar/reemplazar al pausar, cambiar, atender, archivar, cerrar sesión o cambiar cuenta. Una ocurrencia por paciente/generación, sin ráfaga de alertas atrasadas. Propuesta inicial: un aviso por vencimiento hasta nueva acción, sin repetición indefinida.
- RF-011-04: web y app comparten Django/planes/cupos/pacientes. Free/Plus/Premium1/3/ilimitados, funciones manuales y reloj para todos; MediaPipe Premium conservado. Volver de portal refresca capacidades, validación final en servidor. No pagos reales añadidos. Avisos pendientes locales pueden quedar desactualizados sin red: reconciliar al recuperar sesión/red y explicar limitación; no prometer revocación inmediata offline.
- RF-011-05: adaptar la web al índigo/fondos claros/tarjetas y jerarquía de la app aprobada. Conservar modo oscuro, formularios, errores, accesibilidad, permisos y navegación existentes. Colores semánticos centralizados; no reemplazar sitio por prototipo ni alterar diseño móvil aprobado.
- RF-011-06: diferenciar físicamente web/, mobile/, edge/, docs/ y specs/. Dividir Flutter por auth, pacientes, medicamentos, posturas/reloj, plan, perfil, detección y componentes compartidos; conservar plugin MediaPipe. Backend mantiene apps y servicios existentes; no duplicar reglas en cliente ni renombrar labels de migraciones. Rutas públicas preservadas y comandos documentados desde raíz y carpeta web.

## Datos y permisos

PostureTimer existente admite last_event/anchor_at nulos: inicio independiente no crea CareEvent ficticio. Evaluar restricciones completas antes de confirmar ausencia de migración. Mantener generación y tokens firmados; definir idempotencia de inicio/reintento. IDs locales de notificación incluyen cuenta/paciente/generación, almacenamiento mínimo sin nombre ni dosis en texto bloqueado. No credenciales en enlaces de descarga.

| Acción | Anónimo/inactivo | Activo sin perfil / RESTRICTED | ADMIN/MANAGER | Superusuario |
|---|---|---|---|---|
| Paciente/reloj/avisos | Denegar | Solo propios y habilitados por cupo | Solo propios | Solo propios |
| Plan propio y portal | Login/denegar | Propio; correo verificado donde007 lo exige | Propio | Propio |
| Administración web | Denegar | Preservar denegación vigente | Matriz004/008 existente | Reglas existentes de cada acción, sin ampliar |

No confiar en menú o capacidades guardadas. Los cambios físicos no alteran roles ni separación de cuentas.

## Aceptación

1. Paciente nuevo puede crear reloj sin registrar una postura falsa; API rechaza ajeno, inválido, conflicto y repetición peligrosa. Estado vacío siempre orienta.
2. Reloj60/90/120, pausa/reanudación y cuidado real probados; notificación real recibida en Android e iPhone bloqueados, con permiso permitido/denegado y cambios/logout verificados. Ensayo corto solo en entorno de prueba, sin cambiar intervalos de producto.
3. Mismo usuario en web/app observa mismo plan; reducción de cupo y sesión vencida se respetan. Prueba de reconciliación de cambios web y ausencia de duplicados locales/push.
4. Web comparada en claro/oscuro, móvil/escritorio, teclado; conserva catálogo/checkout simulado/mi suscripción/cuenta y panel administrativo.
5. Tras reorganizar, imports, migraciones dry-run, suites Django/Flutter, Tailwind, recursos, demo, builds y comandos funcionan desde ubicaciones documentadas. No mover bases, secretos o entornos inadvertidamente.
6. Evidencia independiente para APK, iOS firmado/prueba física y conectividad; cámara dual y planes sin regresión.

## Decisiones externas pendientes

Servidor remoto/dominio y cuenta de distribución Apple no proporcionados. Preparar prueba LAN y build iOS local; publicación/TestFlight, firma de distribución y despliegue requieren configuración y autorización específica. No pedir contraseñas por chat. Alcance propuesto no incluye tiendas, pagos, alarma clínica crítica ni funcionamiento multiusuario offline perfecto.


## Autorización22/10/2026
El usuario indica «perfecto ahora modificalo»: implementación completa011 autorizada. Los estados documentales anteriores son antecedentes; no autorización de producción/tiendas ni migración real.


## Decisión de alcance — 2026-10-22

El propietario indica: entorno Windows, **Android primero, iOS fuera de alcance** ([D-011-02](../../docs/DECISIONES.md)). En esta spec, las menciones a iOS/iPhone quedan sustituidas, sin reciclar IDs:

- RF-011-01: instalación de prueba solo en Android. Sin build ni prueba iOS.
- RF-011-03: aviso local solo en Android.
- Aceptación 2 y 6: notificación y evidencia física solo en Android. Sin firma ni distribución Apple.
- Decisiones externas: la cuenta de distribución Apple deja de ser bloqueo. T-011-10 queda fuera de alcance.

El texto original arriba se conserva como antecedente.
