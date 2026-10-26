# Instrucciones para agentes — VIGIA

## Contexto y lectura inicial

VIGIA apoya el cuidado domiciliario de personas con dependencia (Proyecto de Título, INACAP). Se construyó sobre una base Django existente: no reconstruir autenticación, usuarios, tema ni navegación. Tiene tres componentes:

| Carpeta | Componente |
|---|---|
| `web/` | Backend y portal Django: `core`, `homeApp`, `UsuarioApp`, `PlanesApp`, `CuidadosApp`, `theme`. El `manage.py` raíz delega en `web/manage.py` |
| `mobile/` | App Flutter, Android primero e iOS en el alcance (D-068; compilación iOS solo en macOS). Funciones en `lib/features/*`; plugin `plugins/vigia_pose` |
| `edge/` | Nodo Python con MediaPipe Pose Landmarker: postura, inmovilidad y caídas. Solo envía metadatos, nunca video |

Las historias HU-01..07, los requerimientos técnicos RT-01..03 y los no funcionales del informe están en `CLAUDE.md` y en la matriz de `docs/TRAZABILIDAD.md`. Las cifras de los no funcionales son objetivos: no declararlas cumplidas sin medición registrada en `validation.md`. «NuevaAPP» es un ejemplo de nombre, no una app a crear automáticamente.

1. Lee `constitution.md`, `README.md`, `CLAUDE.md`, `docs/PROYECTO.md`, `docs/ESTADO_PROYECTO.md` y `specs/README.md`.
2. Para la tarea concreta lee la spec relacionada y las secciones necesarias de `docs/ARQUITECTURA_BASE.md`, `docs/DECISIONES.md` y `docs/OBSERVACIONES_BASE.md`.
3. Inspecciona código real y cambios locales; si existe Git, consulta su estado. No sobrescribas trabajo del usuario ni dependas de memoria de conversaciones.

## Fase inicial obligatoria: DOCUMENTAR

Ante una solicitud de nuevo módulo o cambio funcional, la primera fase genera o actualiza solo Markdown:

- Primero `spec.md`: necesidad, alcance, RF, permisos, datos y aceptación.
- Después `plan.md`: propuesta técnica, archivos reales, integración, migraciones si aplican y pruebas.
- Finalmente `tasks.md`: tareas pequeñas, dependencias, RF y condiciones de finalización, todas pendientes al crearlas.
- Actualiza índice de specs, proyecto/estado, decisiones y trazabilidad cuando corresponda.
- No ejecutes `startapp`, no crees Python/HTML/JS/CSS, tests ejecutables, migraciones, dependencias ni endpoints en esta fase. No desarrolles prototipos funcionales encubiertos.
- Entrega los documentos y detente antes del código. Solo una instrucción posterior explícita de implementación permite pasar a esa fase; revisar documentos no es autorizar despliegue.
- No imponer entrevista. Si hay un vacío crítico, documenta lo definido y deja la decisión afectada pendiente; no inventes respuestas ni marques aprobado el plan.

El usuario proporciona primero nombre del módulo (ejemplo `NuevaAPP`) y requerimiento en lenguaje natural. Valida colisiones y adecuación del nombre al planificar; no cambies silenciosamente el nombre pedido. Una vista pequeña puede ampliar una app existente si se justifica en el plan.

## Prompts y tamaño del trabajo

`prompts/00-orquestador.md` permite elegir las guías documentales pertinentes sin que el usuario pegue una por una. Anuncia qué fases aplicarás. Lee solo lo necesario y respeta la fase autorizada: seleccionar un prompt no autoriza su ejecución.

Nuevo módulo o cambio transversal: carpeta con siguiente número libre `specs/NNN-nombre/`. Comprobar siempre el siguiente número libre en `specs/`. Cambio pequeño: actualizar la spec existente y añadir tareas fechadas. Conservar IDs de RF y decisiones sustituidas. No crear una segunda spec por cada ajuste de texto.

## Convenciones de esta base

- Django, vistas por clases como patrón preferido, Django Templates, Tailwind y crispy_tailwind. Mantener estilo y organización existentes.
- Apps actuales en `web/`: `homeApp`, `UsuarioApp`, `PlanesApp`, `CuidadosApp` y `theme`. Registro local en `web/core/common_settings.py:LOCAL_APPS`; rutas raíz en `web/core/urls.py`. No renombrar apps: sus labels están amarrados a las migraciones (D-011-03).
- API móvil y del nodo en `web/CuidadosApp/api/`. Un cambio de contrato API debe documentar la compatibilidad con la app y el nodo ya instalados.
- Datos clínicos: acceso por propiedad del paciente (009) hasta implementar los vínculos familiar/cuidador de D-050. Sin video a la nube; no registrar datos clínicos en logs.
- Permisos: inspeccionar `web/core/mixins.py`. `usuario_tiene_cargo` exige autenticación/actividad y **admite superusuarios**; para otros usuarios compara cargo. `PermitsPositionMixin` admite ADMIN/MANAGER por defecto mediante `permisos` (nombre existente).
- No suponer que todas las vistas internas usan ese mixin: Home y listado de usuarios usan LoginRequiredMixin. Definir matriz por acción para cada nuevo módulo, incluyendo superusuario, sin perfil, RESTRICTED y anónimo.
- Plantillas reales: `components/Layout/base.html`, `base_extendido.html`, `base_pages.html`. Usar bloques existentes; no inventar `base_extendida.html`.
- Menú compartido: `templates/components/navbar/nav.html`. Visibilidad y acceso real deben ser coherentes; no confiar solo en el menú.
- Mantener idioma es-cl y zona America/Santiago mientras el producto no acuerde otro contexto.
- No copiar reglas de módulos/clientes anteriores ni trasladar políticas de otro repositorio.

## Implementación después de autorización

Trabaja solo tareas autorizadas con sus RF. Reutiliza reglas/servicios existentes; operaciones sensibles, validación en servidor y transacciones según plan. Separa reglas de negocio de presentación cuando la complejidad lo justifique; no impongas una arquitectura adicional por rutina.

Para errores: reproducir, comparar con spec, corregir y añadir regresión pertinente. No alterar la spec para legitimar un fallo. Una limpieza extensa o actualización de dependencias necesita alcance propio.

No leas ni publiques secretos para documentar. No uses datos de producción para pruebas. No hagas despliegues, migraciones reales, commits ni push sin autorización aplicable. Revisa archivos a incluir en Git; no añadas todo a ciegas.

Git en una implementación autorizada (D-059): rama `feature/NNN-nombre` desde `develop`, un commit por tarea y PR hacia `develop`. Nunca push directo a `main`. Hacer merge del PR, desplegar o migrar una DB real requiere autorización explícita aparte.

## Comandos y límites comprobados

Consulta `docs/ENTORNO_Y_VERIFICACION.md` antes de ejecutar. En Windows, los venv `.venv-edge/` y `.venv-mobile/` del repositorio son de macOS (`bin/`) y no sirven: web usa `.venv` en la raíz y edge usa `.venv-edge-win` (D-011-03).

Web, desde `web/`:

```bash
../.venv/Scripts/python.exe -m pip install --require-hashes -r requirements.txt
../.venv/Scripts/python.exe manage.py check --settings=core.test_settings
../.venv/Scripts/python.exe manage.py makemigrations --check --dry-run --settings=core.test_settings
../.venv/Scripts/python.exe manage.py test UsuarioApp homeApp PlanesApp CuidadosApp --settings=core.test_settings
```

Usar siempre `--settings=core.test_settings`; no validar contra la base de desarrollo.

Edge, desde la raíz y con su propio entorno (`edge/requirements.txt`): `python -m unittest edge.test_posture edge.test_fall edge.test_run`. Con MediaPipe instalado, `python -m edge.smoke` comprueba el modelo.

Mobile, desde `mobile/`: `flutter analyze` y `flutter test`. Lo que dependa del dispositivo (notificaciones, cámara, APK instalado) se comprueba en un Android físico y se registra aparte.

Los archivos de dependencias están en UTF-8. Si una herramienta falla al leerlos, registrar el problema y proponer un cambio mínimo.

Tailwind 4 usa el binario standalone, sin Node.js. Si cambian estilos, clases o fuentes, ejecutar `manage.py tailwind build` desde `web/`. Las fuentes se declaran con `@source` en `web/theme/static_src/src/styles.css`; registrar las de cada app nueva y comprobar inclusión/exclusión.

## Validación y cierre

Probar comportamiento y errores relevantes, permisos permitidos/denegados y regresiones de la base, en cada componente tocado. UI interactiva requiere navegador; documentos PDF requieren inspección visual cuando existan y se modifiquen. No agregar tests triviales que solo repitan la implementación.

Documentación: enlaces válidos, requisitos consistentes, estados honestos. Registrar comandos/resultados, lo no comprobado, tareas y siguiente paso en el estado. Responder en español con cambios, evidencia y pendientes. Una tarea terminada técnicamente no significa aceptación funcional del propietario.
