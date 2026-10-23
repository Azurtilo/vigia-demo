# Plan técnico — 011

Depende de [spec](spec.md). Propuesta, no aprobada ni implementada.

## Fases y orden

Aplicar06-cambios →01-especificar →02-planificar →03-tareas. Esta entrega solo Markdown. Después de autorización: corregir reloj y añadir notificación local sobre estructura actual; comprobar integración; armonizar web; separar rutas físicas con verificación; compilar/entregar por plataforma. No mover todo primero y ocultar causas de regresiones.

## Reloj y avisos

Existentes: mobile/lib/care.dart (timer, recordPosture, tab4), CuidadosApp/services.py (configure_timer/record_posture), CuidadosApp/api/views.py (serialización/token/TimerView), CuidadosApp/models.py (PostureTimer), scheduling.py, forms.py y API urls. Diseñar acción start con intervalo/token/version0 para ausencia de reloj; transacción bajo bloqueo de usuario/paciente, creación única y control de generación. No borrar guardas de otras acciones indiscriminadamente. Revisar formularios web y API conjuntamente. No marcar cuidado done por crear alarma.

Añadir módulo Flutter notifications para programar/cancelar próximo aviso con plugin mantenido y compatible, a seleccionar y fijar tras revisar documentación oficial y Flutter3.47.7. No dependencia instalada en DOCUMENTAR. AndroidManifest/Gradle e Info.plist/AppDelegate según requisitos reales. No requerir Firebase para aviso local. Push existente de recordatorios deberá coordinarse mediante preferencia por dispositivo/tipo: no emitir local y push para la misma ocurrencia; distinguir riesgo MediaPipe. Revisar CuidadosApp/api/devices.py, mobile_models.py y worker send_mobile_reminders. Si requiere campos nuevos, migración aditiva con pruebas y aplicación únicamente demo autorizada; nunca DB real.

Guardar solo identificadores/instantes mínimos. Sincronizar al login, volver a primer plano, mutación confirmada y recuperar red; cancelar por logout/cambio de cuenta. Cuando app está cerrada no asumir ejecución de Dart. Probar reinicio, ahorro de batería, zona America/Santiago y cambios de hora; indicar límites de notificaciones programadas por SO y permisos de exactitud. No prometer alertas exactas si no se conceden permisos. Una sola ocurrencia futura por reloj limita almacenamiento y avisos obsoletos; cambios remotos offline no se conocen hasta sincronización.

## Identidad compartida y diseño

Reutilizar allauth/headless, API v1, PlanesApp/entitlements.py y capacity.py. URL de portal deriva de configuración validada; abrir navegador sin token en query string, login web puede requerir sesión propia. El backend sigue siendo fuente de derechos.

Paleta propuesta tomada de Flutter: marca#5057a0, fondo#f6f7fc, superficie#ffffff, texto#252a38; tinta secundaria#596071 y oscuro de marca a ajustar por contraste. Fuente del sistema actual conservada. Tarjetas blancas suaves, botones índigo, títulos alineados a izquierda, navegación existente adaptada. Extender tokens.css; mantener estados éxito/error/aviso independientes y modo oscuro contrastado. Reutilizar static/css/styles.css, PlanesApp/static/PlanesApp/planes.css, templates/components/Layout/, navbar y pages/PlanesApp; actualizar caché y Tailwind si cambian clases/fuentes. No copiar selector de roles del prototipo. Aplicar frontend-design y docs/PERSONALIZACION_VISUAL.md.

## Organización física propuesta

```text
Planes-pagina/
  web/        # manage.py, core/, UsuarioApp/, homeApp/, PlanesApp/, CuidadosApp/, theme/, templates/, static/
  mobile/     # Flutter Android/iOS, assets y plugins/vigia_pose
  edge/       # nodo fijo MediaPipe
  docs/       # contrato/API, diseño, instalación y operación
  specs/      # trazabilidad SDD
```

Flutter lib/: app/theme y navegación; core/api y sesión; features/auth, patients, medications, posture, subscription, profile; shared/widgets; notifications y detection separados. Extraer gradualmente care.dart/main.dart, conservando tests y conducta. No inventar servicios remotos nuevos.

Inventario previo de todos los consumidores de BASE_DIR, rutas assets, scripts, pyproject, requirements, @source, instrucciones y docs. Mover código con historial lógico, sin sobreescribir cambios locales; no commit automático. BASE_DIR Django será web/, raíz de repo explícita donde se necesite mobile/build/web o edge. Configurar ubicaciones de entorno/DB/media por rutas explícitas para no crear otra DB silenciosamente. Conservar .mobile-demo y entornos en su ubicación hasta acuerdo; no mover secretos ni leerlos. Actualizar ignore, guía, comandos, enlaces Markdown e instrucciones de rutas. Migraciones conservan nombres/imports y app labels. Entrega incluye manifiesto antes/después para recuperación selectiva; no copiar RAR encima del proyecto.

## Dispositivos y validación

Android: APK de prueba compatible con teléfonos objetivo; actual ARM64 debug es antecedente, requiere API alcanzable. iOS: build simulador primero, luego dispositivo/firma de desarrollo o TestFlight según cuenta disponible. No publicar ni adquirir cuenta. Hoy se observaron11GB libres; volver a medir antes de descargar/build. No confundir nuevo espacio con build exitoso.

Backend: core.test_settings, check, makemigrations --check --dry-run y suite UsuarioApp homeApp PlanesApp CuidadosApp. Flutter: analyze, tests significativos de reloj/cancelación/identidad/concurrencia, builds Android/iOS y pruebas físicas separadas. UI navegador real para web y preview, incluyendo nuevo reloj vacío y estilo. Ver docs/ENTORNO_Y_VERIFICACION.md antes de ejecutar. Instalar en dispositivos requiere conexión/disponibilidad del propietario; no afirmar completado con solo compilación.

Referencias consultadas22/10/2026: [iOS/Flutter](https://docs.flutter.dev/deployment/ios), [TestFlight](https://developer.apple.com/testflight/), [alarmas Android](https://developer.android.com/develop/background-work/services/alarms). Restricciones exactas/plugin se revalidan al implementar.


## Autorización22/10/2026
El usuario indica «perfecto ahora modificalo»: implementación completa011 autorizada. Los estados documentales anteriores son antecedentes; no autorización de producción/tiendas ni migración real.
