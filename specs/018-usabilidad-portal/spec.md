# 018 — Usabilidad del portal: contraseñas, política de privacidad, páginas sin salida e historial del navegador

Estado: aprobada para implementar T-018-01..07. Fecha: 2026-10-27.
Módulo: portal web (`web/templates`, `web/static`, vistas de `UsuarioApp`, `CuidadosApp`, `PlanesApp` y `PrivacidadApp`, plantillas de allauth). No toca la API, la app móvil ni el nodo. Fuente: prueba del propietario en el teléfono por wifi el 2026-10-27, con cuatro observaciones: (1) los requisitos de la contraseña no indican si se cumplen, (2) la política de privacidad se ve como un solo bloque de texto, (3) al verificar el correo no hay forma de volver a los planes, (4) tras un mensaje como «Dirección principal de correo electrónico establecida», «atrás» repite la página tantas veces como se mostró el mensaje. Después pidió revisar si había más casos del mismo tipo; los hallazgos de esa revisión están incluidos aquí.
Implementación autorizada: SÍ, «fusiona la 13, autorizo para que luego hagas los cambios en el codigo» (2026-10-27), sin despliegue. Decisiones: P-018-01..03 no se eligieron expresamente; se aplican las recomendadas (D-078..D-080), reversibles. Plan y tareas: [plan.md](plan.md), [tasks.md](tasks.md).

## Problema y resultado

La revisión del 2026-10-27 (renderizado de 21 páginas en una base de pruebas desechable y lectura de todas las redirecciones de las vistas) confirmó las cuatro observaciones y encontró que ninguna es aislada:

1. **Contraseñas.** Hay seis pantallas donde se elige una contraseña nueva y todas muestran las reglas como una lista fija de Django, sin indicar cuáles se cumplen: crear cuenta, cambiar contraseña, crear contraseña (cuenta de Google), restablecer desde el correo, y las dos del administrador (crear usuario y restablecer la contraseña de un usuario). Ninguna avisa si la confirmación coincide.
2. **Política de privacidad.** [politica.html](../../web/templates/pages/PrivacidadApp/politica.html) tiene títulos y listas, pero no existe ninguna regla CSS para `.privacy-policy`, y el reinicio de estilos de Tailwind deja títulos, párrafos y viñetas con el mismo aspecto. Pasa con o sin sesión. «Volver» lleva a iniciar sesión aunque se haya llegado desde «Crear cuenta».
3. **Páginas sin salida.** Las páginas de cuenta usan [base_simple.html](../../web/templates/account/Layout/base_simple.html), sin barra de navegación; la única salida es el logo, que lleva a iniciar sesión incluso con la sesión iniciada. Afecta a la página de correos de la cuenta (se abre desde el menú «Correo y verificación» y el menú desaparece), «Verifique su correo», enlace de confirmación inválido, «Le hemos enviado un correo», «Su contraseña ha cambiado», «Cuenta desactivada» y «Cerrar sesión».
4. **Historial del navegador.** Cada formulario que redirige a la misma página deja una entrada repetida en el historial: correos de la cuenta, ficha del paciente (invitar, revocar acceso o invitación, consentimientos, archivar o reactivar), métodos de pago y perfil. Variante: tras registrar una actividad (HU-03), corregir el historial o guardar un formulario, «atrás» vuelve al formulario ya enviado y lo muestra como pendiente. El selector de modo claro u oscuro siempre lleva al inicio.
5. **Textos.** Quedan textos en inglés («E-mail Addresses», «The password reset link was invalid… Please request a new password reset», los de `verified_email_required.html`) y varias páginas tratan de «usted» mientras el resto del portal tutea.

La app móvil abre en el navegador «Crear cuenta», la política y su aceptación, así que estos problemas también llegan a quien usa el teléfono.

Resultado esperado: quien elige una contraseña ve en vivo qué reglas cumple; la política se lee con secciones claras; ninguna página de cuenta deja al usuario sin salida; «atrás» lleva a la página anterior real; y el portal habla en español de Chile, tuteando, en todas sus pantallas.

## Actores y permisos

Sin cambios. Esta spec cambia presentación y navegación, no quién puede hacer qué. La matriz por rol de la [spec 013](../013-cuidado-delegado/spec.md), los cargos de la [spec 004](../004-administracion-usuarios/spec.md) y la aceptación de política de la [spec 014](../014-privacidad/spec.md) siguen igual.

| Acción / datos | Anónimo | Usuario con sesión | Administrador (cargos de 004) | Superusuario |
|---|---|---|---|---|
| Indicadores de contraseña en registro y restablecimiento por correo | Sí | Sí (cambiar o crear contraseña) | Sí, además en crear usuario y restablecer contraseña de un usuario | Igual que administrador |
| Ver la política de privacidad | Sí | Sí | Sí | Sí |
| Navegación en páginas de cuenta | Enlaces a iniciar sesión, crear cuenta o planes | Menú del portal | Menú del portal | Menú del portal |
| Volver a la página anterior tras el modo visual | — | Solo a una ruta interna del portal (RF-018-13) | Igual | Igual |

La validación de contraseñas sigue siendo del servidor. Los indicadores no habilitan nada que hoy esté negado.

## Alcance y exclusiones

Incluye:

- Indicadores en vivo de las reglas de contraseña y de la coincidencia de la confirmación en las seis pantallas.
- Estilos propios de la política de privacidad, disponibles con o sin sesión, un índice de secciones y una salida coherente con el origen.
- Navegación del portal en las páginas de cuenta con sesión, y una salida explícita en cada página de cuenta terminal.
- Que las acciones que vuelven a la misma página, y los formularios que se envían con éxito, no dejen entradas repetidas o ya usadas en el historial; y que el modo visual vuelva a la página donde estaba el usuario.
- Traducir los textos en inglés y unificar el tuteo en las páginas listadas en RF-018-14 y RF-018-15.

No incluye:

- Cambiar las reglas de contraseña del servidor (`AUTH_PASSWORD_VALIDATORS`) ni sus mensajes de error.
- Cambiar el contenido de la política de privacidad (versión, plazos, derechos). Un cambio de contenido exige nueva versión y nueva aceptación (spec 014).
- Los correos que envía allauth (`templates/account/email/*.txt`): no se revisó su tono en esta revisión; quedan como trabajo futuro.
- Las pantallas de la app Flutter. La app solo tiene inicio de sesión con contraseña y no crea cuentas.
- Rediseñar las páginas o cambiar la marca (spec 002 y 015).
- Las pantallas internas de 2FA, que ya tienen el menú. Solo entran si muestran textos en inglés (RF-018-14).

## Historias y flujo

1. **Crear cuenta.** La persona escribe una contraseña. Cada regla empieza neutra; al escribir, «Al menos 8 caracteres» se pone en rojo con ✕ y, al llegar a 8, en verde, tachada y con ✓. «Las contraseñas coinciden» se evalúa al escribir la confirmación. La regla de contraseña común muestra «se revisa al crear la cuenta». Si el servidor rechaza la contraseña, la regla que falló se marca en rojo junto al mensaje de error.
2. **Leer la política desde el registro.** La persona abre la política (en otra pestaña, para no perder el formulario), ve un índice, títulos separados y listas con viñetas. Las salidas son «Crear cuenta» e «Iniciar sesión». Con sesión, la salida es su panel.
3. **Verificar el correo.** Tras crear la cuenta, «Verifica tu correo» ofrece «Ver planes» y, según la sesión, «Ir a mi panel» o «Iniciar sesión». Con un enlace inválido, ofrece pedir otro correo y volver.
4. **Correos de la cuenta.** Desde el menú, la página de correos se abre con el menú visible. La persona marca un correo como principal tres veces seguidas; el mensaje aparece cada vez; un solo «atrás» la lleva a la página desde donde llegó.
5. **Ficha del paciente.** El titular invita a un cuidador y revoca una invitación; un «atrás» vuelve a la lista de pacientes, no a la misma ficha.
6. **Registrar una actividad.** El cuidador confirma un medicamento (HU-03) y llega a la agenda. Al pulsar «atrás» no vuelve al formulario ya enviado como si estuviera pendiente.
7. **Modo visual.** Desde la ficha de un paciente, la persona cambia a modo oscuro y sigue en la ficha.
8. **Sin JavaScript.** Todo lo anterior se envía y valida igual que hoy; los indicadores muestran la lista fija y el historial se comporta como hoy. Nada deja de funcionar.

## Requisitos funcionales

### Contraseñas

- RF-018-01: CUANDO una persona escribe en el campo de contraseña nueva de crear cuenta, cambiar contraseña, crear contraseña, restablecer desde el correo, crear usuario (administrador) o restablecer la contraseña de un usuario (administrador), EL SISTEMA muestra cada regla con uno de tres estados: neutra (aún no evaluada o no evaluable en el navegador), cumple (verde, tachada, ✓) y no cumple (rojo, ✕), y lo actualiza con cada tecla.
- RF-018-02: Las reglas mostradas corresponden a los validadores del servidor: al menos 8 caracteres y no solo números (evaluadas exactas en el navegador); no parecida al usuario ni al correo (según P-018-01); no ser una contraseña común (según P-018-02).
- RF-018-03: CUANDO la persona escribe la confirmación, EL SISTEMA indica si coincide con la contraseña con el mismo código de estados.
- RF-018-04: SI el servidor rechaza la contraseña, ENTONCES la pantalla muestra su mensaje de error como hoy y marca como no cumplida la regla correspondiente. Un indicador verde nunca permite saltarse la validación del servidor.

### Política de privacidad

- RF-018-05: CUANDO cualquiera abre `/privacidad/`, con o sin sesión, EL SISTEMA muestra la política con títulos de sección distinguibles, separación entre secciones, listas con viñetas, un ancho de lectura cómodo y el aviso de borrador destacado, en modo claro y oscuro.
- RF-018-06: La política tiene un índice con enlaces a cada sección.
- RF-018-07: SI la persona no tiene sesión, ENTONCES la política ofrece «Crear cuenta» e «Iniciar sesión»; SI tiene sesión, ofrece volver a su panel. El enlace desde «Crear cuenta» sigue abriendo la política en otra pestaña para no perder el formulario.

### Páginas sin salida

- RF-018-08: CUANDO una persona con sesión abre la página de correos de la cuenta o cerrar sesión, EL SISTEMA muestra el menú del portal, como en cambiar contraseña.
- RF-018-09: Cada página de cuenta terminal ofrece al menos una salida explícita:

  | Página | Salidas |
  |---|---|
  | Verifica tu correo (`verification_sent`) | Ver planes; Ir a mi panel o Iniciar sesión, según la sesión |
  | Confirmar el correo, enlace válido | Confirmar; Cancelar (panel o iniciar sesión) |
  | Confirmar el correo, enlace inválido o vencido | Pedir otro correo; Volver |
  | Verificación de correo obligatoria (`verified_email_required`) | Reenviar verificación o cambiar correo; Volver |
  | Correo de restablecimiento enviado | Volver a iniciar sesión |
  | Enlace de restablecimiento inválido | Pedir un enlace nuevo; Volver a iniciar sesión |
  | Contraseña cambiada (desde el correo) | Iniciar sesión |
  | Cuenta desactivada | Volver a iniciar sesión |
  | Cerrar sesión | Cerrar sesión; Cancelar (vuelve al panel) |

- RF-018-10: SI la persona tiene sesión, ENTONCES el logo de las páginas de cuenta lleva a su panel; si no, a iniciar sesión.

### Historial del navegador

- RF-018-11: CUANDO una acción se envía con éxito y vuelve a la misma página (correos de la cuenta, ficha del paciente, métodos de pago, perfil), EL SISTEMA no agrega una entrada nueva al historial. Después de N acciones, un solo «atrás» lleva a la página anterior distinta. El mensaje de la acción se muestra una vez.
- RF-018-12: CUANDO un formulario se envía con éxito y lleva a otra página (registrar actividad, corregir historial, formularios de paciente, medicamento, cuidado, postura y reloj, crear usuario), EL SISTEMA reemplaza la entrada del formulario: «atrás» desde el destino no muestra el formulario ya enviado como pendiente. Un formulario con errores se queda en pantalla como hoy.
- RF-018-13: CUANDO una persona cambia el modo visual, EL SISTEMA la deja en la página donde estaba. SI la página de origen no es una ruta interna del portal, ENTONCES vuelve al inicio, como hoy.

### Textos

- RF-018-14: Ninguna página del portal muestra texto en inglés. Como mínimo: el título de correos de la cuenta, el aviso de enlace de restablecimiento inválido y `verified_email_required.html`, más los que la plantilla o la traducción de allauth dejen en inglés en las páginas de cuenta y de 2FA.
- RF-018-15: Las páginas del portal tutean (es-CL), como el resto: iniciar sesión, restablecer contraseña y sus confirmaciones, verificar y confirmar correo, correos de la cuenta, cerrar sesión y administración de usuarios.

## Datos y reglas

- No hay modelos, migraciones ni cambios de API.
- **La contraseña nunca sale del navegador mientras se escribe.** Los indicadores se calculan localmente, no se guardan en `localStorage` ni se registran. Esto descarta consultar al servidor tecla a tecla (P-018-02).
- La redirección del modo visual (RF-018-13) solo acepta rutas internas, validadas en el servidor con la utilidad de Django para destinos seguros. Nunca una URL externa (redirección abierta, OWASP A01).
- Las protecciones existentes no cambian: CSRF, la protección contra doble envío y la firma con vencimiento de las acciones de la agenda (spec 009).

## Criterios de aceptación

| RF | Dado / cuando | Entonces |
|---|---|---|
| RF-018-01 | En crear cuenta, escribo «abc» | «Al menos 8 caracteres» en rojo con ✕; al llegar a 8 caracteres, en verde, tachada y con ✓ |
| RF-018-01 | Abro la pantalla sin escribir | Todas las reglas en estado neutro, sin rojo |
| RF-018-02 | Escribo «12345678» | Largo cumplido; «No solo números» en rojo |
| RF-018-02 | Escribo una contraseña de la lista común | La regla de contraseña común en neutro con «se revisa al guardar» (si P-018-02 = A) |
| RF-018-03 | La confirmación difiere en un carácter | «Las contraseñas coinciden» en rojo; al corregirla, en verde |
| RF-018-04 | Envío «password1234» con los indicadores en verde salvo la común | El servidor la rechaza con su mensaje y la regla común queda en rojo |
| RF-018-01 | Las seis pantallas | Las seis muestran los indicadores, incluidas las dos del administrador |
| RF-018-05 | Abro la política sin sesión en un teléfono de 360 px | Títulos, separación y viñetas visibles, sin desplazamiento horizontal; igual en modo oscuro con sesión |
| RF-018-06 | Pulso una sección del índice | La página baja a esa sección |
| RF-018-07 | Abro la política desde «Crear cuenta» | Se abre en otra pestaña y ofrece «Crear cuenta» e «Iniciar sesión» |
| RF-018-08 | Con sesión, abro «Correo y verificación» desde el menú | La página de correos muestra el menú |
| RF-018-09 | Tras crear la cuenta, llego a «Verifica tu correo» | Hay «Ver planes» y una segunda salida según la sesión |
| RF-018-09 | Cada página de la tabla | Muestra sus salidas |
| RF-018-10 | Con sesión, pulso el logo en una página de cuenta | Llego a mi panel, no a iniciar sesión |
| RF-018-11 | Marco un correo como principal 3 veces y pulso «atrás» una vez | Vuelvo a la página anterior distinta; el mensaje se mostró una vez por acción |
| RF-018-11 | En la ficha, invito y luego revoco la invitación, y pulso «atrás» | Salgo de la ficha a la página anterior |
| RF-018-12 | Confirmo un medicamento y pulso «atrás» en la agenda | No veo el formulario de esa actividad como pendiente |
| RF-018-12 | Envío un formulario con un error | El formulario sigue en pantalla con el error, como hoy |
| RF-018-13 | Cambio a modo oscuro en la ficha de un paciente | Sigo en la ficha, en modo oscuro |
| RF-018-13 | Envío el modo visual con un destino externo forzado | Termino en el inicio, no en el sitio externo |
| RF-018-14 | Recorro las páginas de cuenta y de 2FA | Ningún texto en inglés |
| RF-018-15 | Recorro las páginas listadas | Todas tutean |
| Todos | Con JavaScript desactivado | Los formularios se envían y validan como hoy; ninguna acción se pierde |

## No funcionales

- **Accesibilidad:** el estado de cada regla no depende solo del color (icono ✓/✕ y texto para lectores de pantalla). Un resumen se anuncia sin interrumpir (`aria-live="polite"`). Contraste suficiente en modo claro y oscuro (spec 003).
- **Teléfono:** todo funciona a 360 px de ancho, porque es el caso de la app móvil.
- **Sin dependencias nuevas** y sin scripts de terceros; JavaScript propio y CSS del tema, compilado con `manage.py tailwind build`.
- **Mejora progresiva:** sin JavaScript, el portal funciona como hoy.
- **Privacidad:** la contraseña no se envía ni se guarda mientras se escribe.

## Compatibilidad

- Plantillas de allauth sobrescritas en `web/templates/account/` y `web/templates/mfa/`; deben seguir funcionando con la versión fijada en `web/requirements.txt`.
- Registro público y aceptación de la política (specs 007 y 014), con sus pruebas actuales.
- Navegación coherente (spec 008), modo visual (spec 003), restablecimiento administrativo (spec 004), marca y estilos (specs 002 y 015).
- La app móvil abre `/accounts/signup/`, `/privacidad/` y `/privacidad/aceptar/` en el navegador: las rutas no cambian.
- Las pruebas existentes de Django (247) deben seguir pasando.

## Supuestos y decisiones pendientes

Supuestos (reversibles):

- Las reglas se muestran neutras hasta la primera tecla y luego en rojo o verde, para no recibir a la persona con todo en rojo.
- La regla de contraseña común se muestra con el texto «se revisa al guardar», no «se revisa al crear la cuenta», porque también aparece al cambiar la contraseña.

Decisiones pendientes:

- **P-018-01 — Regla «no parecida al usuario ni al correo» en el navegador.**
  - **A (recomendada):** aproximarla. Se marca en rojo solo cuando la contraseña contiene claramente el usuario o la parte del correo antes de la @ (sin distinguir mayúsculas). En otro caso queda neutra con «se revisa al guardar». El validador de Django usa un cálculo de similitud distinto, así que una regla en verde podría fallar en el servidor.
  - **B:** dejarla siempre neutra.
- **P-018-02 — Regla «no ser una contraseña común».**
  - **A (recomendada):** dejarla neutra con «se revisa al guardar». La lista de Django tiene unas 20.000 entradas.
  - **B:** incluir en el navegador una lista reducida de las más comunes. Detecta solo una parte y pesa más la página.
  - **C (descartada):** consultar al servidor mientras se escribe. Enviaría la contraseña tecla a tecla.
- **P-018-03 — Cómo evitar las entradas repetidas en el historial (RF-018-11 y RF-018-12).**
  - **A (recomendada):** JavaScript propio que envía los formularios marcados, muestra la página resultante y reemplaza la entrada del historial en vez de agregar una. Sin JavaScript, el envío normal de hoy.
  - **B:** solo en el servidor, mostrando el resultado en la respuesta del envío sin redirigir. Recargar la página volvería a enviar el formulario; se descarta salvo que A falle.
  - **C:** corregir solo la página de correos y la ficha del paciente, y aceptar el resto.

## Revisión y cambios

- 2026-10-27: borrador documental a pedido del propietario («redacta la spec 018»), después de la prueba por wifi y de la revisión de casos similares. Sin plan ni tareas todavía; no autoriza implementación.
- 2026-10-27: el propietario autoriza la implementación. Se aplican las opciones recomendadas de P-018-01..03 (D-078..D-080) y se redactan [plan.md](plan.md) y [tasks.md](tasks.md).
