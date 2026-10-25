# Implementar después de revisión

Puedes pedir a la IA que lea este archivo en el proyecto. Si copias el mensaje, reemplaza los campos entre <...>. Los nombres/IDs de ejemplo no son trabajo autorizado.

```text
He revisado los documentos de <carpeta de spec>.
Autorizo implementar únicamente <IDs de tareas o alcance completo de esa spec>.
Esta instrucción es posterior a la fase documental.

Lee AGENTS.md, spec.md, plan.md y tasks.md. Comprueba cambios locales y conserva los míos.
Implementa en pasos pequeños reutilizando la base. Añade/ajusta las pruebas pertinentes, verifica permisos en servidor y no amplíes el alcance.
Ejecuta las verificaciones de cada componente tocado (Windows; los venv .venv-edge/ y .venv-mobile/ son de macOS y no sirven):
- web/: desde web/ con ../.venv/Scripts/python.exe: manage.py check, manage.py makemigrations --check --dry-run y manage.py test UsuarioApp homeApp PlanesApp CuidadosApp, siempre con --settings=core.test_settings.
- mobile/: flutter analyze y flutter test desde mobile/.
- edge/: python -m unittest edge.test_posture edge.test_fall edge.test_run desde la raíz, en su entorno separado (.venv-edge-win, edge/requirements.txt).
Si aparece una decisión crítica nueva, contradicción o migración con efectos no acordados, explica el bloqueo antes de asumirlo. No repitas preguntas ya resueltas.
Registra lo realmente ejecutado en tareas y validación; actualiza documentos que hayan cambiado y docs/ESTADO_PROYECTO.md.
Git según AGENTS.md (D-059): rama feature/NNN-nombre desde develop, un commit por tarea y PR hacia develop. No hagas merge, push a main, despliegues, migraciones reales ni uses datos reales por esta autorización.
Entrega cambios, resultados de pruebas, pendientes y siguiente paso.
```
