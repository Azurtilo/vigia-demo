# Tareas — 007 / PlanesApp

[Spec](spec.md) · [Plan](plan.md). Fecha: 2026-10-06.
Estado: implementación autorizada y ejecutada; 01–14 técnicamente completas, 15 con revisión visual manual pendiente y 16 con aceptación del propietario pendiente.
Autorización posterior: «te doy permsio de implementar todo la specs 007 alcanse completo», 2026-10-06. [Validación y evidencia](validation.md). La lista inicial se creó con todas pendientes; las marcas actuales corresponden a trabajo comprobado después de ese permiso.

- [x] **T-007-01 — Preparar entorno e integración mínima.**
  - RF: 02/13. Depende de: autorización posterior.
  - Archivos previstos: PlanesApp/apps.py e inicializadores, core/common_settings.py, core/urls.py, requirements.in/lock, docs/DEPENDENCIAS.md.
  - Hecho cuando: nombre sin colisiones, app/namespace registrados en fuente real; extra socialaccount resuelto con hashes sin upgrade general; intérprete aislado verificado y sin acceso a .env/DB real. No asumir .venv-actualizada disponible.
- [x] **T-007-02 — Modelos y datos iniciales.**
  - RF: 04/05/06/11/13. Depende de: 01.
  - Archivos previstos: PlanesApp/models.py, admin.py, migrations/.
  - Hecho cuando: modelos/constraints, cuatro planes/beneficios exactos y Position Cliente público RESTRICTED; colisión de nombre con código distinto falla sin alterar cargos. Migración/reversión ensayadas exclusivamente con datos ficticios; pérdidas/no-op documentados.
- [x] **T-007-03 — Registro público local y aprovisionamiento.**
  - RF: 01/05. Depende de: 02.
  - Archivos previstos: UsuarioApp/services.py, adapters.py, forms.py; PlanesApp/services.py; templates/account/signup.html y login.html; common_settings.
  - Hecho cuando: alta crea User+Profile RESTRICTED+Free atómicos; flags/cargo no manipulables, duplicados/errores sin restos; cuentas previas y registro interno conservados; adaptar regresión de signup cerrado con sustitución explícita de 001.
- [x] **T-007-04 — Confirmación de correo antes de contratar.**
  - RF: 03. Depende de: 03.
  - Archivos previstos: configuración allauth, adapters/forms, plantillas account existentes; PlanesApp/permissions.py.
  - Hecho cuando: envío/confirmación/reenvío probados localmente; cuenta sin verificar conserva resumen/cancelación pero no métodos/contratación; cuentas internas/login/MFA preservados; ningún verificado confiado desde POST.
- [x] **T-007-05 — Google y conexiones seguras.**
  - RF: 02/03. Depende de: 03/04.
  - Archivos previstos: UsuarioApp/adapters.py, core/settings.py/test_settings.py/common_settings.py; templates/socialaccount/ necesarias y enlace de conexiones.
  - Hecho cuando: adapter social comparte alta atómica, Google repetido no duplica ni cambia cargos, colisión exige conexión autenticada, callback/error/cancelación probados con mocks. Configuración OAuth documentada sin secretos; ensayo real solo con credenciales configuradas, o límite pendiente explícito.
- [x] **T-007-06 — Proteger lectura interna y navegación cliente.**
  - RF: 12/13. Depende de: 02.
  - Archivos previstos: UsuarioApp/views.py, homeApp/views.py, core/context_processors.py, templates/components/navbar/nav.html, tests pertinentes.
  - Hecho cuando: RESTRICTED/sin cargo no root reciben 403 Usuarios y Home redirige antes de consultar cuentas; navegación coherente. Root lectura y ADMIN/MANAGER preservados; 004/006 sin cambios de privilegios. Selector visual cliente conserva POST/CSRF/contrato 003.
- [x] **T-007-07 — Catálogo y resumen propio.**
  - RF: 04/05/12/13. Depende de: 02/06.
  - Archivos previstos: PlanesApp/urls.py, views.py, services.py; templates/pages/PlanesApp/catalogo.html y mi_suscripcion.html, componentes de planes.
  - Hecho cuando: catálogo anónimo/privado correcto; Free inicial/virtual, estado por fechas, beneficios/valores y acciones propias, sin métricas ficticias presentadas como reales ni escrituras por GET.
- [x] **T-007-08 — Métodos y simulador de tarjetas.**
  - RF: 06. Depende de: 02/04.
  - Archivos previstos: PlanesApp/simulator.py, forms.py, services.py, views.py/urls.py; plantillas métodos/eliminar.
  - Hecho cuando: lista cerrada/nombre/fecha/CVC validados; guarda solo máscara/fixture, sin PAN/CVC en DB/respuestas/logs; método ajeno 404, duplicados/default/eliminar último con confirmación y atomicidad correctos.
- [x] **T-007-09 — Tarjeta visual en vivo.**
  - RF: 07/13. Depende de: 08.
  - Archivos previstos: componente de tarjeta, PlanesApp/static/PlanesApp/card.js y planes.css; fuentes Tailwind.
  - Hecho cuando: una tarjeta refleja entrada y gira al CVC, sin gradiente/diseño ajeno; teclado/móvil/movimiento reducido/sin JS y errores coherentes. Sin almacenamiento del navegador/analítica ni listeners duplicados.
- [x] **T-007-10 — Checkout, compra y resultado.**
  - RF: 08/11. Depende de: 04/07/08.
  - Archivos previstos: PlanesApp/services.py, forms.py, views.py/urls.py; checkout.html y resultado.html.
  - Hecho cuando: propuesta revalidada, precio desde servidor, propiedad/verificación, CSRF, idempotencia durable y versión/concurrencia; éxito atómico, rechazo sin activar, fallo técnico sin éxito falso y recarga sin nuevo cargo.
- [x] **T-007-11 — Cambios, cancelación y revocación.**
  - RF: 09/11. Depende de: 10.
  - Archivos previstos: servicios/forms/vistas, cancelacion.html, checkout/resumen.
  - Hecho cuando: cambio cobra destino completo y reinicia período, Free inmediato sin reembolso; plan actual no cobra; cancelación a término y revocación antes del cierre, reenvío inocuo y registro de efectos/autor/fecha.
- [x] **T-007-12 — Fechas y renovación simulada.**
  - RF: 10/05/11. Depende de: 11.
  - Archivos previstos: PlanesApp/services.py, forms.py, views.py, resumen/checkout.
  - Hecho cuando: mes calendario y límite de mes/bisiesto/DST definidos; POST Simular renovación elegible no cobra atrasos, no duplica período y no extiende en rechazo. Cancelada/Free no renuevan; lectura sin mutaciones.
- [x] **T-007-13 — Historial y detalle propio.**
  - RF: 11. Depende de: 10/11/12.
  - Archivos previstos: PlanesApp/views.py/urls.py, historial.html/resultado.html.
  - Hecho cuando: paginación y snapshots propios, referencias/estados/fechas claros, borrar método no borra representación histórica; detalle ajeno 404 y etiqueta simulada sin apariencia de factura tributaria.
- [x] **T-007-14 — Pruebas de servidor y regresión.**
  - RF: 01–06/08–13. Depende de: 03–08/10–13.
  - Archivos previstos: UsuarioApp/tests_registro_publico.py, PlanesApp/tests.py y tests de base afectados.
  - Hecho cuando: suite aislada/check/esquema correctos con casos normales/negativos/rollback/propiedad/roles/idempotencia/fechas; adaptaciones históricas justificadas por 007. Concurrencia en motor objetivo probada si disponible o límite explícito; mocks no atribuidos a OAuth real.
- [ ] **T-007-15 — Build y validación visual.**
  - RF: 07/12/13. Depende de: 05–13.
  - Archivos previstos: theme/static_src/src/styles.css, CSS generado, versiones de caché y evidencia bajo esta spec.
  - Hecho cuando: fuentes app/exclusiones/utilidades verificadas, build standalone; navegador ambos modos/cinco anchos/zoom/teclado/movimiento reducido/sin JS con datos ficticios. Estados vacíos/error/rechazo/confirmación y no desbordamiento comprobados; límites registrados.
- [ ] **T-007-16 — Cierre documental y revisión del propietario.**
  - RF: 13 y trazabilidad de todos. Depende de: 14/15.
  - Archivos previstos: validation.md posterior, tasks/índice/proyecto/estado/decisiones/trazabilidad/arquitectura.
  - Hecho cuando: rutas/comandos/resultados reales por RF, pendientes externos honestos y diff revisado; propietario revisa experiencia. Aceptación funcional separada de finalización técnica; no despliegue/migración real/commit/push por esta tarea.

## Autorización y ejecución

01–14 implementadas y verificadas con 117 tests en core.test_settings, check/esquema/pip y ensayo de migraciones en SQLite ficticio. Alta transaccional está en UsuarioApp/signup_forms.py y tests nuevos en PlanesApp/tests.py; se justifican esas rutas efectivas en validation.md. OAuth real se declara pendiente externo por credenciales, conforme al límite de 05. Movimiento reducido implementado/revisado estáticamente, comprobación visual real pendiente en 15.

**T-007-15 parcial:** build standalone correcto, navegador claro/oscuro a cinco anchos, teclado/giro, vacío/errores/aprobado/rechazo/cancelación y formulario con scripts bloqueados comprobados. Pendientes manuales: zoom 200% y preferencia reducida, no configurables por la superficie de navegador disponible. Capturas/mediciones en evidencia/.

**T-007-16 parcial:** documentación, trazabilidad, comandos/resultados y diff revisados; falta la aceptación estética/funcional del propietario. No marcar ese acto como realizado por el agente.

## Reanudación

Código de 007 entregado. Usar .venv, leer docs/PLANESAPP_DESARROLLO.md y validation.md. Configurar OAuth propio sin compartir secretos y ensayar conexión/ingreso real; completar revisiones manuales/aceptación. Migración de DB existente requiere autorización específica de entorno/respaldo. No se hizo despliegue, commit/push ni lectura de .env/DB/media personal. Próxima spec sugerida 008, comprobar.
