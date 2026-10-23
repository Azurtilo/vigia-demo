# Contrato implementable 010

Autorización posterior registrada el 2026-10-19. Login/MFA/registro de allauth en /_allauth/app/v1/; API propia en /api/v1/. La API solo acepta X-Session-Token válido, nunca cookies como autorización móvil. Mutaciones JSON con validación de forms/servicios; respuestas privadas sin caché. Error {error, fields?}; 401 sesión, 403 capacidad/actividad, 404 ajeno, 400 datos/versión.

Recursos: GET me, capabilities, patients, agenda, guides, reminders; GET/POST patients/<id>; POST patients para alta; POST patients/<id>/archive o reactivate; GET/POST patients/<id>/medications y tasks; POST .../<obj_id> para edición; POST posture, timer, events y history/<event>/correction con token de acción entregado al consultar; GET history paginada. POST capacity con selección propia/fingerprint/versión.

Detección: POST patients/<id>/nodes crea credencial aleatoria solo mostrada una vez (hash en DB); POST nodes/<id>/revoke. GET patients/<id>/observations. Nodo usa Authorization: Bearer con credencial distinta de sesión, GET edge/status y POST edge/observations; revalida Premium y paciente habilitado, dedup event_id, tiempo y schema. Sin imagen/video ni coordenadas faciales.

Diseño Flutter: fondo #f2f5f8, superficies #ffffff, texto #182536, acento #0f766e, alerta #b42318; tipografía del sistema legible, navegación Agenda/Pacientes/Plan, tarjeta próxima acción y lista cronológica. Mantener guías existentes como assets. UI independiente de web; estados vacíos/error y reintentos sin éxito optimista.
