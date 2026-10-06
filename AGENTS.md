# Instrucciones para agentes — base Django reutilizable

## Contexto y lectura inicial

Es una base existente; no reconstruir autenticación, usuarios, tema ni navegación. No contiene todavía un módulo de negocio definido. «NuevaAPP» es un ejemplo, no una app a crear automáticamente.

1. Lee `constitution.md`, `README.md`, `docs/PROYECTO.md`, `docs/ESTADO_PROYECTO.md` y `specs/README.md`.
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

Nuevo módulo o cambio transversal: carpeta con siguiente número libre `specs/NNN-nombre/`. Primer número disponible: 001, comprobarlo siempre. Cambio pequeño: actualizar la spec existente y añadir tareas fechadas. Conservar IDs de RF y decisiones sustituidas. No crear una segunda spec por cada ajuste de texto.

## Convenciones de esta base

- Django, vistas por clases como patrón preferido, Django Templates, Tailwind y crispy_tailwind. Mantener estilo y organización existentes.
- Apps actuales: `homeApp`, `UsuarioApp` y `theme`. Registro local en `core/settings.py:LOCAL_APPS`; rutas raíz en `core/urls.py`.
- Permisos: inspeccionar `core/mixins.py`. `usuario_tiene_cargo` exige autenticación/actividad y **admite superusuarios**; para otros usuarios compara cargo. `PermitsPositionMixin` admite ADMIN/MANAGER por defecto mediante `permisos` (nombre existente).
- No suponer que todas las vistas internas usan ese mixin: Home y listado de usuarios usan LoginRequiredMixin. Definir matriz por acción para cada nuevo módulo, incluyendo superusuario, sin perfil, RESTRICTED y anónimo.
- Plantillas reales: `components/Layout/base.html`, `base_extendido.html`, `base_pages.html`. Usar bloques existentes; no inventar `base_extendida.html`.
- Menú compartido: `templates/components/navbar/nav.html`. Visibilidad y acceso real deben ser coherentes; no confiar solo en el menú.
- Mantener idioma es-cl y zona America/Santiago mientras el producto no acuerde otro contexto.
- No copiar reglas de módulos/clientes anteriores ni trasladar políticas de otro repositorio.

## Implementación después de autorización

Trabaja solo tareas autorizadas con sus RF. Reutiliza reglas/servicios existentes; operaciones sensibles, validación en servidor y transacciones según plan. Separa reglas de negocio de presentación cuando la complejidad lo justifique; no impongas una arquitectura adicional por rutina.

Para errores: reproducir, comparar con spec, corregir y añadir regresión pertinente. No alterar la spec para legitimar un fallo. Una limpieza extensa o actualización de dependencias necesita alcance propio.

No leas ni publiques secretos para documentar. No uses datos de producción para pruebas. No hagas despliegues, migraciones reales, commits ni push sin autorización aplicable. Revisa archivos a incluir en Git; no añadas todo a ciegas.

## Comandos y límites comprobados

Consulta `docs/ENTORNO_Y_VERIFICACION.md` antes de ejecutar. Comandos existentes, desde entorno local de desarrollo configurado:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test UsuarioApp homeApp
```

Esta base tiene `core/test_settings.py` y pruebas funcionales iniciales en UsuarioApp/homeApp. Ejecutarlas explícitamente con `--settings=core.test_settings`; no usar la base de desarrollo para validarlas ni asumir que cubren módulos futuros.

Dependencias: `python -m pip install -r requirements.txt` en entorno virtual. El archivo recibido está en UTF-8. Si una herramienta falla al leerlo, registrar el problema y proponer un cambio mínimo.

Tailwind 4 usa el binario standalone, sin Node.js. Si cambian estilos, clases o fuentes, ejecutar `python manage.py tailwind build`. Las fuentes se declaran con `@source` en `theme/static_src/src/styles.css`; registrar las de cada app nueva y comprobar inclusión/exclusión.

## Validación y cierre

Probar comportamiento y errores relevantes, permisos permitidos/denegados y regresiones de la base. UI interactiva requiere navegador; documentos PDF requieren inspección visual cuando existan y se modifiquen. No agregar tests triviales que solo repitan la implementación.

Documentación: enlaces válidos, requisitos consistentes, estados honestos. Registrar comandos/resultados, lo no comprobado, tareas y siguiente paso en el estado. Responder en español con cambios, evidencia y pendientes. Una tarea terminada técnicamente no significa aceptación funcional del propietario.
