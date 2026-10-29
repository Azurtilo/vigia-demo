# Plan técnico — 018 / Usabilidad del portal

Spec: [spec.md](spec.md). Estado: aprobado para implementar T-018-01..07.
Autorización de implementación: «fusiona la 13, autorizo para que luego hagas los cambios en el codigo» (2026-10-27). Las decisiones P-018-01..03 no se eligieron expresamente: se aplican las opciones recomendadas en la spec (D-078..D-080), reversibles si el propietario elige otra.

## Inspección de la base

Leídos el 2026-10-27 sobre `develop` (`73fb6a1`):

- **Formularios con contraseña nueva.**
  - Registro: `UsuarioApp.signup_forms.PublicSignupForm` (hereda de `allauth.account.forms.SignupForm`; `password1`, `password2`).
  - Cambiar, crear y restablecer desde el correo: formularios de allauth 65.19.7 (`ChangePasswordForm`, `SetPasswordForm`, `ResetPasswordKeyForm`), sin sobrescribir en `ACCOUNT_FORMS` ([common_settings.py:131](../../web/core/common_settings.py#L131)). `SetPasswordField` de allauth pone como ayuda la lista HTML de Django, que en es-CL trata de «usted» («Su contraseña no puede…»).
  - Administración: `UsuarioApp.forms.UserCreateForm` (`password1`, `password2`; su error de coincidencia dice «Passwords do not match») y `AdministrativePasswordForm` (`new_password1`, `new_password2`).
  - Validadores: los 4 de Django, con `MinimumLengthValidator` en 8 por omisión ([common_settings.py:101](../../web/core/common_settings.py#L101)). Sus códigos de error: `password_too_short`, `password_entirely_numeric`, `password_too_similar`, `password_too_common`.
- **Plantillas.** Las páginas de cuenta extienden [base_simple.html](../../web/templates/account/Layout/base_simple.html) (sin menú) o [base_account.html](../../web/templates/account/Layout/base_account.html) (con menú). `email.html` y `logout.html` usan la primera; `logout.html` tiene un comentario «NO USADA», pero sí se muestra en `GET /accounts/logout/`.
- **Estilos.** [static/css/styles.css](../../web/static/css/styles.css) se carga en todas las páginas; `CuidadosApp/care.css` solo con sesión. No hay reglas para `.privacy-policy`. Tailwind 4 compila aparte (`theme/static_src`).
- **JavaScript.** Scripts propios con `defer` en [base.html](../../web/templates/components/Layout/base.html); `mensajes.js` expone `window.createToast`. No hay CSP. No hay JavaScript que proteja el doble envío.
- **Redirecciones.** Las vistas siguen POST → redirección → GET. Vuelven a la misma página: correos de la cuenta (allauth), `AccessView`, `RevokeAccessView`, revocar invitación, `ConsentView`, `RevokeConsentView`, `ArchiveView` y reactivar (todas a la ficha), `MethodsView` y `DefaultMethodView` (métodos), `ProfileUpdateView` (perfil). Van a otra página: `DailyEventView` (agenda), `CorrectionView` (historial), formularios de `CuidadosApp` en [form.html](../../web/templates/pages/CuidadosApp/form.html) (ficha), `LeaveView` (pacientes), `UserCreateView` (vuelve a registrar). `VisualModeUpdateView` siempre va a `Home` ([UsuarioApp/views.py:79](../../web/UsuarioApp/views.py#L79)).
- **Textos.** El catálogo en español de allauth trata de «usted» en mensajes como «Ha confirmado…», «Ha iniciado sesión…», «No puede eliminar su correo principal…» y en la ayuda «¿Ha olvidado su contraseña?» del formulario de inicio de sesión. No hay `msgfmt` en el equipo, así que no se puede compilar un catálogo propio sin agregar herramientas.

## Diseño propuesto

### Indicadores de contraseña (RF-018-01..04, D-078, D-079)

**`UsuarioApp/password_rules.py` (nuevo).** Python puro:

- `rules()` recorre `AUTH_PASSWORD_VALIDATORS` y devuelve las reglas a mostrar, cada una con `code`, texto en tuteo y modo de evaluación en el navegador:

  | Validador | Texto | En el navegador |
  |---|---|---|
  | `MinimumLengthValidator` | «Al menos N caracteres» (N leído del validador) | exacto |
  | `NumericPasswordValidator` | «No usar solo números» | exacto |
  | `UserAttributeSimilarityValidator` | «Que no se parezca a tu usuario ni a tu correo» | aproximado (D-078): rojo si contiene el usuario o la parte del correo antes de la @ (desde 3 caracteres); si no, neutro «se revisa al guardar» |
  | `CommonPasswordValidator` | «Que no sea una contraseña común» | neutro «se revisa al guardar» (D-079) |
  | Otro validador | su `get_help_text()` | neutro |

- `PasswordRulesMixin` para formularios: declara `password_field` y `confirm_field`, vacía la ayuda de esos campos (desaparece la lista de Django en «usted») y expone `password_checklist`: las reglas, los ids de los campos, los valores personales con que comparar y los códigos que el servidor rechazó (de `self.errors.as_data()`, RF-018-04).

**Formularios.** El mixin se aplica a `PublicSignupForm`, a tres formularios nuevos en `UsuarioApp/account_forms.py` que heredan de los de allauth (registrados en `ACCOUNT_FORMS` como `change_password`, `set_password` y `reset_password_from_key`), y a `UserCreateForm` y `AdministrativePasswordForm`. Valores personales: los campos `username` y `email` del formulario cuando existen (registro y alta administrativa), o el usuario del formulario (cambiar, crear, restablecer y restablecimiento administrativo).

**`components/password_checklist.html` (nuevo).** Lista `<ul data-password-checklist>` con una fila por regla y la de coincidencia, estado inicial `pending` (o `fail` para las rechazadas por el servidor), icono y texto oculto para lectores de pantalla, y una región `aria-live="polite"`. Sin JavaScript es la ayuda estática, ya en tuteo. Se incluye en las seis plantillas después del formulario renderizado por crispy; el script la mueve justo debajo del campo de contraseña.

**`static/js/contrasena.js` (nuevo).** Evalúa en cada `input`: largo, solo números, contención del usuario o correo y coincidencia. Nunca envía ni guarda la contraseña. Cambia `data-state` (`pending`, `pass`, `fail`) y actualiza el resumen anunciado («Cumples 2 de 4 requisitos»).

**Estilos** en `styles.css`: verde y tachado para `pass`, rojo para `fail`, gris para `pending`, con los tokens de color de `tokens.css` para que funcione en modo claro y oscuro.

### Política de privacidad (RF-018-05..07)

- [politica.html](../../web/templates/pages/PrivacidadApp/politica.html): ids en cada `h2`, un índice `<nav aria-label="Secciones">`, el aviso de borrador en un recuadro y salidas según la sesión (anónimo: «Crear cuenta» e «Iniciar sesión»; con sesión: «Volver a mi panel»). El texto no cambia.
- Estilos `.privacy-policy` en `styles.css` (que se carga sin sesión): ancho de lectura de unos 70 caracteres, jerarquía de títulos, separación, viñetas y el recuadro del aviso.

### Páginas sin salida (RF-018-08..10)

- `email.html` pasa a `base_account.html`. `logout.html` elige la base según la sesión (`{% extends %}` con variable) y agrega «Cancelar».
- Salidas de la tabla de RF-018-09 en `verification_sent.html`, `email_confirm.html`, `verified_email_required.html`, `password_reset_done.html`, `password_reset_from_key.html` (enlace inválido), `password_reset_from_key_done.html` y `account_inactive.html`, con los botones existentes (`button`, `button secondary`).
- `base_simple.html`: el logo lleva a `Home` con sesión y a `account_login` sin ella.

### Historial del navegador (RF-018-11..13, D-080)

**`core/navigation.py` (nuevo): `ReplaceNavigationMiddleware`.** Si la petición es POST con la cabecera `X-Vigia-Navigation: replace` y la respuesta es una redirección (301, 302, 303 o 307) a un destino interno (`url_has_allowed_host_and_scheme` con el host de la petición), la cambia por `200` JSON `{"location": "<destino>"}` con `Cache-Control: no-store`. Cualquier otra respuesta (formulario con errores, 403 de CSRF, redirección externa) pasa intacta. Va justo después de `SecurityMiddleware`, para ver la respuesta final, incluida la del consentimiento (`ConsentRequiredMiddleware`).

**`static/js/historial.js` (nuevo).** Para cada `form[data-replace-history]`:

1. Intercepta `submit` (respeta `preventDefault` previo, como el `confirm()` de eliminar correo).
2. Arma `FormData` con el botón que envió (`event.submitter`: nombre y valor, como en «Hacer primario»), desactiva ese botón y hace `fetch` con la cabecera.
3. Si recibe `{"location"}`, llama a `location.replace(location)`: la entrada del formulario se sustituye por el destino, y los mensajes de Django, aún en la sesión, salen una sola vez en esa carga.
4. Si recibe HTML (errores), lo muestra en el documento con `history.replaceState` a la URL de la respuesta.
5. Si falla la red, reactiva el botón y muestra un aviso con `createToast`. No reintenta el envío por su cuenta.

Sin JavaScript, o si el navegador no tiene `fetch`, el formulario se envía como hoy.

**Formularios marcados** con `data-replace-history`: los de `email.html`, `access.html` (invitar, revocar acceso, revocar invitación, salir), `consents.html` (registrar y revocar; no la exportación, que descarga un archivo), archivar y reactivar en `patient.html`, `metodos.html` (agregar y predeterminado), el de datos en `perfil.html` (no la exportación), `CuidadosApp/form.html` (actividad, corrección y formularios de paciente, medicamento, cuidado, postura y reloj), `registro_usuario.html` y `visual_mode.html`.

**Modo visual (RF-018-13).** `visual_mode.html` agrega `next` con `request.get_full_path`. `VisualModeUpdateView` redirige a `next` si `url_has_allowed_host_and_scheme` lo acepta, y si no, a `Home`.

### Textos (RF-018-14, RF-018-15)

- Plantillas: textos literales en español tuteado donde hoy hay `{% trans %}` con msgid en inglés sin traducción o traducción en «usted»: `email.html`, `password_reset*.html`, `password_change.html`, `password_set.html`, `verification_sent.html`, `email_confirm.html`, `verified_email_required.html`, `logout.html`, `account_inactive.html`, y las de UsuarioApp con «usted».
- Mensajes de allauth: se sobrescriben las plantillas `templates/account/messages/*.txt` que el portal usa, con texto tuteado (por ejemplo, «Correo principal actualizado.»). Es el mecanismo que allauth ofrece y no necesita compilar catálogos.
- Inicio de sesión: un `LoginForm` propio (`ACCOUNT_FORMS["login"]`) quita la ayuda «¿Ha olvidado su contraseña?» del campo, porque la plantilla ya muestra «¿Olvidaste tu contraseña?».
- `UserCreateForm`: el error de coincidencia pasa a «Las contraseñas no coinciden.»
- 2FA y cuentas de Google: se revisan renderizadas; solo se cambia lo que salga en inglés o en «usted».

## Archivos previstos

| Archivo | Cambio |
|---|---|
| `web/UsuarioApp/password_rules.py` | Nuevo: reglas y `PasswordRulesMixin` |
| `web/UsuarioApp/account_forms.py` | Nuevo: formularios de allauth con el mixin y `LoginForm` sin ayuda duplicada |
| `web/UsuarioApp/signup_forms.py`, `web/UsuarioApp/forms.py` | Mixin en registro y en los dos formularios administrativos; texto de coincidencia |
| `web/UsuarioApp/views.py` | `next` validado en el modo visual |
| `web/core/common_settings.py` | `ACCOUNT_FORMS` y el middleware |
| `web/core/navigation.py` | Nuevo: middleware |
| `web/templates/components/password_checklist.html` | Nuevo |
| `web/templates/account/*.html`, `account/Layout/base_simple.html`, `account/messages/*.txt` | Salidas, menú, logo y textos |
| `web/templates/pages/PrivacidadApp/politica.html` | Índice, salidas y estructura |
| Plantillas con formularios marcados | `data-replace-history` |
| `web/static/js/contrasena.js`, `web/static/js/historial.js` | Nuevos |
| `web/static/css/styles.css` | Política e indicadores |
| `web/templates/components/Layout/base.html` | Carga de los dos scripts |
| `web/UsuarioApp/tests.py`, `web/PrivacidadApp/tests.py`, `web/core` (pruebas del middleware) | Pruebas |

Sin migraciones, dependencias, cambios de API ni de la app móvil.

## Pruebas

- **Reglas y mixin:** las reglas se derivan de los validadores (largo leído de la configuración); la ayuda de Django desaparece; un POST con contraseña corta, numérica, común o parecida marca la regla correspondiente como rechazada; los seis formularios exponen la lista; la contraseña no aparece en el HTML.
- **Middleware:** con la cabecera y redirección interna, JSON con `location`; sin cabecera, 302 intacto; redirección externa intacta; GET intacto; formulario con errores (200 HTML) intacto; los mensajes siguen en la sesión hasta el GET.
- **Modo visual:** `next` interno se respeta; `next` externo, `//evil.example` o vacío vuelven a `Home`.
- **Plantillas:** la política tiene índice y salidas según la sesión; las páginas de cuenta tienen sus salidas y el menú donde corresponde; el logo cambia según la sesión; los formularios marcados llevan `data-replace-history` y los de exportación no.
- **Textos:** una prueba renderiza las páginas de cuenta (con y sin sesión) y falla si encuentra frases en inglés de una lista o fórmulas de «usted» («Por favor», «su contraseña», «Ha …», «desea»).
- **Regresión:** las suites completas de Django, más `check`, `makemigrations --check` y `tailwind build`.
- **Navegador:** el JavaScript no tiene pruebas automáticas en el repo (sin Node). Se verifica a mano en el navegador del teléfono contra la demo por wifi, y se registra en `validation.md` lo que se haya podido comprobar.

## Riesgos

- `document.write` en la ruta de errores de `historial.js` vuelve a ejecutar los scripts de la página. Es la ruta poco frecuente; si da problemas, se cambia a recargar con un envío nativo solo en esa ruta.
- allauth puede cambiar sus plantillas de mensajes en una versión futura; las sobrescritas quedan listadas en el plan para revisarlas al actualizar (spec 005).
- La regla aproximada de parecido (D-078) puede quedar neutra y aun así fallar en el servidor. Está previsto en RF-018-04.
