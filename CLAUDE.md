# CLAUDE.md — Proyecto VIGIA

**Sigue [AGENTS.md](AGENTS.md)** y [constitution.md](constitution.md): fases SDD (spec → plan → tasks antes de código), permisos, comandos y cierre documental. Este archivo solo añade el contexto del proyecto; ante conflicto prevalecen AGENTS.md y las instrucciones explícitas del usuario.

## Proyecto

VIGIA (Proyecto de Título, INACAP): apoyo al cuidado domiciliario de personas con dependencia.

| Carpeta | Componente |
|---|---|
| `web/` | Backend y portal Django (`core`, `UsuarioApp`, `homeApp`, `PlanesApp`, `CuidadosApp`, `theme`). `manage.py` raíz delega en `web/manage.py` |
| `mobile/` | App Flutter (Android primero), `lib/features/*`, plugin `plugins/vigia_pose` |
| `edge/` | Nodo Python con MediaPipe Pose Landmarker |
| `docs/`, `specs/` | Documentación y trazabilidad SDD |

Antes de trabajar lee `README.md`, `docs/ESTADO_PROYECTO.md`, `specs/README.md` y la spec relacionada (vigente: `specs/011-ecosistema-instalable/`).

## Requerimientos del informe

Historias de usuario:

- **HU-01** Familiar configura plan de cuidados y horarios de medicación.
- **HU-02** Cuidador ve agenda diaria de tareas.
- **HU-03** Cuidador confirma administración de medicamento (registro auditable).
- **HU-04** Cuidador registra cambio de posición (reinicia temporizador).
- **HU-05** Familiar recibe push ante eventos de riesgo.
- **HU-06** Familiar ve historial y trazabilidad del cuidado delegado.
- **HU-07** Familiar gestiona su suscripción en el portal web.

Requerimientos técnicos:

- **RT-01** Edge analiza postura con MediaPipe.
- **RT-02** Detecta inmovilidad por tiempo configurable.
- **RT-03** Detecta caídas (cambio brusco de altura).

No funcionales:

- Sin video a la nube: solo metadatos.
- Alerta de caída en ≤ 10 s.
- Inferencia < 100 ms por cuadro.
- Backend con disponibilidad ≥ 99,5 %.
- Detección de caídas ≥ 90 % y falsos positivos ≤ 5 %.

Entorno: Windows, Android primero (iOS fuera de alcance), español es-CL.

Estas cifras son objetivos del informe, no resultados medidos: no declararlas cumplidas sin evidencia registrada en `validation.md`.

## Comandos (Windows)

Los venv `.venv-edge/` y `.venv-mobile/` del repo son de macOS (`bin/`), no sirven en Windows. Usa `.venv` en la raíz para web.

```bash
.venv/Scripts/python.exe -m pip install --require-hashes -r web/requirements.txt
cd web
../.venv/Scripts/python.exe manage.py check --settings=core.test_settings
../.venv/Scripts/python.exe manage.py makemigrations --check --dry-run --settings=core.test_settings
../.venv/Scripts/python.exe manage.py test UsuarioApp homeApp PlanesApp CuidadosApp --settings=core.test_settings
```

- Edge (entorno separado, `edge/requirements.txt`): `python -m unittest edge.test_posture` desde la raíz.
- Flutter, desde `mobile/`: `flutter analyze` y `flutter test`. `pubspec.yaml` exige Dart ^3.13.5; el SDK local está fijado en Flutter 3.47.7 (`C:\Users\josea\flutter`).
