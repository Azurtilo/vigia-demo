# Tareas — 009 / CuidadosApp

Spec: [spec.md](spec.md). Plan: [plan.md](plan.md).
Estado: tareas 01–11 ejecutadas; 12 parcial por comprobaciones manuales nativas; 13 documentación entregada y aceptación pendiente. Autorización posterior de implementación: SÍ, «te doy permiso de implementar specs 009 alcanse completo».
P-009-01/02/03 confirmadas. Los estados iniciales se conservan al final como antecedentes; no confundirlos con la implementación autorizada.

- [x] T-009-01 — Integrar app CuidadosApp y permiso de titular para todos los cargos.
  - RF: 01/11/12. Depende de: instrucción posterior de implementación.
  - Archivos: app/permissions/urls y core common_settings/urls.
  - Hecho cuando: nombre/case correctos, activo/login y owner compartidos, sin excepción root ni modelos clínicos globales en admin.
- [x] T-009-02 — Modelar pacientes, horarios, guías, eventos, relojes y selección de capacidad.
  - RF: 03–09/12. Depende de: 01.
  - Hecho cuando: constraints/índices/migraciones propuestos creados y probados con fixtures/reversión, sin DB real ni conflicto de dependencias.
- [x] T-009-03 — Evolucionar PlanesApp a Free/Plus/Premium y cupos.
  - RF: 02/10. Depende de: 01.
  - Hecho cuando: tres activos a $0/$4.990/$9.990, max 1/3/null; Pro renombrado/Hogar histórico, snapshots/fechas intocados, IA/cámaras rotuladas futuras.
- [x] T-009-04 — Implementar pacientes propios, archivo/reactivación y validación de cuota.
  - RF: 01/03/10. Depende de: 02/03.
  - Hecho cuando: CRUD limitado al titular, campos válidos, límite atómico compartiendo bloqueo de User; archivo preserva historia y detiene avisos.
- [x] T-009-05 — Integrar elección de pacientes al reducir plan/cancelar/vencer.
  - RF: 02/03/10/12. Depende de: 03/04.
  - Hecho cuando: selección propia firmada/versionada, aviso previo de archivo, pago fallido sin archivos, aplicación atómica, cancelación a término conserva período y retiro invalida selección; vencimiento sin selección no elige pacientes automáticamente.
- [x] T-009-06 — Registrar medicamentos y horarios diarios, tareas y agenda propia.
  - RF: 01/04/08/09. Depende de: 04.
  - Hecho cuando: IDs anidados propios, dosis ingresada sin prescripción, fechas/horas únicas, realizadas/omitidas explícitas, snapshots y agenda coherentes.
- [x] T-009-07 — Implementar guías educativas y assets originales de referencia.
  - RF: 05/11. Depende de: 02.
  - Hecho cuando: ilustraciones locales/alt, instrucciones/fuentes/versiones concordantes y revisadas, móvil/modos; ninguna evaluación automática de paciente.
- [x] T-009-08 — Implementar eventos posturales y temporizadores persistentes.
  - RF: 06/09/12. Depende de: 04/07.
  - Hecho cuando: 60/90/120, timestamps servidor, atomicidad/versiones, pausa/reanudar, edición de intervalo explícita y recarga sin reinicio ni falso cuidado.
- [x] T-009-09 — Implementar avisos dentro de web abierta y acuses separados.
  - RF: 07/08/12. Depende de: 06/08.
  - Hecho cuando: preaviso diez minutos/vencimiento/atraso, poll privado, dedup entre pestañas, revalidación al volver y versiones; sin push/correo/SMS ni promesa con web cerrada.
- [x] T-009-10 — Componer panel, ficha, agenda/historial y navegación.
  - RF: 01/05/08/09/11. Depende de: 05–09.
  - Hecho cuando: próxima acción por paciente, guía legible, Home cliente a cuidados, enlaces propios para todos, selector compartido, HTML de cuidados no depende de animación/gráfico.
- [x] T-009-11 — Verificar servidor, permisos negativos y regresión.
  - RF: todos. Depende de: 01–10.
  - Hecho cuando: suite aislada nueva+base, check/esquema, propiedad incluso root, límite/races/rollback, selección, historia, fechas/DST/medianoche, acuses/generaciones/idempotencia comprobados con datos ficticios.
- [ ] T-009-12 — Compilar e inspeccionar UI y tiempos en navegador.
  - RF: 05–12. Depende de: 10/11.
  - Hecho cuando: @source/exclusiones/Tailwind, cinco anchos/dos modos/teclado/reducido, dos cuentas/pestañas, avisos simulando tiempo desde servidor, suspensión/retorno y fallback; evidencia real y límites de herramienta.
- [ ] T-009-13 — Cerrar documentos/evidencia y entregar para aceptación.
  - RF: todos. Depende de: 11/12.
  - Hecho cuando: validation.md con comandos reales, decisiones/trazabilidad/estado vigentes, límites/pedidos pendientes claros; aceptación no marcada por suite verde.

## Autorización, ejecución y reanudación

2026-10-06: DOCUMENTAR únicamente, inspección de código existente, contexto recibido y referencias primarias. Respuestas explícitas: precios, avisos con web abierta y elección de pacientes activos al bajar cupo. No código/app/dependencia/test ejecutable ni migración creada/ejecutada. Autorizaciones anteriores 007/008 preservadas, sin ampliarlas a cuidado.

Fase inicial conservada como antecedente. Instrucción posterior recibida: «te doy permiso de implementar specs 009 alcanse completo». T-009-01–11 completas; 31 pruebas nuevas/158 totales OK. T-009-12 parcial: cinco anchos/dos modos, formularios, guías, avisos, dos cuentas/pestañas y fallback verificados; zoom, movimiento reducido, offline/suspensión nativos pendientes. T-009-13 documentación/evidencia entregadas, cierre total y aceptación pendientes. [Validación](validation.md) y [resultados](evidencia/verificacion.json). Helpers/preview retirados; no migración real/deploy/commit/push.

## Aceptación del propietario

Pendiente de aceptación funcional/visual. Nombre/división delegados y alcance de implementación autorizado explícitamente después de DOCUMENTAR; responder requisitos no se usó como sustituto de esa autorización.

## Ajuste visual solicitado — 2026-10-06

- [x] T-009-15 — Corregir flechas sobredimensionadas de selectores crispy (RF-009-11/12).
  - Pedido directo «corriges eso porfa» con captura del formulario de postura. Fallo visual, sin cambio funcional/entrevista nueva.
  - Causa observada: plantilla de paquete crispy con utilidades no incluidas en fuentes Tailwind propias; SVG sin tamaño/posición efectivos, además de regla genérica de SVG del formulario.
  - Solución prevista: override local del componente select conservando attrs/opciones/grupos/múltiples, CSS semántico con tamaño/posición/color propios y revisión de caché. No tocar paquete/DB ni reglas de cuidado.
  - Hecho cuando: fallo reproducido, selectores claros/oscuros escritorio/móvil pequeños y operables por teclado, errores/selección conservados, build/regresión pertinentes y evidencia registrada.
  - Resultado: SVG anterior 240×240 debajo del campo; nuevo 20×20 dentro del selector en los cuatro casos 390/1440 claro/oscuro. Teclado, obligatorio y POST postura/90 minutos correctos. Contratos attrs/grupos/múltiples preservados; build 86 ms/check OK. Suite final 158 OK (15,142 s); primera ejecución detectó intermitencia de carrera SQLite, ensayo aislado/repetición posterior correctos, anotada en validación sin cambiar reglas de negocio.

- [x] T-009-14 — Mejorar las cuatro imágenes educativas (RF-009-05/11).
  - Fuente: pedido directo «puedes mejorar las imágenes» y captura de las guías actuales. Ajuste visual dentro del alcance implementado, sin nueva funcionalidad ni spec adicional.
  - Propuesta: ilustraciones originales más detalladas de paciente/cama/apoyos, serie consistente en petróleo/marfil/azul; proporciones humanas reconocibles y composición limpia. Texto de guía/fuente separado del bitmap para mantener lectura móvil.
  - Archivos: static/CuidadosApp/guides, componente guide y resolución de asset si es necesaria; no modificar datos de pacientes ni migrar DB existente.
  - Hecho cuando: cuatro imágenes guardadas en workspace e integradas, inspección real de sujeto/pose/lectura en claro/oscuro y móvil, evidencia/punto de continuación actualizados.
  - Resultado: cuatro PNG originales integrados mediante CareGuide.illustration y el componente compartido; alt actualizado y revisión de caché. Laterales asignados por lado anatómico apoyado tras inspección, no por el nombre del prompt. 31 pruebas OK (0,915 s), Ruff/check/esquema correctos; cuatro casos de navegador a 390/1440, claro/oscuro, imágenes cargadas y sin overflow. [Evidencia visual](evidencia/imagenes-v2-navegador.json), [prompts](evidencia/prompts-imagenes-v2.json). Aceptación del propietario sigue pendiente.
