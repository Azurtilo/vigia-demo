# Tareas — 016 / Correcciones de la QA del 2026-10-26

Spec: [spec.md](spec.md). Plan: [plan.md](plan.md).
Estado: en implementación. Rama: `feature/016-correcciones-qa`, un commit por tarea (D-059).

- [x] T-016-01 — Pillow y certifi actualizados; herramientas de desarrollo fuera de producción.
  - RF: RF-016-01, 02. Hallazgos: QA-2026-10-26-01, 06 y 08.
  - Hecho cuando: el lock se instala con hashes en un entorno limpio, las suites Django pasan y `pip-audit` no reporta vulnerabilidades en `web/requirements.txt`.
- [x] T-016-02 — Comando de pruebas completo e integración continua mínima.
  - RF: RF-016-03, 04. Hallazgos: QA-2026-10-26-02 y 03.
  - Hecho cuando: los documentos vigentes indican `PrivacidadApp` y el CI pasa en la PR.
- [x] T-016-03 — Guía para programar la purga y los avisos.
  - RF: RF-016-05. Hallazgo: QA-2026-10-26-04.
  - Hecho cuando: `docs/OPERACION.md` existe, está enlazada y sus comandos se probaron contra la demo. La configuración del servidor real queda pendiente del propietario.

## Autorización posterior
2026-10-26: «empieza por corregir alguno de los hallazgos, en especifico: Actualizar Pillow y certifi y sacar black de producción. Agregar PrivacidadApp al comando de pruebas documentado y crear una integración continua mínima. Programar la purga de datos y los avisos periódicos en el despliegue». Autorizadas T-016-01..03. Sin merge, despliegue ni migración real.

## Ejecución
| Fecha | Tarea | Archivos / comando | Resultado / pendiente |
|---|---|---|---|
| 2026-10-26 | T-016-01 | `web/requirements.in`, `requirements.txt`, `requirements-dev.in`, `requirements-dev.txt` (pip-tools 7.6.1, pip 26.2.1, entorno aparte); `docs/DEPENDENCIAS.md` | Cambian solo Pillow 12.3.0 → 13.0.0 y certifi 2026.7.22 → 2026.10.23; salen `black`, `cookiecutter`, `ruff`, `types-python-dateutil` y `pytokens` (dependencia de `black`). Entorno limpio con `--require-hashes`: `check` sin problemas y Django 235 OK. `pip-audit`: sin vulnerabilidades en ambos locks. `.venv` actualizado |
| 2026-10-26 | T-016-02 | Comando con `PrivacidadApp` en `CLAUDE.md`, `AGENTS.md`, `README.md`, `docs/ENTORNO_Y_VERIFICACION.md`, `docs/CUIDADOSAPP_DESARROLLO.md`, `prompts/04-implementar.md`, `.claude/agents/qa-vigia.md` y la skill `validar-produccion-sdd`; nuevo `.github/workflows/ci.yml` (Django, Edge, Flutter y `pip-audit`) | Sin documentos vigentes con el comando antiguo (las líneas fechadas de `ENTORNO_Y_VERIFICACION.md` se conservan). El CI se comprueba en la PR |
| 2026-10-26 | T-016-02 (corrección) | `.github/workflows/ci.yml` | La auditoría combinada de los tres archivos falló en local (pip no mezcla requisitos con y sin hashes), aunque el commit anterior la daba por probada. Ahora se audita un archivo por paso, incluido `requirements-dev.txt`; los cuatro se probaron en local sin vulnerabilidades |
| 2026-10-26 | T-016-03 | `docs/OPERACION.md` (nueva), enlaces en `docs/CUIDADOSAPP_DESARROLLO.md` y `README.md` | Contra la demo: `purge_expired_data --dry-run` informa cantidades sin borrar; `send_mobile_reminders` termina con «VIGIA_PUSH_ENABLED está desactivado»; el comando para ver la última purga responde `None` (nunca hubo una purga real). Hallado: `VIGIA_PUSH_ENABLED` no se define en ninguna configuración ni se lee del entorno. Pendiente del propietario: configurar las tareas en el servidor real |
| 2026-10-26 | T-016-02 (CI en GitHub) | [Ejecución 40415661262](https://github.com/Azurtilo/vigia-demo/actions/runs/40415661262) en la [PR #11](https://github.com/Azurtilo/vigia-demo/pull/11) | Los cuatro trabajos pasan: Django 235 pruebas (35 s), Edge 22 (16 s), Flutter `analyze` sin problemas y 46 pruebas (1 m 44 s), `pip-audit` sin vulnerabilidades en los cuatro archivos (47 s). El push necesitó agregar el permiso `workflow` a la credencial de `gh` |

## Reanudación
2026-10-26: T-016-01..03 hechas y CI verde en la PR #11. Fusión autorizada: «fusiona 10 y 11 y registra los demas en pendientes». Pendientes registrados en `ESTADO_PROYECTO.md` (14–16). Pendientes del propietario: tareas en el servidor y activación de `VIGIA_PUSH_ENABLED`.

## Aceptación del usuario
Pendiente.
