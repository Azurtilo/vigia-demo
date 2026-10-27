# Validación — 017 / Robustez de la detección de caídas

Entorno: Windows 10, rama `feature/017-robustez-caidas` desde `develop` (`2fedd78`). Web con `.venv` raíz y `core.test_settings` (SQLite en memoria). Edge con `.venv-edge-win` (MediaPipe 0.10.35, OpenCV 5.0.0.93) y modelo en `edge/models/`. Flutter 3.47.7.
Estado: verificación técnica **sintética**. Sin cámara real, servidor en vivo, personas ni Firebase real (T-017-13).

## Línea base (T-017-01), 2026-10-27

| Comando | Resultado |
|---|---|
| `manage.py check --settings=core.test_settings` | Sin problemas |
| `manage.py makemigrations --check --dry-run --settings=core.test_settings` | Sin cambios |
| `manage.py test UsuarioApp homeApp PlanesApp CuidadosApp PrivacidadApp --settings=core.test_settings` | **235 OK** |
| `python -m unittest edge.test_posture edge.test_fall edge.test_run` | **22 OK** |
| `flutter analyze` / `flutter test` | Sin problemas / **46 OK** |
| `python -m edge.bench sintetico.mp4` (300 cuadros de ruido, 640×480, 30 FPS, en el scratchpad de la sesión) | 0 personas; inferencia promedio 12,31 ms, p95 13,56 ms, máx 20,31 ms; 57,71 FPS; 0 caídas. **No mide el KPI** (sin persona en el cuadro) |
