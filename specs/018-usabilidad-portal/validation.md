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

## Resultados finales — T-018-07 (2026-10-27)

| Comando | Resultado |
|---|---|
| `manage.py test UsuarioApp homeApp PlanesApp CuidadosApp PrivacidadApp --settings=core.test_settings` | **269** pruebas OK (desde 247) |
| `manage.py check --settings=core.test_settings` | Sin problemas |
| `manage.py makemigrations --check --dry-run --settings=core.test_settings` | Sin cambios |
| `manage.py tailwind build` (Tailwind 4.3.0) | Compila. El CSS compilado solo cambia por una utilidad `.fixed` que sale de la palabra `fixed` en `CuidadosApp/api/detection.py` (spec 017); es previo a esta spec y no se incluye |

Sin cambios en Edge ni Flutter: no se tocaron `edge/` ni `mobile/`.

### Evidencia por requisito

| RF | Pruebas automáticas | Navegador |
|---|---|---|
| RF-018-01..04 | `UsuarioApp.tests.IndicadoresContrasenaTests` (6): las seis pantallas, reglas derivadas de la configuración, rechazos del servidor en rojo (también los que Django adjunta a la confirmación), mensaje único de coincidencia, contraseña ausente del HTML | 13 comprobaciones en registro y cambiar contraseña |
| RF-018-05..07 | `PrivacidadApp.tests.PolicyReadingTests` (3): índice, secciones, salidas según la sesión, política en otra pestaña desde el registro | Jerarquía, viñetas y sin desplazamiento horizontal a 360 px; capturas en modo claro y oscuro |
| RF-018-08..10 | `UsuarioApp.tests.SalidasCuentaTests` (4): menú, salidas de las 9 páginas y logo | Menú en correos |
| RF-018-11..13 | `UsuarioApp.tests.HistorialNavegacionTests` (6): middleware con y sin cabecera, redirección externa, errores, cookies de mensajes, `next` del modo visual, exportaciones sin marcar | 9 comprobaciones, abajo |
| RF-018-14/15 | `UsuarioApp.tests.TextosCuentaTests` (3): 24 páginas con y sin sesión y 7 acciones; ayuda de restablecer una sola vez | — |

Mutaciones: 4 en las reglas de contraseña, 5 en el middleware y el modo visual, y 5 en los textos; las 14 hicieron fallar alguna prueba.

### Navegador — Chrome 156 headless

Chrome manejado por el protocolo DevTools con un cliente propio (fuera del repositorio), ventana de 360 × 800 en modo móvil, contra una copia migrada y desechable de la base de la demo en `127.0.0.1:8001` con la cuenta ficticia `demo_plus`. La base `.mobile-demo/demo.sqlite3` no cambió (hash comprobado).

Resultado: **30 de 30 comprobaciones OK** y ningún error de JavaScript. Entre ellas:

- La lista queda justo debajo del campo de contraseña y empieza neutra. «abc» pone el largo en rojo; «12345678», el largo en verde y tachado y «solo números» en rojo. Una contraseña con el usuario pone el parecido en rojo y la confirmación pasa de rojo a verde. El resumen anuncia «Requisitos cumplidos: 3 de 3.».
- En «Correos de tu cuenta», tres «Hacer primario» seguidos muestran el mensaje y **no agregan entradas al historial**; un solo «atrás» vuelve al panel. Control: quitando la marca, dos envíos agregan dos entradas, que es el problema reportado.
- Un correo inválido muestra el error en el lugar del formulario sin agregar entradas, y los scripts siguen funcionando.
- El modo visual cambia en `/cuidados/`, se queda en `/cuidados/` y no agrega entradas.

Ajuste hecho tras ver las capturas: la lista ahora pone primero las reglas que el navegador comprueba y oculta «(se revisa al guardar)» en una regla que ya está en rojo.

Incidencias de la prueba, no del producto:

- Varias corridas seguidas contra la página de correos alcanzaron el límite de solicitudes de allauth (429). Se reinició el servidor de prueba para limpiar el contador.
- En una corrida tardía, el control falló porque Chrome limita el historial de una pestaña a 50 entradas; en la corrida anterior el mismo control pasó (43 → 45).

### Hallazgos y pendientes

- **Mensajes de validación de Django en «usted».** Por ejemplo: «Introduzca una dirección de correo electrónico válida.». Vienen del catálogo de Django y aparecen en cualquier formulario del portal. Corregirlos en todo el portal exige un catálogo de traducción propio (`LOCALE_PATHS` y un `.mo` compilado), fuera del alcance de esta spec. Queda propuesto como trabajo futuro.
- **La revisión previa sobrestimó el «usted» en la administración de usuarios.** El «su» de esas páginas es de tercera persona («asigna su cargo») y está bien.
- **Sin probar en un teléfono físico.** El JavaScript se verificó en Chrome de escritorio con ventana móvil. La prueba en el teléfono del propietario por wifi queda pendiente.
- **Sin probar en el navegador:** la ficha del paciente (invitar, revocar, consentimientos, archivar), métodos de pago, perfil y los formularios de CuidadosApp. Usan el mismo mecanismo y sus vistas redirigen de la misma forma, pero no se recorrieron.
