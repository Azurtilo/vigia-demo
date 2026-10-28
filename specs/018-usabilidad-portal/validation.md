# Validación — 018 / Usabilidad del portal

Spec: [spec.md](spec.md). Plan: [plan.md](plan.md). Tareas: [tasks.md](tasks.md).
Entorno: Windows 10, `.venv` de la raíz, `core.test_settings`. Rama `feature/018-usabilidad-portal`.

## Revisión previa (2026-10-27)

Antes de la spec se renderizaron 21 páginas del portal en una base de pruebas desechable (prueba `audit_render`, fuera del repositorio) y se leyeron todas las redirecciones de las vistas. Los hallazgos están en la sección «Problema y resultado» de la [spec](spec.md). La base de la demo (`.mobile-demo/demo.sqlite3`) no se modificó: la prueba por wifi usó una copia migrada.

## Línea base — T-018-01

Sobre `develop` (`73fb6a1`), sin cambios de código:

| Comando | Resultado |
|---|---|
| `manage.py test UsuarioApp homeApp PlanesApp CuidadosApp PrivacidadApp --settings=core.test_settings` | 247 pruebas, OK |
