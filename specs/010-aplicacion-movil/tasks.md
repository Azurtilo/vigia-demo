# Tareas — 010 / Aplicación móvil

Spec: [spec.md](spec.md). Plan: [plan.md](plan.md).
Estado: implementación parcial verificada · 2026-10-19. Implementación autorizada: SÍ, instrucción posterior del usuario el 2026-10-19.
La autorización posterior permite la ejecución; casillas completas solo cuando se cumple su criterio. Ver estado real al final.

- [ ] T-010-01 — Cerrar alcance y matriz clínica.
  - RF: RF-010-01–12.
  - Depende de: ninguna.
  - Archivos previstos: spec.md, plan.md.
  - Hecho cuando: ubicación/reglas P-010-01, colaboración P-010-02 y matriz comercial P-010-06 resueltas; demás decisiones asignadas; permisos por acción definidos.
- [x] T-010-02 — Definir contrato de autenticación y API.
  - RF: RF-010-01–06/10.
  - Depende de: T-010-01 (numeración dentro de esta spec).
  - Archivos previstos: contrato Markdown; UsuarioApp/api/ y CuidadosApp/api/ previstos.
  - Hecho cuando: rutas/campos/errores, MFA/Google, revocación y concurrencia revisables antes de código.
- [ ] T-010-03 — Preparar cliente Flutter iOS y Android.
  - RF: RF-010-01/10.
  - Depende de: T-010-01/02 (numeración dentro de esta spec).
  - Archivos previstos: mobile/ previsto.
  - Hecho cuando: nombre confirmado, entorno verificado y ambas plataformas conectan solo a backend de prueba.
- [ ] T-010-04 — Integrar autenticación existente.
  - RF: RF-010-01.
  - Depende de: T-010-02/03 (numeración dentro de esta spec).
  - Archivos previstos: UsuarioApp/api/, mobile/lib/auth/ previstos.
  - Hecho cuando: acceso/inactivo/MFA/expiración/logout comprobados sin eludir reglas.
- [x] T-010-05 — Exponer pacientes y suscripción propia.
  - RF: RF-010-02/06.
  - Depende de: T-010-02/04 (numeración dentro de esta spec).
  - Archivos previstos: CuidadosApp/api/, PlanesApp/api/ previstos.
  - Hecho cuando: propiedad/cupos y plan correctos; portal conserva operaciones comerciales.
- [x] T-010-06 — Exponer agenda, eventos, guías y reloj.
  - RF: RF-010-03–05/10.
  - Depende de: T-010-02/05 (numeración dentro de esta spec).
  - Archivos previstos: CuidadosApp/api/ previsto.
  - Hecho cuando: servicios compartidos y reintentos concurrentes web/móvil sin doble registro.
- [x] T-010-07 — Construir pantallas de cuidados e historial.
  - RF: RF-010-02–06/10.
  - Depende de: T-010-03/05/06 (numeración dentro de esta spec).
  - Archivos previstos: mobile/lib/care/ y subscription/ previstos.
  - Hecho cuando: flujos completos, errores visibles y reloj conforme a servidor.
- [ ] T-010-08 — Implementar colaboración solo si se incluye.
  - RF: RF-010-08.
  - Depende de: T-010-01/02/06 (numeración dentro de esta spec).
  - Archivos previstos: política y migración aditiva previstas.
  - Hecho cuando: invitación/aceptación/revocación/cupos acordados y pruebas web/API; si se excluye registrar aplazamiento, no marcar implementada.
- [ ] T-010-09 — Integrar notificaciones según alcance.
  - RF: RF-010-07.
  - Depende de: T-010-01/04/06 (numeración dentro de esta spec).
  - Archivos previstos: backend notifications/ y cliente previstos.
  - Hecho cuando: proveedor/retención definidos y entrega real, privacidad y desvinculación verificadas.
- [ ] T-010-10 — Integrar eventos de detección MediaPipe.
  - RF: RF-010-09.
  - Depende de: T-010-01/02/09/13/14; T-010-08 solo si se acuerda colaboración (numeración dentro de esta spec).
  - Archivos previstos: adaptador de nodo/eventos por definir.
  - Hecho cuando: hardware/protocolo definidos y eventos reales, ajenos, repetidos y fuera de plan comprobados; salida automática diferenciada del registro manual.
- [ ] T-010-11 — Verificar iOS, Android y regresión de base.
  - RF: RF-010-01–12 según alcance.
  - Depende de: T-010-04–10 aplicables y T-010-13–15 (numeración dentro de esta spec).
  - Archivos previstos: pruebas API/Flutter y evidencia previstas.
  - Hecho cuando: permisos, cortes de red, simultaneidad, iOS/Android reales y regresión aislada con resultados reales.
- [ ] T-010-12 — Entregar evidencia y pedir aceptación funcional.
  - RF: RF-010-01–12 según alcance.
  - Depende de: T-010-11 (numeración dentro de esta spec).
  - Archivos previstos: validation.md y docs previstos.
  - Hecho cuando: limitaciones/resultados/paso siguiente registrados; artefactos Android/iOS de prueba solo si tareas autorizadas y sin secretos; no publicación en tiendas.

## Ampliación documental — 2026-10-19

Instrucción humana: iOS y Android, funciones por planes y detección de posición con MediaPipe. En ese momento no autorizaba código; la autorización posterior figura al final.

- [x] T-010-13 — Definir e implementar capacidades por plan tras autorización.
  - RF: RF-010-06, RF-010-09, RF-010-11.
  - Depende de: T-010-01 y T-010-02; resolver P-010-06 antes del código.
  - Archivos previstos: PlanesApp/entitlements.py, API propia y configuración/modelo de capacidades por definir; Flutter consulta de plan.
  - Hecho cuando: matriz acordada aplicada en API y UI, cambio/expiración y pago fallido probados; ningún evento ni push fuera de capacidad; historial conservado.
- [ ] T-010-14 — Preparar y validar detector local MediaPipe y clasificación de postura.
  - RF: RF-010-09.
  - Depende de: T-010-01 y T-010-02; fijar hardware/ubicación y métricas antes de código.
  - Archivos previstos: procesador local, modelos/reglas y evaluación en ruta por definir; no creados.
  - Hecho cuando: supina/lateral izquierda/lateral derecha/indeterminada contrastadas con referencias, oclusión y desconexión explícitas; métricas acordadas satisfechas, sin video en nube ni cuidado manual ficticio.
- [ ] T-010-15 — Completar integración específica y paridad iOS/Android.
  - RF: RF-010-01, RF-010-07, RF-010-10, RF-010-11, RF-010-12.
  - Depende de: T-010-03, T-010-04, T-010-07, T-010-09, T-010-10 y T-010-13.
  - Archivos previstos: mobile/ios/, mobile/android/, pruebas de integración y evidencia por plataforma.
  - Hecho cuando: login, permisos/push, protección de sesión, accesibilidad, planes y resultados MediaPipe verificados por separado en ambos SO; límites de firma/distribución registrados.

## Autorización posterior

Recibida; ver mensaje literal al final. No autoriza producción ni migración de DB existente.

## Ejecución

Implementación parcial ejecutada; ver matriz de cierre y validación.

## Reanudación y aceptación

Revisar decisiones P-010 y ajustar estos mismos documentos, sin nueva spec por aclaraciones. Implementación ya autorizada. Aceptación funcional pendiente.

## Autorización de implementación — 2026-10-19

Mensaje humano posterior: «hacelo en base a todo lo que te proporcione veelo igual en base al informe y todo lo entregado, tomando en cuenta igual lo de planes-pagina revisa todo». Autoriza implementar 010 y verificar en entorno aislado; no despliegue ni DB existente. Se adopta matriz propuesta (Premium MediaPipe, cuidados en todos los planes), nombre técnico vigia_mobile y nodo local conforme al informe. Colaboración consultada de forma específica; no ampliar derechos entre cuentas hasta respuesta.

Decisiones técnicas: autenticación nativa mediante allauth.headless ya incluido en dependencia existente, X-Session-Token con sesión revocable y MFA; API JSON adapta forms/services existentes. iOS/Android son objetivos separados. Detector local MediaPipe con calibración de referencias por postura, sin afirmar validación clínica ni transmisión de imágenes. Firebase requiere configuración externa para entregar push real; no simular entrega como éxito.

## Estado de ejecución comprobado — 2026-10-19

| Tarea | Estado / evidencia o límite |
|---|---|
| 01 | Parcial: matriz Premium y nodo local adoptados; hardware, métricas clínicas y colaboración pendientes. |
| 02 | Contrato y API implementados; autenticación allauth headless existente, sin UsuarioApp/api nuevo. |
| 03 | Cliente y plataformas generadas; APK compilado. Conexión nativa en ambos SO pendiente. |
| 04 | Login/MFA/revocación probados en servidor; UI de acceso probada. Google real y dispositivos pendientes. |
| 05–07 | API, cupos, agenda, servicios, pantallas e historial implementados; pruebas servidor y vista previa. |
| 08 | Pendiente de matriz acordada. No se habilita acceso entre cuentas. |
| 09 | Registro/revocación de dispositivo y worker implementados; entrega real/configuración pendientes. |
| 10 | API de nodo, idempotencia y capacidades probadas; observaciones de cámara real pendientes. |
| 11–12 | Parciales: evidencia y guía entregadas; aceptación y verificación nativa pendientes. |
| 13 | Capacidades servidor/UI, expiración, revocación y plan insuficiente comprobados; push real pendiente en 09. |
| 14 | Clasificador calibrable y regla temporal implementados; 5 pruebas sintéticas + modelo cargado. Precisión real no validada. |
| 15 | Pendiente paridad comprobada en Android/iOS físicos, firma e integraciones externas. |

[Resultados detallados](validation.md) · [Cómo probar](../../docs/MOVIL_DESARROLLO.md).

## Tareas del ajuste — 2026-10-20

- [ ] T-010-16 (RF-010-01): sustituir alta móvil por enlace al registro web existente y verificar login conservado.
- [x] T-010-17 (RF-010-10/12): inspeccionar referencia AI Studio cuando sea accesible y documentar diferencias antes de adaptar pantallas. Dependencia: acceso al prototipo o exportación del usuario.

T-010-16: código ajustado; verificación Flutter pendiente por SDK temporal ausente, casilla conservada pendiente. T-010-17: bloqueo de acceso Google, sin diseño inferido.

## Adaptación documentada — 2026-10-20

T-010-17 completada: referencia recorrida y diferencias registradas; bloqueo Google resuelto. Usuario mantiene planes web y solicita cámara móvil más nodo fijo. Nuevas tareas pendientes:

- [ ] T-010-18 (RF01/02–06/10/12): implementar navegación y estilo de referencia con login web compartido, pantallas Inicio/Medicinas/Posturas/Perfil y capacidades reales. Dependencia: mapa de referencia. Hecho al verificar flujos y estados en ambos SO.
- [ ] T-010-19 (RF09/11): definir contrato definitivo de origen móvil/fijo, fuente activa, idempotencia y alertas; adaptar modelo/API con migración aditiva y pruebas de aislamiento. Dependencia: decisiones de detección dual.
- [ ] T-010-20 (RF09/12): integrar MediaPipe y cámara local Android, permisos/ciclo de vida/calidad, sin video remoto. Depende de19. Hecho con inferencia real y escenarios negativos documentados.
- [ ] T-010-21 (RF09/12): integración equivalente iOS y pruebas independientes. Depende de19; requiere SDK/espacio/firma según dispositivo.
- [ ] T-010-22 (RF09/11/12): probar coexistencia teléfono/nodo fijo, revocación y ausencia de doble alerta; presentar modalidad/origen en UI. Depende de19–21.
- [ ] T-010-23 (RF02): acordar alcance de campos nuevos de ficha y reportes antes de implementar migraciones adicionales; conservar datos existentes.

La ampliación queda documentada; ninguna de estas tareas se declara implementada por esta inspección.

## Implementación de adaptación — 2026-10-20

Autorizada explícitamente: «realiza los cambios en lo que ya estaba en base a lo que te pedi».

- T18: código de seis destinos, Inicio/acciones, filtros de medicamentos, búsqueda de paciente, accesos Guías/Reloj/Cámara y Perfil; tema índigo. Validación visual/nativa pendiente.
- T19: contrato de snapshots móvil por X-Session-Token, fuente separada y migración0005 generada. API/propiedad/capacidad/idempotencia probadas. Nodo fijo conserva sus credenciales e inmovilidad; foto móvil no genera alertas.
- T20/21: camera0.12.1 y plugin local Android/Swift escritos; modelo oficial incluido; inferencia local, calibración por sesión, permiso, pausa y liberación de recursos. Dependencias/compilación/inferencia física pendientes. No marcar como verificado.
- T22: separación de orígenes e imposibilidad de riesgo móvil probadas en servidor; coexistencia física pendiente.
- T23: no se añadieron campos clínicos/foto/reportes sin contrato; se conservan ficha y contactos existentes.

SDK temporal ausente y disco con menos de300MB libres bloquean pub get/analyze/tests/build/UI actual. APK anterior conservado y obsoleto respecto de este código. [Validación](validation.md).
