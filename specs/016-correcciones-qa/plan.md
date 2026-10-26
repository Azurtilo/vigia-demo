# Plan técnico — 016 / Correcciones de la QA del 2026-10-26

Spec: [spec.md](spec.md).

## Inspección

- `web/requirements.in` declara `pillow==12.3.0`, `certifi==2026.7.22` y, como «herramientas de desarrollo existentes», `cookiecutter`, `black`, `ruff` y `types-python-dateutil`. `requirements.txt` se genera con pip-tools 7.6.1 y pip 26.2.1 en un entorno aparte ([DEPENDENCIAS.md](../../docs/DEPENDENCIAS.md)).
- `cookiecutter` solo lo importa `django-tailwind` dentro de `tailwind init` (crear un tema), que no se ejecuta en el servidor. `black`, `ruff` y `types-python-dateutil` no se importan en el código. Las cuatro son herramientas de desarrollo.
- Pillow solo se usa en las fotos de perfil (`UsuarioApp/forms.py`, `utils/customer_img.py`).
- Las pruebas del Edge no importan MediaPipe ni OpenCV (`run.py` los importa al iniciar la cámara); solo necesitan `requests`.
- No hay `.github/`. El SDK de Flutter fijado es 3.47.7.
- `send_mobile_reminders` exige `VIGIA_PUSH_ENABLED` y Firebase; `purge_expired_data` admite `--dry-run`.

## Tareas y archivos

| Tarea | Archivos | Verificación |
|---|---|---|
| T-016-01 | `web/requirements.in`, `web/requirements.txt`, `web/requirements-dev.in`, `web/requirements-dev.txt`, `docs/DEPENDENCIAS.md` | Instalación con hashes en un entorno limpio, suites Django, `pip-audit` |
| T-016-02 | `CLAUDE.md`, `AGENTS.md`, `docs/ENTORNO_Y_VERIFICACION.md`, `.claude/agents/qa-vigia.md`, `.github/workflows/ci.yml` | Búsqueda del comando antiguo; CI verde en la PR |
| T-016-03 | `docs/OPERACION.md`, enlaces desde `docs/CUIDADOSAPP_DESARROLLO.md` y `README.md` | Comandos ejecutados contra la demo |

## Riesgos

- Pillow 13 es una versión mayor: se valida con las pruebas de foto de perfil, que procesan imágenes reales.
- El CI usa Ubuntu, y el lock se verificó en Windows. Si un hash no existe para Linux, el CI lo mostrará y se ajusta.
