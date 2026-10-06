# Tareas — 004 / UsuarioApp

Fecha: 2026-10-02. [Spec](spec.md), [plan](plan.md).
Estado: implementación del alcance completo autorizada por instrucción posterior explícita del propietario el 2026-10-02 y ejecutada. T-004-01 a 06 completas; T-004-07 parcial, T-004-08 documentación entregada con revisión pendiente. Las tareas se crearon todas pendientes en DOCUMENTAR; no se ejecutaron por el hecho de existir.

- [x] **T-004-01 — Fijar contrato y preparar recuperación antes del código.**
  - RF: RF-004-01 a RF-004-07.
  - Depende de: revisión documental e instrucción posterior explícita de implementación de 004. P-004-01/02 ya confirmadas; no repetir preguntas.
  - Archivos: spec.md/plan.md/tasks.md, documentos de estado/decisiones; snapshot acotado cuando se autorice implementación.
  - Hecho cuando: permisos de superusuario definidos en todas las matrices, autorización registrada, cambios locales reinspeccionados y recuperación preparada sin secretos/datos personales.
- [x] **T-004-02 — Añadir política por acción y destinatario.**
  - RF: RF-004-02/03/04.
  - Depende de: T-004-01.
  - Archivos previstos: nuevo UsuarioApp/permissions.py, UsuarioApp/tests.py.
  - Hecho cuando: ADMIN gestiona MANAGER/RESTRICTED; MANAGER solo RESTRICTED; restablecimiento solo administrador autorizado; casos de root decididos, actividad y destinatarios protegidos probados. Helper global/Registro sin cambios.
- [x] **T-004-03 — Ajustar activar/desactivar y controles existentes.**
  - RF: RF-004-02/03/04/06/07.
  - Depende de: T-004-02.
  - Archivos previstos: UsuarioApp/views.py, templates/pages/UsuarioApp/usuarios_lista.html, UsuarioApp/tests.py.
  - Hecho cuando: ambos POST reutilizan política por destinatario, solo guardan is_active, protegen CSRF/404/405, deniegan con 403 y controles por fila coinciden con servidor. Matriz y reenvíos válidos/denegados comprobados.
- [x] **T-004-04 — Preparar formulario de restablecimiento seguro.**
  - RF: RF-004-01/05/06.
  - Depende de: T-004-02.
  - Archivos previstos: UsuarioApp/forms.py, UsuarioApp/tests.py.
  - Hecho cuando: SetPasswordForm reutilizado, dos entradas nuevas y reconfirmación del operador validadas; validadores usan destinatario; errores no guardan ni repueblan secretos y nuevo hash generado mediante Django.
- [x] **T-004-05 — Integrar endpoint y pantalla administrativa.**
  - RF: RF-004-01/04/05/06/07.
  - Depende de: T-004-03/04.
  - Archivos previstos: UsuarioApp/views.py, urls.py, usuarios_lista.html y nueva restablecer_password.html.
  - Hecho cuando: acceso GET/POST protegido, nunca correo/token, escritura mínima transaccional y respuesta sin caché/secretos; formulario/acción compatibles claro/oscuro, cancelar no escribe, errores y fallo de escritura contextual sin éxito aparente. Sin cambios en otros flujos de cuenta.
- [x] **T-004-06 — Verificar seguridad y regresiones en servidor aislado.**
  - RF: todos.
  - Depende de: T-004-03/04/05.
  - Archivos previstos: UsuarioApp/tests.py y validation.md.
  - Hecho cuando: matriz cruzada completa, URL y HTML, login de nueva contraseña, dos sesiones de destinatario y operador, MFA preservado, cero correo, CSRF y fallos probados; check/suite/makemigrations dry-run/build reales registrados. Escenarios de 002 ajustados por cambio autorizado, regresión 001/003 conservada. Sin consultas a bases reales.
- [ ] **T-004-07 — Validar interacción en navegador.**
  - Estado real: parcial. Listado/formulario en cinco anchos y ambos modos, errores, teclado/foco, cancelar, envío vacío bloqueado y sin scripts comprobados; MANAGER desactiva/reactiva RESTRICTED en navegador. Envío válido de nueva contraseña por interfaz pendiente de revisión manual; guardado/sesiones/MFA sí probados en servidor. No se introdujeron nuevas credenciales en el navegador.
  - RF: RF-004-01/04/05/07.
  - Depende de: T-004-06.
  - Archivos previstos: evidencia sintética y validation.md; correcciones acotadas si aparecen fallos.
  - Hecho cuando: listado/formulario/errores en claro/oscuro y móvil/escritorio, teclado/foco, cancelar/guardar y formulario sin scripts comprobados; permisos por destinatario observados; sin contraseñas/datos reales en capturas. Todo límite visual pendiente queda explícito.
- [ ] **T-004-08 — Cerrar trazabilidad y entregar revisión.**
  - Estado real: documentos y diff preparados, resultados registrados; revisión del envío válido de T-004-07 y del propietario pendientes. No se marca aceptación automáticamente.
  - RF: todos.
  - Depende de: T-004-06/07.
  - Archivos: spec/plan/tasks/validation, índices y documentos afectados del plan.
  - Hecho cuando: ejecución y resultados reales/pendientes registrados; diff revisado sin cambios ajenos ni secretos; entrega con siguiente paso. Aceptación funcional del propietario se registra únicamente si ocurre.

## Registro documental realmente ejecutado

| Fecha | Acción | Resultado |
|---|---|---|
| 2026-10-02 | Lectura de reglas, contexto, código y git status/branch/log | main / 8f9adda, árbol limpio al comenzar; política actual y referencias inspeccionadas |
| 2026-10-02 | Inventario/lectura selectiva del ZIP con zipfile | Sin extracción/ejecución; sin importación de FruticulaApp ni cambios de referencia |
| 2026-10-02 | Consulta P-004-01/02 | Propietario confirmó misma jerarquía en activación y exigencia de cargo incluso al superusuario; documentos ajustados |
| 2026-10-02 | Spec → plan → tasks e índices | Solo Markdown; no equivale a completar T-004-01 ni autorizar implementación |

## Autorización y ejecución de código

Recibida después de la fase documental: propietario revisó 004 y autorizó únicamente implementar su alcance completo. No autoriza datos reales, migraciones reales, producción, despliegue, commit o push. [Evidencia y límites](validation.md).

| Fecha | Tarea | Archivos / comando ejecutado | Resultado |
|---|---|---|---|
| 2026-10-02 | T-004-01 | Relectura/status y snapshot .recovery-004 | main/8f9adda; cambios documentales previos conservados, 123 archivos/hash y contratos protegidos idénticos |
| 2026-10-02 | T-004-02/03 | permissions.py, views.py, listado y tests | Política única por actor/destinatario; POST/403/404/405/CSRF; estado mínimo y protección de destinatarios |
| 2026-10-02 | T-004-04/05 | forms.py, views.py, urls.py, plantilla nueva y 500.html | ADMIN reconfirma, validadores/hash; sin correo; transacción/escritura mínima, never_cache y campos sensibles |
| 2026-10-02 | T-004-06 | Helper ejecutar.py test/check/makemigrations dry-run/tailwind build | 57 tests OK, check sin problemas, ningún cambio de esquema, build 4.3.0 y 60 plantillas OK. MFA aislado para evitar efecto lateral de allauth |
| 2026-10-02 | T-004-07 | Preview SQLite en memoria/navegador | Cinco anchos/ambos modos y gestión inferior OK; validación vacía/foco/errores/cancelación/sin scripts; envío válido por UI pendiente manual |
| 2026-10-02 | T-004-08 | Spec/plan/tasks/validation y docs/índices | Entrega y trazabilidad actualizadas; revisión funcional del propietario pendiente |

## Reanudación

Completar revisión manual del envío válido de contraseña por interfaz y aceptación del propietario. No repetir autorización de implementación ni P-004-01/02. Conservar autorización/evidencia de 002/003; no aplicar su migración real por este pedido. Preview únicamente sintético; su cierre/limpieza se registra en validation.md.

Aceptación funcional: pendiente.
