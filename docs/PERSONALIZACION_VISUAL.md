# Personalizar la identidad visual

Implementación de las specs [002](../specs/002-renovacion-visual/spec.md) y [003](../specs/003-modo-visual-usuario/spec.md). La base conserva Django Templates, crispy_tailwind, Tailwind 4 standalone, Alpine y ECharts existentes.

## Cambiar el color de una plataforma

Edita únicamente [static/css/tokens.css](../web/static/css/tokens.css). En `:root`, cambia el par `--brand-light`/`--brand-dark` y sus textos `--on-brand-light`/`--on-brand-dark`. `--brand` y `--on-brand` se resuelven según el modo de la cuenta. La paleta inicial usa petróleo; ciruela y cobre también se comprobaron en ambos modos.

| Identidad | --brand-light | --brand-dark | Texto claro / oscuro |
|---|---|---|---|
| Petróleo | #0f766e | #5eead4 | #ffffff / #102124 |
| Ciruela | #7e22ce | #c084fc | #ffffff / #102124 |
| Cobre | #9a3412 | #fdba74 | #ffffff / #102124 |

Ejemplo para ciruela:

```css
:root {
  --brand-light: #7e22ce;
  --brand-dark: #c084fc;
  --on-brand-light: #ffffff;
  --on-brand-dark: #102124;
}
```

Modificar valores no requiere compilar Tailwind. Guarda y recarga; usa recarga forzada si se conservan recursos antiguos. El gráfico lee colores al cargar. El botón de Inicio guarda la elección personal de luminosidad; cambiar la marca en tokens afecta a toda la plataforma.

El hover, selección tenue, foco y primera serie del gráfico derivan de `--brand`. El hover oscuro aclara el acento para conservar contraste con texto oscuro; la selección tenue mezcla marca con la superficie de su modo. No copies hexadecimales a componentes. Comprueba ambos textos de marca y sus usos al personalizar; auditoría reproducible en [verificar_contraste.py](../specs/003-modo-visual-usuario/verificar_contraste.py).

## Contrato de tokens

| Familia | Variables | Responsabilidad |
|---|---|---|
| Marca | --brand-light, --brand-dark, --on-brand-light, --on-brand-dark; --brand, --on-brand, --brand-hover, --brand-soft, --focus | Par configurable y valores resueltos para acciones, enlaces y foco |
| Superficies | --page, --surface, --surface-muted | Fondo, contenido y fondos secundarios |
| QR | --qr-surface | Blanco en ambos modos para mantener legible el SVG negro de MFA; no invertir imágenes |
| Texto | --ink, --muted | Texto principal y ayuda |
| Bordes | --border, --control-border | Separaciones decorativas y límites de controles |
| Estados | --success, --danger, --warning, --info y variantes -soft; --on-danger, --danger-hover | Significado de mensajes y acciones sensibles; independiente del color de marca |
| Gráfico | --chart-1, --chart-2, --chart-3 | Series diferenciadas; chart-1 sigue la marca |
| Presentación | --overlay, --shadow, --font-ui | Fondo modal, elementos flotantes y familia del sistema |
| Movimiento | --motion-fast, --motion-panel | Duraciones en milisegundos; mantener la unidad ms para cierre JS |

Los botones peligrosos usan `--on-danger`, para que cambiar el texto de marca no altere su contraste. Éxito/error/aviso usan texto además de color. Para otra paleta comprueba texto normal ≥ 4,5:1, texto grande ≥ 3:1, límites de controles/foco ≥ 3:1 y navegación activa sobre marca tenue. No es suficiente revisar solo el botón principal.

El [CSS fuente Tailwind](../web/theme/static_src/src/styles.css) enlaza variables semánticas con `@theme inline`. Utilidades como `bg-brand`, `text-ink`, `text-muted`, `bg-surface`, `border-line` y `bg-danger-soft` se resuelven desde estos tokens. No concatenes `bg-` con un color; utiliza clases completas detectables por el compilador.

## Reutilizar componentes

- Estructura privada: extender `components/Layout/base_extendido.html` y completar `content_main`. Formulario privado: `components/Layout/base_pages.html` y `content_pages`. Cuenta interna: `account/Layout/base_account.html` y `content_account`; pública: `account/Layout/base_simple.html`.
- Encabezado: `.page-heading` con un h1, una explicación breve y la acción pertinente. Contenido: `.panel`; no es necesario envolver cada texto en una tarjeta.
- Botón de formulario: `components/btn/button.html`, ancho completo. Botón acotado: `button_size.html`. Enlace de acción: `ancor_btn.html`. Parámetros existentes conservados: `button_text`, `button_name`, `button_type`, `button_class` y `ancor_link`; el botón completo también admite `button_id`. Variantes: `secondary` y `danger`.
- Los formularios dentro de `.form-panel` aplican la presentación común a crispy y allauth. Conserva etiquetas, errores, CSRF y contratos del servidor; no escondas mensajes de validación por conseguir una captura más limpia.
- Estados compactos: `.badge` y variantes `success`, `warning`, `danger`, `brand`. Añade siempre una descripción del estado.
- Diálogo: `dialog.dialog`, un título asociado con `aria-labelledby`, un disparador `data-open-dialog="id"` y botón `data-close-dialog`. El JavaScript compartido gestiona apertura, Escape, Tab, scroll y retorno de foco. El componente `components/modal/modal.html` conserva `modal_id`, `modal_title` y `modal_body_id`; `abrir_modal` mantiene parámetros existentes y sanitiza HTML con DOMPurify.
- Notificaciones: el layout base incluye `components/mensajes.html` una sola vez. Puedes llamar `success(texto)`, `error(texto)`, `warning(texto)` o `info(texto)`. El texto se trata como texto, no HTML. Errores/advertencias permanecen hasta cerrarlos; éxito/información duran ocho segundos y se pausan al pasar el puntero o dar foco.
- El menú sigue definido en `components/navbar/nav.html`, usado en escritorio/móvil. Los permisos de gestión vienen de `puede_registrar_usuarios`/`puede_gestionar_usuarios`, que comparten el helper del servidor. Ocultar un botón no sustituye autorización en su vista.

## Compilar y verificar

En un entorno local preparado, después de cambiar clases o fuentes:

```text
python manage.py tailwind --settings=core.test_settings build
python manage.py check --settings=core.test_settings
python manage.py makemigrations --check --dry-run --settings=core.test_settings
python manage.py test UsuarioApp homeApp --settings=core.test_settings
```

El argumento `--settings` de tailwind va antes de `build`. El CSS generado es [theme/static/css/dist/styles.css](../web/theme/static/css/dist/styles.css); no editarlo manualmente. Las fuentes propias se registran con `@source`; conservar exclusiones de migraciones, cachés, dependencias y generados. No hace falta Node.js para compilar la base.

Cuando cambies recursos estáticos, actualiza su versión de caché en el layout o usa archivos versionados. Tokens y styles usan `?v=003`; scripts sin cambios conservan `?v=002`. Estas versiones no son selectores de colores.

Revisa login, Inicio, Usuarios, Registro, Perfil, Cuenta/MFA y errores; datos válidos/inválidos; teclado, Escape, móvil y mensajes largos. Prueba la marca con fondo real, también en el gráfico, y conserva la semántica de estados. El movimiento reducido está contemplado en CSS y JS; su evidencia y las limitaciones de herramientas se registran en [validation.md](../specs/002-renovacion-visual/validation.md).

## Modo claro/oscuro por cuenta

Actualización 008: Inicio y Mi suscripción reutilizan [visual_mode.html](../web/templates/components/visual_mode.html) con idénticos SVG sol/luna, labels/clases y POST/CSRF; el retorno a Home conserva su redirección de clientes. Index ahora muestra agregados de PlanesApp y gráfico de planes con cantidades HTML accesibles. [Validación 008](../specs/008-dashboard-navegacion/validation.md): 127 tests y navegador; colores siguen en tokens.css. El menú compartido incorpora SVG y oculta Inicio según el helper; sidebar desplazable y details/noscript móvil mantienen acceso a enlaces cuando no hay scripts.

Inicio muestra luna para activar oscuro y sol para activar claro, junto al estado actual. Un formulario POST con CSRF guarda solo la cuenta activa de la sesión y vuelve a Inicio; funciona sin ejecución de scripts. Todos los cargos, staff, superusuario y usuarios sin perfil pueden cambiar su propia elección. No modifica cargos, perfiles ni fotos.

`UserVisualPreference` guarda light/dark con relación única y restricción de base. Sin fila, claro; las visitas no crean filas. El processor `preferencias_visuales` entrega el modo al HTML antes del CSS. Anónimos y preautenticación usan claro; logout conserva la elección de cuenta. No se guarda en cookies/localStorage ni se sigue el modo del sistema.

La migración [0002](../web/UsuarioApp/migrations/0002_user_visual_preference.py) fue creada y probada/revertida solo en SQLite efímero. **No está aplicada a la base existente**: antes de usar la función allí, acordar entorno y respaldo y autorizar esa aplicación por separado. Revertir elimina elecciones, conserva usuarios/perfiles y requiere coordinar la versión de código. [Validación y límites](../specs/003-modo-visual-usuario/validation.md): 43 tests Django, 180 pares de contraste y navegador; aceptación y revisión visual restante pendientes.

## Recuperación de esta copia

La carpeta no tenía Git al comenzar. El punto de recuperación es `.recovery-002/antes-implementacion.zip`, acompañado de `sha256-antes.txt`. Contiene los archivos de código/documentación seleccionados antes del cambio, sin .env, bases ni media personal. Recupera solo los archivos que corresponda revisar, para no sobreescribir trabajo posterior; recompila CSS si reviertes clases. No se hicieron migraciones sobre datos reales.
