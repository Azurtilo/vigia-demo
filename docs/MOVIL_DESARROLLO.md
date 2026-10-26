# VIGIA móvil — pruebas locales

Para instalar en un teléfono (Android por USB o red local, iPhone en macOS) sigue [INSTALACION_CELULAR.md](INSTALACION_CELULAR.md); esta página conserva notas de desarrollo anteriores. iOS está en el alcance desde el 2026-10-26 (D-068).

Versión de desarrollo Flutter para Android/iOS. Backend Django existente, API por sesión y capacidades calculadas por servidor. No es una entrega publicada ni validada clínicamente. Estado y límites: [validación 010](../specs/010-aplicacion-movil/validation.md).

## Probar ahora en este Mac

La vista previa utiliza el mismo cliente Flutter, compilado para navegador: http://127.0.0.1:8000/mobile/ . Esta prueba no sustituye la ejecución nativa en teléfonos.

Cuentas ficticias: `demo_free`, `demo_plus`, `demo_premium`. Contraseña de estas tres cuentas locales: `VigiaDemo-2026!`. No corresponden a cuentas reales. Prueba agenda, pacientes, medicamentos, postura manual, historial y Mi plan. Premium habilita vinculación del nodo; sin nodo/calibración se muestra ausencia de observaciones.

Si el servidor se detiene, desde la raíz:

```bash
.venv-mobile/bin/python manage.py runserver 127.0.0.1:8000 --settings=core.mobile_demo_settings --noreload
```

La demo usa exclusivamente `.mobile-demo/demo.sqlite3`, datos ficticios, correo en consola y configuración local de pruebas; no lee `.env`. No exponer esta configuración a Internet. Para recrearla en otra copia de desarrollo, preparar entorno con `requirements.txt`, ejecutar `migrate --settings=core.mobile_demo_settings` y `seed_mobile_demo --settings=core.mobile_demo_settings`. No ejecutar estos pasos sobre settings de producción.

## Android

APK debug: `mobile/build/app/outputs/flutter-apk/app-debug.apk`. Se instala en Android, no en iPhone. El valor inicial del servidor es `http://10.0.2.2:8000`, que apunta al Mac desde el emulador Android.

Para teléfono físico, conectar Mac y teléfono a la misma red local. Reiniciar la demo indicando la IP LAN del Mac (reemplazar `192.168.1.20`):

```bash
VIGIA_DEMO_HOSTS=192.168.1.20 .venv-mobile/bin/python manage.py runserver 0.0.0.0:8000 --settings=core.mobile_demo_settings --noreload
```

En la pantalla de ingreso, abrir **Servidor de pruebas** y usar `http://192.168.1.20:8000`. El servidor debe permanecer activo; permitir acceso en la red local si el sistema lo solicita. La selección de servidor y HTTP están limitados a compilaciones debug. Release exige HTTPS.

## Flutter e iOS

SDK utilizado en esta sesión: `/tmp/vigia-flutter-sdk/bin/flutter` (3.47.7/Dart 3.13.5); `/tmp` es temporal. Para desarrollo permanente instalar Flutter en una ruta propia. Desde `mobile/`:

```bash
flutter pub get
flutter analyze
flutter test
flutter build apk --debug --dart-define=API_URL=http://10.0.2.2:8000
flutter build ios --simulator --debug --no-codesign
flutter run -d <identificador-dispositivo> --dart-define=API_URL=https://servidor-de-pruebas.example
```

Para iPhone físico se requiere equipo/firma Apple y servidor accesible. El proyecto incluye `ios/`; no hay IPA firmada ni publicación. Consultar resultado real del intento iOS en validación. Vista previa: `flutter build web --debug --base-href /mobile/`.

## Planes y datos

Free: 1 paciente; Plus: 3; Premium: ilimitados. Todos conservan cuidados manuales, medicamentos, guías e historial. Premium habilita detección y alertas de riesgo; el servidor revalida vigencia y paciente habilitado en cada evento. Los cupos usan la lógica de selección/archivo existente. No existe colaboración entre cuentas todavía; cada titular ve solo sus pacientes, también si es superusuario.

## Nodo local MediaPipe

El teléfono consulta los resultados; el procesamiento de cámara ocurre en un nodo local según el informe. Ver [edge/README.md](../edge/README.md). No se transmiten imágenes, videos ni landmarks a Django. Detecciones automáticas y cuidados manuales se guardan separados.

## Integraciones externas pendientes

- Google: configurar clientes OAuth Android/iOS/web del proyecto, SHA de firma Android y esquema URL iOS; `GOOGLE_CLIENT_ID`/`GOOGLE_SERVER_CLIENT_ID` mediante dart-define y configuración allauth del servidor. El flujo está escrito, no verificado con credenciales reales.
- Firebase: configurar proyecto y aplicaciones nativas/APNs; `FIREBASE_PROJECT_ID`, `FIREBASE_API_KEY`, `FIREBASE_APP_ID`, `FIREBASE_SENDER_ID` específicos por plataforma. Validar capacidades/firma y entrega real en cada SO. El botón informa configuración faltante; no finge envío.
- Servidor push: instalar `requirements-push.txt` en entorno previsto, credencial Firebase externa mediante Application Default Credentials y setting `VIGIA_PUSH_ENABLED=True`. Ejecutar periódicamente `python manage.py send_mobile_reminders` con settings de ese entorno. No se ha instalado un scheduler ni enviado mensajes reales. Pendientes rotación de token, recepción en primer plano y prueba de segundo plano/cierre por plataforma.
- Migración aditiva CuidadosApp 0004 pendiente en cualquier DB existente; solo aplicada a demo y pruebas. Revisar respaldo y autorización antes de una migración real.

## Actualización de referencia — 2026-10-20

Código actualizado a Inicio/Pacientes/Medicinas/Posturas/Plan/Perfil. Cámara dual: nodo fijo existente y cámara del teléfono con análisis puntual. `mobile/plugins/vigia_pose` integra MediaPipe nativo; referencias solo en sesión. Se requiere resolver nuevas dependencias con `flutter pub get` y CocoaPods para iOS, ejecutar análisis/tests y recompilar. El SDK temporal indicado arriba ya no existe. El APK y build/web actuales son versiones anteriores, no sirven como evidencia de esta UI/cámara nueva.

Migración0005 pendiente en demo/DB real. Para demo exclusivamente, después de detener el servidor: `python manage.py migrate --settings=core.mobile_demo_settings`. Nunca usar ese comando sin settings explícito. No se ejecutó migración real.


## Versión comprobada — 2026-10-21

Sustituye las notas anteriores de SDK ausente y APK obsoleto: SDK3.47.7 restaurado, dependencias resueltas y APK nuevo en [app-debug.apk](../mobile/build/app/outputs/flutter-apk/app-debug.apk), solo Android ARM64. No es una entrega firmada de producción. Vista local: http://127.0.0.1:8000/mobile/ con servidor demo activo y cuentas ficticias indicadas arriba. Migración0005 ya aplicada en demo; sigue pendiente en cualquier DB real.

El APK usa inicialmente http://10.0.2.2:8000 (emulador Android); un teléfono físico necesita servidor de pruebas accesible y configurar su dirección desde «Servidor de pruebas» en login. No usar127.0.0.1 del teléfono para conectar al Mac. Para acceso LAN se debe configurar VIGIA_DEMO_HOSTS y escuchar en la interfaz correspondiente; el servidor actual solo escucha en127.0.0.1. No exponer la demo a Internet.

MediaPipe ahora tiene dos orígenes: análisis puntual local en teléfono (calibrar, analizar y guardar metadatos) y monitoreo continuo mediante nodo fijo. La vista web no ejecuta la cámara del teléfono. Inferencia real pendiente de prueba física. iOS pendiente de espacio, SDK/CocoaPods y compilación. Ver [resultados y limitaciones](../specs/010-aplicacion-movil/validation.md).

## Roles en la app (spec 013), 2026-10-25

`GET /api/v1/patients` y `GET /api/v1/patients/<id>` incluyen `role` y `allowed_actions`; la app oculta lo que el rol no permite y no pide historial, observaciones ni nodos si no corresponde. Endpoints nuevos: `patients/<id>/access` (titular), `access/preview`, `access/accept`, `access/<id>/revoke`, `invitations/<id>/revoke`, `patients/<id>/leave` y `patients/<id>/summary`. Un servidor sin roles mantiene el comportamiento anterior (`features/patients/access.dart`).

## Privacidad en la app (spec 014), 2026-10-25

Si la API responde 403 con `consent_required`, la app muestra un aviso con botón al portal (`/privacidad/aceptar/`). Al agregar un paciente pide quién da el consentimiento y envía `consent_basis`, `representative_name`, `representative_relation` y `consent_confirm`. El perfil enlaza la política y la exportación o eliminación de la cuenta en el portal (`features/profile/privacy.dart`).
