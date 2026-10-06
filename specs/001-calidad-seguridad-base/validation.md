# Validación — 001 / CalidadBase

Fecha: 2026-09-20. Estado: verificado técnicamente; aceptación funcional del propietario pendiente.

## Resultado

Se implementaron T-001-01 a T-001-10 sin migrar datos reales, desplegar, hacer commit o push. Se preservaron requirements.txt en UTF-8, media/ en .gitignore, ACCOUNT_ADAPTER (ahora en la configuración común), ausencia de ACCOUNT_ALLOW_REGISTRATION, opcionales desactivados, correo inicial y gráfico demostrativo. `.gitignore` también excluye el runtime temporal de validación para evitar que una recreación accidental llegue a Git.

## Evidencia automatizada

El `.venv` existente no pudo ejecutarse porque apunta a `C:\Users\Fernando\AppData\Local\Programs\Python\Python312\python.exe`, que no existe. Para validar se usó el Python empaquetado del workspace y se instalaron exactamente las versiones de requirements.txt en `.codex-test-runtime`; esa carpeta se eliminó después.

| Comprobación | Resultado |
|---|---|
| `manage.py check --settings=core.test_settings` | OK: 0 problemas |
| `manage.py makemigrations --check --dry-run --settings=core.test_settings` | OK: no changes detected; no creó migraciones |
| `manage.py test UsuarioApp homeApp --settings=core.test_settings -v 2` | OK: 15 pruebas en 1.686 s |
| `npm ci` en theme/static_src | OK: 125 paquetes; audit informó 9 vulnerabilidades (1 baja, 1 moderada, 7 altas) |
| `npm run build` final | OK: Tailwind terminó en 403 ms; avisó caniuse-lite desactualizado |

La suite cubrió aislamiento de DB/correo/hashers/media/HTTP; adapter y GET/POST público cerrado; acceso interno anónimo, RESTRICTED, sin perfil, sin cargo, staff, inactivo, ADMIN, MANAGER y superusuario; altas válidas; username duplicado, correo inválido, contraseñas discordantes/débiles, cargos inválidos y archivo mayor a 5 MiB; HTML del enlace y regresión del gráfico.

## Evidencia Tailwind

Se crearon testigos temporales con `z-[123]` solo en JavaScript propio, `tracking-[0.123em]` solo en Python propio y `rotate-[13deg]` bajo una migración excluida. El build incluyó los dos primeros y no el tercero. Se retiraron los tres archivos y se ejecutó un build final limpio. El CSS resultante es `theme/static/css/dist/styles.css`.

Tailwind no garantiza clases concatenadas. Los módulos futuros deben escribir nombres completos, usar mapas de valores completos o una safelist finita y registrar sus nuevas raíces en la configuración.

## Navegador

Se creó una base SQLite temporal separada y un superusuario ficticio sin Profile. En navegador integrado:

- el inicio cargó estilos y mantuvo «Grafico Ejemplo»;
- el superusuario vio Registro en escritorio y abrió `/registro/` con formulario estilizado;
- a 390 × 844, el menú móvil abrió y mostró Registro;
- los estáticos devolvieron HTTP 200 en la segunda ejecución con `runserver --insecure` local.

La DB, settings auxiliares, usuario ficticio, pestañas y servidor temporales se eliminaron al terminar. La ausencia del enlace para actores denegados quedó validada por la suite de integración HTML; no se reutilizaron datos reales en navegador.

## Límites y pendientes

- Las 9 vulnerabilidades informadas por npm corresponden al árbol declarado existente. No se ejecutó `npm audit fix` porque actualizar dependencias requiere alcance y validación propios.
- El aviso de caniuse-lite desactualizado no impidió compilar; actualizarlo también debe planificarse por separado.
- Reparar/recrear el `.venv` local queda pendiente de entorno. No afecta la evidencia ejecutada con las mismas versiones declaradas.
- No se probó SMTP, axes ni preventconcurrentlogins porque permanecen desactivados por decisión aprobada.
- La aceptación funcional final corresponde al propietario y no se infiere de una suite verde.

## Ajuste del 2026-09-22

Alcance autorizado: revisar los nuevos documentos, hacer reproducible la migración ya iniciada a Tailwind 4 standalone y detallar las pruebas asociadas por RF. No se modificaron permisos, datos, modelos, rutas ni reglas de negocio.

| Comprobación | Resultado real |
|---|---|
| Instalación aislada desde `requirements.txt` | OK: django-tailwind 4.5.0 y pytailwindcss 0.3.0 instalados. `pip` avisó un conflicto con `cryptography` del runtime anfitrión, paquete ajeno a este requirements; los comandos del proyecto se ejecutaron desde el destino aislado |
| `check --settings=core.test_settings` | OK: sin problemas |
| `makemigrations --check --dry-run --settings=core.test_settings` | OK: sin cambios detectados |
| `test UsuarioApp homeApp --settings=core.test_settings -v 1` | OK: 15 pruebas en 1.754 s |
| `tailwind --settings=core.test_settings build` | OK: Tailwind 4.3.0 standalone; build final en 70 ms |
| Testigos temporales | JavaScript `z-[117px]` y Python `tracking-[0.117em]` incluidos; `rotate-[17deg]` bajo migraciones excluido |
| Limpieza | Testigos retirados y CSS final recompilado; ninguna cadena testigo quedó en el generado |

`tailwind.config.js` no se restauró. Tailwind 4 no detecta automáticamente la configuración JavaScript heredada; esta base usa configuración CSS-first en `theme/static_src/src/styles.css`. El modo standalone evita Node.js, pero no permite asumir disponibilidad de plugins npm de terceros.

Las vulnerabilidades y el aviso de caniuse-lite anotados en la validación histórica del 2026-09-20 correspondían al árbol npm eliminado; ya no son pendientes del flujo standalone actual.

La trazabilidad ahora cuenta métodos automatizados asociados por RF. Los conteos son asociaciones: un método puede respaldar más de un RF y los subtests no se inflan como casos independientes. La aceptación funcional final continúa pendiente del propietario.
