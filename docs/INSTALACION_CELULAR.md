# Instalar y probar VIGIA en el celular

Guía para el equipo que prueba la app en un teléfono con la demo local. Solo datos ficticios: la demo usa su propia base (`.mobile-demo/demo.sqlite3`), no lee `.env` y no debe exponerse a Internet ([MOVIL_DESARROLLO.md](MOVIL_DESARROLLO.md)).

Alcance: Android primero e iOS en el alcance ([D-068](DECISIONES.md)). iOS se compila solo en macOS con Xcode. No hay publicación en Google Play ni en App Store.

| Plataforma | Estado | Evidencia |
|---|---|---|
| Android | Probado en un teléfono físico el 2026-10-26 | [validation.md de la spec 015](../specs/015-integracion-unificado/validation.md#android-físico--t-015-07-2026-10-26) |
| iPhone | Procedimiento preparado, **sin validar** (T-015-08..10, a cargo de Sandra) | Pendiente |

## 1. Preparar la demo

Una sola vez, en el equipo que hará de servidor:

```bash
# Windows (Git Bash), desde web/
../.venv/Scripts/python.exe manage.py migrate --settings=core.mobile_demo_settings
../.venv/Scripts/python.exe manage.py seed_mobile_demo --settings=core.mobile_demo_settings
```

En macOS, el mismo comando con el Python del entorno de esa máquina. `seed_mobile_demo` crea las cuentas ficticias `demo_free`, `demo_plus` y `demo_premium` y, al terminar, muestra la contraseña local. No la copies en documentos ni en mensajes. El comando se niega a correr con otra configuración que no sea `core.mobile_demo_settings`.

## 2. Android

Hay dos maneras de conectar el teléfono con la demo.

### Opción A: cable USB (recomendada para probar)

Es la que se usó en las pruebas del 2026-10-25 y del 2026-10-26. El servidor escucha solo en el propio equipo y el teléfono llega por el cable.

1. Activa la depuración USB en el teléfono, conéctalo y acepta la huella del equipo. `adb devices` debe mostrarlo como `device`.
2. Inicia la demo, desde `web/`:

   ```bash
   ../.venv/Scripts/python.exe manage.py runserver 127.0.0.1:8000 --noreload --settings=core.mobile_demo_settings
   ```

3. Abre el túnel: `adb reverse tcp:8000 tcp:8000`.
4. Compila e instala, desde `mobile/`:

   ```bash
   flutter build apk --debug --target-platform android-arm64 --dart-define=API_URL=http://127.0.0.1:8000
   adb install -r build/app/outputs/flutter-apk/app-debug.apk
   ```

Si el teléfono se bloquea o se desconecta, el túnel puede perderse. La app avisa «No se pudo actualizar los avisos. Revisa la conexión». Revisa `adb reverse --list` y vuelve a ejecutar el paso 3.

### Opción B: red local (wifi)

Sirve sin cable, pero depende de la red y del firewall. Todavía no se ha validado en un teléfono físico.

1. Teléfono y equipo en la misma red. Averigua la IP privada del equipo (por ejemplo, con `ipconfig` en Windows) y úsala donde dice `<IP-del-servidor>`.
2. Inicia la demo aceptando esa IP, desde `web/`:

   ```bash
   VIGIA_DEMO_HOSTS=<IP-del-servidor> ../.venv/Scripts/python.exe manage.py runserver 0.0.0.0:8000 --noreload --settings=core.mobile_demo_settings
   ```

   `VIGIA_DEMO_HOSTS` solo admite IP privadas o locales. Si el sistema pregunta, permite el acceso en redes privadas; no desactives el firewall.
3. Genera el APK de descarga, desde la raíz:

   ```bash
   VIGIA_API_URL=http://<IP-del-servidor>:8000 sh mobile/tool/build_android.sh
   ```

   El APK queda en `artifacts/android/` (no se versiona).
4. Desde el navegador del teléfono abre `http://<IP-del-servidor>:8000/descargar/` y descarga el APK. Android pedirá permiso para instalar desde ese navegador. Si la página dice «APK Android no disponible», repite el paso 3.
5. En la app, «Servidor de pruebas» permite cambiar la dirección (solo en compilaciones debug; una compilación release exige HTTPS).

### Qué probar en Android

Repite el recorrido de la [validación](../specs/015-integracion-unificado/validation.md#android-físico--t-015-07-2026-10-26):

- inicio de sesión;
- HU-03 (confirmar un medicamento) y HU-04 (registrar un cambio de postura);
- «Activar avisos en este teléfono» y un aviso con la pantalla bloqueada;
- cierre de sesión sin avisos pendientes;
- pestaña Planes;
- vista de cuidador;
- aviso de política sin aceptar.

## 3. iPhone (macOS)

Procedimiento preparado según D-069 (Apple ID gratuito), **sin validar todavía**. Al ejecutarlo, registra el resultado en la validación de la spec 015 (T-015-08..10) y corrige esta sección si algo no coincide.

Requisitos: un Mac con Xcode y CocoaPods, unos 10 GB libres, un iPhone con iOS 15 o posterior y un cable.

1. Prepara la demo en el Mac (paso 1) e iníciala por la red local, como en la opción B de Android, con la IP del Mac.
2. Desde `mobile/`:

   ```bash
   flutter pub get
   cd ios && pod install && cd ..
   flutter build ios --simulator --debug
   ```

   El build de simulador es la primera comprobación (RF-015-09). MediaPipe puede no correr en simuladores de Apple Silicon; la cámara se prueba en el iPhone.
3. Abre `ios/Runner.xcworkspace` en Xcode. En *Signing & Capabilities* elige tu equipo personal (Personal Team). Si Xcode lo pide, ajusta el identificador del paquete para tu equipo, sin versionar ese cambio.
4. Conecta el iPhone, activa el modo desarrollador y ejecuta desde `mobile/`: `flutter run -d <id-del-iphone>`. En el iPhone, confía en el certificado del desarrollador (Ajustes → General → VPN y gestión de dispositivos).
5. En la app, «Servidor de pruebas» → `http://<IP-del-servidor>:8000`. Acepta el permiso de red local. La app ya admite HTTP solo en la red local (`NSAllowsLocalNetworking`).

Con Apple ID gratuito:

- El perfil vence a los 7 días; para seguir probando, vuelve a ejecutar el paso 4.
- No hay push de riesgo en iPhone (D-069): HU-05 se comprueba en Android.
- Los avisos locales del reloj sí funcionan y deben probarse con la pantalla bloqueada (RF-015-11).

No se versionan certificados, perfiles, `GoogleService-Info.plist` ni claves `.p8` (D-054).

## Problemas frecuentes

| Síntoma | Qué revisar |
|---|---|
| La app no conecta | USB: `adb reverse --list`. Red local: que la IP esté en `VIGIA_DEMO_HOSTS`, que el servidor escuche en `0.0.0.0` y que el firewall permita el puerto 8000 en redes privadas |
| `INSTALL_FAILED_UPDATE_INCOMPATIBLE` | La app instalada se firmó en otro equipo. Desinstálala (se pierden sus datos locales) e instala de nuevo |
| El aviso llega tarde | Sin permiso de alarmas exactas el horario es aproximado; la app lo indica en el reloj |
| `/descargar/` no ofrece el APK | Ejecuta `mobile/tool/build_android.sh` y recarga |
