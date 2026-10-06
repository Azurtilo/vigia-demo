# 003 — Modo claro y oscuro por usuario

Fecha: 2026-10-02. Estado: implementación autorizada y ejecutada; validación visual parcial y aceptación pendientes.
Cambio transversal sobre la renovación 002; no crea una app de negocio.
Fuente: botón de sol/luna en Inicio para elegir modo claro u oscuro y conservar la configuración individual.
Implementación autorizada: **SÍ**, alcance completo de 003, por instrucción posterior explícita del propietario el 2026-10-02. No autoriza migraciones sobre bases reales, producción, despliegue, commits o push.

## Necesidad y resultado

Cada persona debe poder elegir cómo ve la plataforma. Un botón en Inicio alternará entre claro y oscuro; su cuenta conservará la elección al recargar, navegar, cerrar/iniciar sesión o acceder desde otro navegador/dispositivo.

La preferencia pertenece al usuario, no al navegador compartido ni a la marca global del proyecto. Se amplía una exclusión expresa de 002 sin alterar su evidencia histórica.

## Alcance

- Un botón en el encabezado de Inicio, junto a las acciones existentes; luna para activar oscuro y sol para activar claro.
- Modo aplicado a la interfaz autenticada existente: navegación, Inicio/gráfico, usuarios, registro interno, perfil, cuenta/MFA, mensajes, diálogos, carga y errores renderizados con contexto de usuario.
- Preferencia persistente en servidor, lectura al renderizar y guardado exclusivo de la propia cuenta.
- Paleta oscura centralizada en el mismo archivo de tokens, manteniendo legibilidad, estados semánticos y movimiento reducido.
- Migración aditiva, pruebas pertinentes y guía de personalización actualizada después de implementar.

Fuera de alcance: selector de color de marca por usuario, modo automático del sistema, nuevos controles en otras páginas, rediseñar la composición de 002, editar preferencias ajenas, nuevo panel de administración, cambiar autenticación/cargos, dependencias nuevas, reparar .venv, migrar bases reales, producción, despliegue, commits/push.

## Permisos por acción

Todos los «Sí» requieren cuenta autenticada y activa. La preferencia personal no exige cargo administrativo ni cambia los permisos de las demás vistas.

| Acción | Anónimo | ADMIN | MANAGER | RESTRICTED | Sin perfil / sin cargo | Staff sin cargo | Superusuario sin perfil |
|---|---|---|---|---|---|---|---|
| Ver botón en Inicio | No | Sí | Sí | Sí | Sí | Sí | Sí |
| Leer/aplicar su elección | Claro público | Sí | Sí | Sí | Sí | Sí | Sí |
| Guardar su elección por POST/CSRF | No | Sí | Sí | Sí | Sí | Sí | Sí |
| Cambiar preferencia ajena por esta función | No | No | No | No | No | No | No |

Una cuenta inactiva, incluido superusuario inactivo, no puede guardar. No se aceptará un identificador de destinatario como autoridad; el propietario se obtiene de la sesión. GET no modifica la preferencia. Los formularios actuales de perfil/registro no editarán este dato.

## RF

- **RF-003-01 — Selector en Inicio.** Mostrar un único botón operable con ratón, Enter y Espacio. Luna y nombre «Activar modo oscuro» cuando está claro; sol y nombre «Activar modo claro» cuando está oscuro. Estado actual comprensible y foco visible, sin depender solo del icono/color.
- **RF-003-02 — Persistencia individual.** Guardar la elección en la cuenta autenticada; recuperarla en nuevas visitas, sesiones y dispositivos. Dos usuarios del mismo navegador mantienen elecciones independientes. No escribir una preferencia al consultar una página.
- **RF-003-03 — Propiedad y validación.** Solo light/dark son válidos; permisos comprobados en servidor, POST y CSRF obligatorios, propietario exclusivo request.user. Valores vacíos/arbitrarios, GET y peticiones no autorizadas no cambian datos. Repetir el mismo destino conserva el resultado.
- **RF-003-04 — Aplicación coherente.** Renderizar desde el servidor el modo guardado antes de mostrar el contenido; las pantallas autenticadas y gráfico consumen los tokens del modo. Sin fila de preferencia, el modo inicial es claro. Anónimos y preautenticación usan claro; logout conserva el valor guardado para el siguiente acceso del propietario.
- **RF-003-05 — Paletas accesibles.** Ambos modos conservan composición de 002 y colores configurables en tokens.css. Controles, foco, ayudas, estados y gráfico mantienen contraste objetivo: texto normal 4,5:1; texto grande/controles 3:1. Iconos SVG decorativos con nombre accesible; 360–1440 px, zoom 200 % y movimiento reducido contemplados.
- **RF-003-06 — Guardado fiable.** Confirmar visualmente el nuevo modo después de guardar. Ante rechazo/fallo no presentar una elección no persistida como guardada; mantener la preferencia anterior y ofrecer mensaje legible. No dejar un cambio pendiente que continúe después de logout.
- **RF-003-07 — Compatibilidad y entrega.** Preservar autenticación, MFA, permisos, perfil/imagen/actividad, filtros y contratos de 001/002. Documentar migración, pares de colores y resultados reales; no declarar aceptación por tener tests verdes.

## Datos y reglas

Implementación autorizada: `UserVisualPreference` en UsuarioApp, una relación uno a uno con el usuario y `mode` limitado a light/dark. Sin otros datos personales, historial de cambios ni auditoría nueva. Si falta la fila, claro; la fila se crea en el primer guardado válido. Borrar una cuenta elimina su preferencia por cascada; desactivar/logout no la elimina.

Es una migración aditiva con tabla nueva; no rellena todas las cuentas ni modifica Profile, Position o User. Al revertirla se perderían las preferencias, por lo que la reversión real necesita respaldo y autorización propios.

La preferencia no se agrega a formularios de creación/edición del perfil, ni se guarda en cookies/localStorage. Cambiar modo no debe procesar imágenes ni cambiar cargos. La actualización habitual de actividad del middleware existente sigue su comportamiento previo.

## Aceptación

| RF | Escenario | Resultado |
|---|---|---|
| 01, 05 | Inicio claro; pulsar luna con teclado o ratón | Se guarda oscuro, vuelve Inicio oscuro y ofrece sol; mismo foco perceptible, contenido legible en móvil/escritorio |
| 01, 02 | Pulsar sol; recargar/cerrar sesión/volver a entrar | Claro persistido y recuperado |
| 02, 04 | A elige oscuro; B usa el mismo navegador con claro; A vuelve | B no hereda oscuro; A recupera oscuro, también en otro navegador |
| 03 | Peticiones directas por todos los actores de la matriz | Solo activos autenticados cambian su propio valor, cualquiera sea su cargo |
| 03 | Incluir ID de B en el POST de A | B permanece intacto; la operación solo puede afectar A |
| 03, 06 | GET, POST sin CSRF, valor vacío/inválido o fallo al guardar | No se altera la preferencia; respuesta/error coherente, sin mensaje de éxito falso |
| 02, 03 | Enviar dos veces el mismo destino | Una fila por usuario y mismo modo final |
| 04, 07 | Usuario/superusuario sin perfil cambia modo | No se crea ni edita su Profile y sigue teniendo los accesos que ya tenía |
| 04, 05 | Navegar por pantallas autenticadas en oscuro | Todos los componentes/gráfico coherentes; no cambia la marca global de otros usuarios |
| 05, 07 | Tres identidades de 002 en ambos modos, errores, campos y mensajes | Contraste comprobado, estados legibles y datos/validación originales preservados |

## Supuestos y revisión

Persistencia de cuenta en base de datos interpreta «por usuario» y permite varios dispositivos. Inicio es el único lugar solicitado para el botón; su efecto abarca la sesión autenticada. Claro inicial, sin selección automática del sistema, aprobado con el alcance e implementado. Paleta oscura final pendiente de aceptación estética del propietario.

No apareció una decisión crítica nueva ni efectos de migración distintos de los aprobados. La tabla/POST/tokens se implementaron según [plan.md](plan.md); resultados y pendientes reales en [validation.md](validation.md) y [tasks.md](tasks.md). La migración solo se ejecutó/revirtió sobre SQLite efímero. Pendientes de T-002-13 y aceptación de 002 se conservan.

2026-10-02: requerimiento nuevo registrado; fase documental solamente.
2026-10-02, instrucción posterior: propietario revisó documentos y autorizó exclusivamente el alcance completo de 003; implementación entregada para revisión, sin aceptación asumida.
