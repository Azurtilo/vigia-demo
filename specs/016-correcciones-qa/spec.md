# 016 — Correcciones de la revisión de calidad del 2026-10-26

Estado: en implementación. Fecha: 2026-10-26.
Módulo: cambio transversal (dependencias de `web/`, documentación de comandos, integración continua y operación). Fuente: [QA_2026-10-26.md](../../docs/QA_2026-10-26.md) y pedido del propietario del 2026-10-26: «empieza por corregir alguno de los hallazgos, en especifico: Actualizar Pillow y certifi y sacar black de producción. Agregar PrivacidadApp al comando de pruebas documentado y crear una integración continua mínima. Programar la purga de datos y los avisos periódicos en el despliegue».
Implementación autorizada: sí, T-016-01..03 (2026-10-26). Sin merge, despliegue ni migración real.

## Problema y resultado

La revisión de calidad encontró:
- dependencias de la web con vulnerabilidades conocidas: QA-2026-10-26-01 (Pillow), 06 (certifi) y 08 (`black` en producción);
- un comando de pruebas que omite la privacidad, sin CI que lo compense: QA-2026-10-26-02 y 03;
- tareas periódicas sin programar: QA-2026-10-26-04.

Resultado esperado:
- dependencias de producción sin vulnerabilidades conocidas;
- un comando de pruebas documentado que corre todas las suites;
- un CI que lo ejecuta en cada PR;
- una guía de operación que deja listas para programar la purga y los avisos.

## Requisitos

- RF-016-01: `web/requirements.txt` usa Pillow 13.x y un certifi sin avisos, regenerado con pip-tools y hashes (D-005, `docs/DEPENDENCIAS.md`). `pip-audit` no reporta vulnerabilidades en `web/requirements.txt`. Las pruebas de foto de perfil siguen pasando.
- RF-016-02: las herramientas de desarrollo (`black`, `ruff`, `cookiecutter`, `types-python-dateutil`) salen de `requirements.txt` y pasan a `requirements-dev.txt`, también con hashes y restringido por el lock de producción. El servidor no las instala.
- RF-016-03: `CLAUDE.md`, `AGENTS.md`, `docs/ENTORNO_Y_VERIFICACION.md` y el agente `qa-vigia` indican el comando de pruebas con `PrivacidadApp`.
- RF-016-04: un flujo de GitHub Actions se ejecuta en cada PR hacia `develop` o `main` y en cada push a `develop`. Corre los mismos comandos documentados:
  - Django: `check`, `makemigrations --check` y pruebas;
  - Edge: pruebas unitarias;
  - Flutter: `analyze` y `test`;
  - `pip-audit` de los requisitos de Python.

  Usa versiones fijas de las acciones y del SDK, sin secretos.
- RF-016-05: `docs/OPERACION.md` indica cómo programar en el servidor:
  - `purge_expired_data`, una vez al día;
  - `send_mobile_reminders`, cada 5 minutos (propuesta: P-012-01 sigue abierta).

  Incluye ejemplos de cron y del Programador de tareas de Windows, el registro de la salida y la verificación con `--dry-run`. No se configura ningún servidor real desde el repositorio.

## Aceptación

| RF | Comprobación |
|---|---|
| 01–02 | `pip install --require-hashes -r web/requirements.txt` en un entorno limpio; suites Django verdes; `pip-audit` sin hallazgos en el lock de producción |
| 03 | La búsqueda del comando antiguo sin `PrivacidadApp` no encuentra documentos vigentes |
| 04 | El CI corre en la PR de esta spec y pasa |
| 05 | Los comandos de la guía se ejecutan en local contra la demo (`purge_expired_data --dry-run`; `send_mobile_reminders` informa que el push está desactivado) |

## Fuera de alcance

- Los demás hallazgos de la QA del 2026-10-26.
- Configurar el servidor de producción, que requiere su acceso (pendiente del propietario).
- Decidir P-012-01.
- Actualizar dependencias de Flutter (QA-2026-10-26-12).
- Lock con hashes del Edge (QA-2026-10-26-07).

## Revisión y cambios

- 2026-10-26: creada con autorización de implementación en el mismo pedido.
