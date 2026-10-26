# Tareas — 016 / Correcciones de la QA del 2026-10-26

Spec: [spec.md](spec.md). Plan: [plan.md](plan.md).
Estado: en implementación. Rama: `feature/016-correcciones-qa`, un commit por tarea (D-059).

- [x] T-016-01 — Pillow y certifi actualizados; herramientas de desarrollo fuera de producción.
  - RF: RF-016-01, 02. Hallazgos: QA-2026-10-26-01, 06 y 08.
  - Hecho cuando: el lock se instala con hashes en un entorno limpio, las suites Django pasan y `pip-audit` no reporta vulnerabilidades en `web/requirements.txt`.
- [ ] T-016-02 — Comando de pruebas completo e integración continua mínima.
  - RF: RF-016-03, 04. Hallazgos: QA-2026-10-26-02 y 03.
  - Hecho cuando: los documentos vigentes indican `PrivacidadApp` y el CI pasa en la PR.
- [ ] T-016-03 — Guía para programar la purga y los avisos.
  - RF: RF-016-05. Hallazgo: QA-2026-10-26-04.
  - Hecho cuando: `docs/OPERACION.md` existe, está enlazada y sus comandos se probaron contra la demo. La configuración del servidor real queda pendiente del propietario.

## Autorización posterior
2026-10-26: «empieza por corregir alguno de los hallazgos, en especifico: Actualizar Pillow y certifi y sacar black de producción. Agregar PrivacidadApp al comando de pruebas documentado y crear una integración continua mínima. Programar la purga de datos y los avisos periódicos en el despliegue». Autorizadas T-016-01..03. Sin merge, despliegue ni migración real.

## Ejecución
| Fecha | Tarea | Archivos / comando | Resultado / pendiente |
|---|---|---|---|
| 2026-10-26 | T-016-01 | `web/requirements.in`, `requirements.txt`, `requirements-dev.in`, `requirements-dev.txt` (pip-tools 7.6.1, pip 26.2.1, entorno aparte); `docs/DEPENDENCIAS.md` | Cambian solo Pillow 12.3.0 → 13.0.0 y certifi 2026.7.22 → 2026.10.23; salen `black`, `cookiecutter`, `ruff`, `types-python-dateutil` y `pytokens` (dependencia de `black`). Entorno limpio con `--require-hashes`: `check` sin problemas y Django 235 OK. `pip-audit`: sin vulnerabilidades en ambos locks. `.venv` actualizado |

## Reanudación
2026-10-26: spec, plan y tareas creados; implementación en curso.

## Aceptación del usuario
Pendiente.
