# VIGIA

VIGIA es un sistema de apoyo al cuidado domiciliario de personas con dependencia. Lo desarrollamos como Proyecto de Título en INACAP. Une tres partes: un portal web para la familia, una app móvil para el cuidador y un nodo local que analiza la postura de la persona cuidada sin enviar video a la nube.

> Estado: piloto técnico en desarrollo. No tiene validación clínica. Las metas del informe (alerta de caída en ≤ 10 s, inferencia < 100 ms, detección ≥ 90 %) todavía no se han medido; la evidencia real se registra en el `validation.md` de cada spec.

## Qué hace

- La familia configura el plan de cuidados y los horarios de medicación, y gestiona su suscripción (Free, Plus o Premium) en el portal web.
- El cuidador ve su agenda diaria, confirma la administración de cada medicamento y registra los cambios de posición en la app móvil.
- La familia consulta el historial del cuidado y recibe avisos ante eventos de riesgo.
- El nodo local usa MediaPipe Pose Landmarker para clasificar la postura y detectar inmovilidad prolongada. Solo envía metadatos al servidor (postura, confianza, fecha y riesgo), nunca imágenes.

## Componentes

| Carpeta | Componente | Tecnología |
|---|---|---|
| [web/](web/) | Backend, API y portal web (`core`, `UsuarioApp`, `homeApp`, `PlanesApp`, `CuidadosApp`, `theme`) | Django 5.2, allauth, Tailwind standalone |
| [mobile/](mobile/) | App del cuidador y de la familia, con el plugin nativo `plugins/vigia_pose` | Flutter (Android primero; iOS se compila en macOS) |
| [edge/](edge/) | Nodo local de análisis de postura | Python 3.12, MediaPipe, OpenCV |
| [docs/](docs/), [specs/](specs/) | Documentación, decisiones y trazabilidad SDD | Markdown |

El `manage.py` de la raíz delega en `web/manage.py`, así que los comandos Django funcionan desde la raíz o desde `web/`.

## Entorno por sistema operativo

**Cada integrante crea sus entornos virtuales en su propio equipo. Los entornos nunca se suben al repositorio** (están en `.gitignore`). Un entorno creado en macOS no funciona en Windows, ni al revés: no se copian entre equipos.

Para que una misma carpeta compartida no mezcle entornos, cada sistema usa nombres distintos:

| Uso | Windows | macOS |
|---|---|---|
| Web (Django) | `.venv` | `.venv-mobile` (nombre que ya usan los integrantes con Mac) |
| Edge (MediaPipe) | `.venv-edge-win` | `.venv-edge` |
| Mobile (Flutter) | SDK de Flutter instalado en el equipo | SDK de Flutter instalado en el equipo |

Requisitos: Python 3.12 y Flutter 3.47.7 (Dart 3.13.5, como exige `mobile/pubspec.yaml`).

### Windows (PowerShell)

Desde la raíz del repositorio:

```powershell
# Web
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install --require-hashes -r web/requirements.txt

# Edge
py -3.12 -m venv .venv-edge-win
.venv-edge-win\Scripts\python.exe -m pip install -r edge/requirements.txt

# Mobile (con Flutter en el PATH)
cd mobile
flutter pub get
cd ..
```

### macOS (zsh)

Desde la raíz del repositorio:

```zsh
# Web
python3.12 -m venv .venv-mobile
.venv-mobile/bin/python -m pip install --require-hashes -r web/requirements.txt

# Edge
python3.12 -m venv .venv-edge
.venv-edge/bin/python -m pip install -r edge/requirements.txt

# Mobile (con Flutter en el PATH)
cd mobile
flutter pub get
cd ..
```

En los ejemplos siguientes, `PY_WEB` y `PY_EDGE` significan el intérprete del entorno de tu sistema. En Windows son `.venv\Scripts\python.exe` y `.venv-edge-win\Scripts\python.exe`. En macOS son `.venv-mobile/bin/python` y `.venv-edge/bin/python`.

## Cómo ejecutar

### Web

La configuración normal lee un archivo `.env` en la raíz. `SECRET_KEY` es obligatoria; `DEBUG`, `ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS` son opcionales. El `.env` es personal y nunca se sube al repositorio.

Para probar en local con datos ficticios, usa la configuración de demo. No lee `.env` y crea su propia base en `.mobile-demo/`:

```bash
PY_WEB manage.py migrate --settings=core.mobile_demo_settings
PY_WEB manage.py seed_mobile_demo --settings=core.mobile_demo_settings
PY_WEB manage.py runserver 127.0.0.1:8000 --settings=core.mobile_demo_settings --noreload
```

El portal queda en http://127.0.0.1:8000/. Las cuentas ficticias y el acceso desde un teléfono están en [docs/MOVIL_DESARROLLO.md](docs/MOVIL_DESARROLLO.md). No ejecutes `migrate` sin `--settings` sobre una base existente.

### Mobile

Con el servidor de demo activo, desde `mobile/`:

```bash
flutter run --dart-define=API_URL=http://10.0.2.2:8000
flutter build apk --debug --dart-define=API_URL=http://10.0.2.2:8000
```

`10.0.2.2` es el equipo anfitrión visto desde el emulador Android. Para un teléfono físico, Android o iPhone, sigue [docs/INSTALACION_CELULAR.md](docs/INSTALACION_CELULAR.md). iOS está en el alcance desde el 2026-10-26 (D-068) y se compila solo en macOS.

### Edge

El modelo va en `edge/models/pose_landmarker_lite.task`. Esa carpeta está en `.gitignore`. Copia el modelo que ya trae la app móvil o descárgalo desde la [documentación de MediaPipe](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker):

```powershell
# Windows
New-Item -ItemType Directory -Force edge/models
Copy-Item mobile/assets/models/pose_landmarker_lite.task edge/models/
```

```zsh
# macOS
mkdir -p edge/models
cp mobile/assets/models/pose_landmarker_lite.task edge/models/
```

Calibración y monitoreo (detalle, consentimiento y token del nodo en [edge/README.md](edge/README.md)):

```bash
PY_EDGE -m edge.run --references edge/models/referencias.json --camera ruta/video-autorizado.mp4 --calibrate supina
PY_EDGE -m edge.run --references edge/models/referencias.json --camera 0 --server http://127.0.0.1:8000 --allow-local-http
```

## Pruebas

```bash
# Web, desde web/
PY_WEB manage.py check --settings=core.test_settings
PY_WEB manage.py makemigrations --check --dry-run --settings=core.test_settings
PY_WEB manage.py test UsuarioApp homeApp PlanesApp CuidadosApp PrivacidadApp --settings=core.test_settings

# Edge, desde la raíz
PY_EDGE -m unittest edge.test_posture

# Mobile, desde mobile/
flutter analyze
flutter test
```

Las pruebas Django usan `core.test_settings`: SQLite en memoria y sin leer `.env`. Las pruebas de Edge son geométricas y sintéticas; no prueban la precisión con personas reales.

## Documentación

| Necesidad | Archivo |
|---|---|
| Estado actual y punto de reanudación | [docs/ESTADO_PROYECTO.md](docs/ESTADO_PROYECTO.md) |
| Specs y spec vigente | [specs/README.md](specs/README.md), [specs/011-ecosistema-instalable/](specs/011-ecosistema-instalable/) |
| Decisiones y trazabilidad | [docs/DECISIONES.md](docs/DECISIONES.md), [docs/TRAZABILIDAD.md](docs/TRAZABILIDAD.md) |
| Entorno y verificación | [docs/ENTORNO_Y_VERIFICACION.md](docs/ENTORNO_Y_VERIFICACION.md) |
| App móvil y demo | [docs/MOVIL_DESARROLLO.md](docs/MOVIL_DESARROLLO.md) |
| Flujo de trabajo SDD y reglas del agente | [constitution.md](constitution.md), [AGENTS.md](AGENTS.md), [MANUAL_SDD.md](MANUAL_SDD.md) |
| Base Django original e historial de evolución | [docs/BASE_ORIGINAL.md](docs/BASE_ORIGINAL.md) |

## Equipo

- José Acuña
- Constanza Contreras
- Sandra Santos
