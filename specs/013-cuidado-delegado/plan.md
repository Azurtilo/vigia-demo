# Plan técnico — 013 / Cuidado delegado

Spec: [spec.md](spec.md). Estado: propuesta; sin código.
Autorización de implementación: pendiente.

## Inspección de la base

Leído el 2026-10-25 en la rama `docs/decisiones-2026-10-25` (commit 99afd9f):

- `web/CuidadosApp/models.py`: `Patient.owner` (FK a usuario, PROTECT). `CareEvent.author`, con idempotencia única por (`author`, `reference`) y ocurrencia única por (`patient`, `occurrence_key`). `ReminderReceipt` por usuario y `CapacitySelection` por usuario.
- `web/CuidadosApp/services.py`: cada mutación hace `locked_user(user)` y luego `own_patient(actor, pk)`, que filtra `owner=user`. Los tokens de acción (`action_token`/`read_action`) van firmados con `user.pk`. `require_eligible(actor, patient)` usa el cupo de quien actúa.
- `web/CuidadosApp/capacity.py` y `scheduling.py`: `capacity_state(user)`, `agenda(user)` y `reminders(user)` parten de `Patient.objects.filter(owner=user)`.
- `web/CuidadosApp/views.py` (web) y `api/views.py`, `api/detection.py` (API): resuelven el paciente con `own_patient`; las listas filtran `owner=request.user`. `RevokeNodeView` filtra `patient__owner=user`. `allowed()` de detección usa `capabilities(user)`.
- `web/CuidadosApp/management/commands/send_mobile_reminders.py`: recorre dispositivos y, por cada usuario, toma recordatorios y riesgos de sus pacientes propios.
- `web/CuidadosApp/permissions.py`: `CareOwnerMixin` hereda `ClientMixin` (autenticado y activo).
- `web/PlanesApp/entitlements.py`: `capabilities(user)` según la suscripción del usuario.
- Flutter: `mobile/lib/core/api.dart`, `features/patients/patient_screen.dart`, `features/home/care_home.dart`, `features/profile/profile_panel.dart`.
- Última migración de CuidadosApp: `0007_postureobservation_risk_fall`. No hay `CACHES` configurado (caché local por proceso).

Cambios locales a preservar: `.claude/skills/` sin seguimiento.

## Diseño propuesto

Se amplía `CuidadosApp`; no hace falta una app nueva porque el vínculo es parte del dominio del paciente.

1. **Módulo nuevo `CuidadosApp/access.py`.** Concentra la matriz de la spec:
   - `ACTIONS`: acción → roles permitidos (`titular`, `familiar`, `cuidador`), por ejemplo `view`, `edit_patient`, `configure`, `record`, `history`, `correct`, `manage_access`, `manage_nodes`, `archive`.
   - `role_for(user, patient)` devuelve `titular` si es el dueño, el rol del vínculo activo, o `None`.
   - `patient_for(user, pk, action)` → (paciente, rol): 404 sin rol y `PermissionDenied` (403) si el rol no permite la acción. Reemplaza a `own_patient` en vistas y servicios.
   - `accessible_patients(user)`: queryset de pacientes propios más vinculados activos, anotado con el rol.
   - `active_ids_for(user)`: une los ids activos de `capacity_state(titular)` de cada titular involucrado, restringidos a los pacientes vinculados.
   - `own_patient` se conserva como atajo de solo titular para crear paciente, cupo y selección.
2. **Bloqueo.** Toda mutación sobre un paciente bloquea la fila del **titular** (`locked_user(patient.owner)`), no la de quien actúa. Así una confirmación del cuidador queda serializada con los cambios de plan y cupo del titular, que ya bloquean esa misma fila. Después del bloqueo se vuelve a comprobar el rol, para que una revocación concurrente gane. Se verifica aparte que quien actúa esté activo. El orden es siempre «fila del titular» para no introducir interbloqueos.
3. **Elegibilidad y plan.** `require_eligible(patient.owner, patient)` y `capabilities(patient.owner)` en vez de las de quien actúa (RF-013-09).
4. **Autoría.** `CareEvent.author = actor` (quien actúa), como hoy. `replay` sigue acotado por autor. Los tokens de acción siguen firmados con quien actúa.
5. **Invitaciones (`CuidadosApp/invitations.py`).** `create_invitation`, `preview_code`, `accept_code`, `revoke_access`, `revoke_invitation`, `leave`. El código se genera con `secrets`, se muestra una vez y se guarda su SHA-256. La aceptación es atómica: bloquea al titular, valida el código con `select_for_update`, crea el vínculo y marca el código como usado. El límite de intentos (RF-013-05) se cuenta en base de datos, porque la caché local por proceso no comparte el conteo entre procesos.
6. **Avisos (RF-013-11).** Función `recipients(patient)` en `access.py` con dos salidas: cuidado pendiente (titular y cuidadores) y riesgo (titular, familiares y cuidadores, D-063). `reminders(user)` y `send_mobile_reminders` pasan a recorrer `active_ids_for(user)`, y el riesgo se habilita por `capabilities(titular)`. La spec 012 (D-051, push inmediato) debe reutilizar `recipients`.

## Mapa por requisito

| RF | Archivos existentes / propuestos | Cambio previsto | Evidencia prevista |
|---|---|---|---|
| 01–05 | Nuevo `CuidadosApp/invitations.py`; `models.py` (`PatientInvitation`, `AccessCodeAttempt`) | Generar, previsualizar y aceptar con hash, vencimiento, un solo uso y límite de intentos | Pruebas Django de servicio: vigente, vencido, usado, revocado, propio, duplicado, límite |
| 06 | `invitations.py`; `models.py` (`PatientAccess`) | Revocar, renunciar y revocar código; registrar fecha y autor | Prueba de revocación con token de acción previo → 404 |
| 07 | Nuevo `access.py`; `services.py`, `views.py`, `api/views.py`, `api/detection.py`, `permissions.py` | `patient_for` con acción en cada punto de entrada | Prueba parametrizada endpoint × rol (titular, familiar, cuidador, ajeno, superusuario, revocado) |
| 08 | `views.py` (Panel, PatientList, Agenda, Reminders), `scheduling.py`, `api/views.py` (Patients, Agenda) | Listas con `accessible_patients`/`active_ids_for` y rol | Prueba de listas con pacientes de dos titulares |
| 09 | `services.py`, `capacity.py` | Bloqueo del titular, elegibilidad y plan del titular, autor = actor | Prueba de autor, de ocurrencia única entre titular y cuidador, y de paciente fuera de cupo |
| 10 | `capacity.py` (sin cambios de conteo) | Confirmar que el cupo sigue contando `owner` | Prueba: cupos de titular e invitado sin cambio |
| 11 | `scheduling.py`, `send_mobile_reminders.py`, `access.py` | Destinatarios por rol | Prueba con Firebase simulado: riesgo y cuidado por rol, sin duplicados |
| 12 | `api/views.py` (`patient_data`), Flutter `core/api.dart`, `features/patients/`, `features/home/` | `role` y `allowed_actions` por paciente; la UI se adapta | Prueba Django del contrato; `flutter test` de widgets por rol |
| 13 | Nuevas vistas web y plantillas en `web/templates/pages/CuidadosApp/`; endpoints API; pantalla Flutter | Listar, generar y revocar accesos; «Unirme con un código» | Pruebas Django de vistas; revisión en navegador y en Android |
| 14 | `views.py` (detalle e historial), `api/views.py` (History), Flutter | Vista resumida para el cuidador | Prueba: cuidador recibe 403 en historial y obtiene el resumen |

## Datos y contratos

Modelos nuevos en `CuidadosApp` (migración aditiva `0008`):

- `PatientInvitation`: `patient` (FK PROTECT), `role` (choices `familiar`/`cuidador`), `code_hash` (64, único), `created_by` (FK usuario), `created_at`, `expires_at`, `used_at`/`used_by` (nulos), `revoked_at` (nulo). Índice por (`patient`, `used_at`, `revoked_at`).
- `PatientAccess`: `patient` (FK PROTECT, `related_name="accesses"`), `user` (FK PROTECT), `role`, `invitation` (FK, nulo), `accepted_at`, `revoked_at`/`revoked_by` (nulos). `UniqueConstraint(patient, user)` condicionada a `revoked_at IS NULL`. `CheckConstraint` de rol válido.
- `AccessCodeAttempt`: `user` (FK CASCADE), `created_at`, `success`. Se consulta por ventana de 15 minutos. Su purga queda para la spec de privacidad.

Endpoints API propuestos (bajo `/api/v1/`, autenticación `X-Session-Token` vigente):

| Método y ruta | Rol | Respuesta |
|---|---|---|
| `GET patients` | cualquiera | Agrega `role` y `allowed_actions` a cada paciente (campos nuevos; los clientes actuales los ignoran) |
| `GET patients/<pk>/access` | titular | Vínculos activos e invitaciones pendientes (sin códigos) |
| `POST patients/<pk>/access` | titular | `{role}` → `{code, expires_at}`, una sola vez |
| `POST access/<id>/revoke` y `POST invitations/<id>/revoke` | titular | 200 |
| `POST access/preview` | cuenta verificada | `{code}` → `{patient_name, role}` o error genérico |
| `POST access/accept` | cuenta verificada | `{code}` → paciente con rol |
| `POST patients/<pk>/leave` | familiar o cuidador | 200 |
| `GET patients/<pk>/summary` | cuidador (y superiores) | Agenda del día y última postura |

Rutas web propuestas: `pacientes/<pk>/accesos/` (titular), `pacientes/unirme/` (aceptar), `pacientes/<pk>/salir/` (renunciar). Todas por POST para mutar, con CSRF.

Compatibilidad del contrato: los campos nuevos son aditivos y ningún endpoint actual cambia de forma para el titular. El contrato del nodo no cambia.

## Permisos e interfaz

- Web: `CareView.dispatch` resuelve con `patient_for(..., action)`, donde cada vista declara un atributo `care_action`. Los botones se muestran según el rol en el contexto, pero el control real está en el servidor. Nuevo enlace «Unirme con un código» en el menú de cuidados (`templates/components/navbar/nav.html`) y sección «Personas con acceso» en el detalle del paciente, visible solo para el titular.
- Insignia de rol («Titular», «Familiar», «Cuidador») en las listas web y móvil.
- Flutter: el modelo de paciente lee `role` y `allowed_actions`; las pantallas ocultan acciones no permitidas; una pantalla nueva sirve para ingresar el código y otra para gestionar accesos (titular). Un 403 o 404 inesperado muestra un mensaje y recarga la lista.
- Reutilizar las plantillas base existentes (`components/Layout/base_extendido.html`) y los tokens del tema; textos en es-CL.

## Migraciones y reversión

Una migración aditiva `0008` que solo crea tablas, sin cambiar columnas existentes ni requerir backfill. Reversión: revertir a `0007` borra solo las tablas nuevas (se pierden los vínculos, no los registros clínicos). Probar avance y reversión con datos ficticios en SQLite de pruebas. No aplicar a una base existente por esta spec.

## Plan de pruebas

- **Django (nuevo `CuidadosApp/test_access.py`):**
  - matriz parametrizada endpoint × rol, con 404 para ajeno, superusuario sin vínculo y revocado, 403 para rol sin permiso, y sin cambios en la base en ambos casos (cubre también QA-08 en los endpoints de detección);
  - invitaciones (RF-01..06);
  - autoría y ocurrencia única entre titular y cuidador;
  - elegibilidad por el cupo del titular;
  - destinatarios de push con Firebase simulado;
  - contrato `role`/`allowed_actions`;
  - avance y reversión de la migración.
- **Regresión:** suite completa `UsuarioApp homeApp PlanesApp CuidadosApp`; los tests actuales de dueño único deben pasar sin cambios de comportamiento.
- **Flutter:** pruebas de widgets para titular y cuidador (acciones visibles), pantalla de código (error genérico) y manejo de 403/404; `flutter analyze`.
- **Edge:** sin cambios; correr la suite como regresión.
- **Manual:** navegador (gestión de accesos y unirse) y Android físico con dos cuentas (titular y cuidador), registrando en `validation.md`.

## Riesgos, alternativas y dependencias

- **Riesgo principal:** que un punto de entrada quede con `owner=user` y permita o niegue mal. Mitigación: `own_patient` se usa solo donde la acción es de titular, se revisan con `grep` todos los `owner=` y `own_patient(` de CuidadosApp, y la matriz parametrizada recorre todas las rutas.
- **Bloqueo por titular:** serializa a todas las personas de un mismo titular. Es aceptable para el volumen del prototipo.
- **Alternativa descartada:** agregar `role` al modelo de usuario o usar grupos de Django. El rol es por paciente, no global, y un cuidador puede tener roles distintos con distintos titulares.
- **Alternativa descartada:** compartir la cuenta del titular. No identifica al autor (HU-03).
- **Dependencias:** ninguna dependencia nueva. Coordinar con la spec 012 (D-051) para que el push inmediato use `recipients`, y con la spec de privacidad (D-052) para la conservación de vínculos e intentos.

## Documentos afectados

Al implementar: `specs/README.md` (estado), `docs/TRAZABILIDAD.md` (matriz HU-01/02/03/04/06 y sección 013), `docs/ESTADO_PROYECTO.md`, `docs/CUIDADOSAPP_DESARROLLO.md` (uso de accesos), `docs/MOVIL_DESARROLLO.md` y el estado de D-061 a D-063 en `docs/DECISIONES.md`.

## Decisiones para implementar

Ninguna. P-013-01..03 resueltas por el propietario (D-061 a D-063). La implementación requiere una instrucción posterior explícita.
