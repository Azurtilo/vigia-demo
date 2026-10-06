# Plan técnico — 004 / UsuarioApp

Spec: [spec.md](spec.md). Fecha: 2026-10-02. Estado: plan aprobado mediante instrucción posterior del alcance completo e implementado; [validación y límites](validation.md).
Autorización de implementación: SÍ, recibida el 2026-10-02. P-004-01/02 confirmadas por el propietario: exigir cargo incluso al superusuario y aplicar jerarquía tanto al activar como al desactivar.

## Inspección documental original y trabajo preservado

- Git disponible en main; HEAD inspeccionado `8f9adda`. `git status --short` vacío al comenzar. No stage, reset, commit o push. No se asume que el agente haya creado ese commit.
- Vistas actuales: UserListView usa LoginRequiredMixin, búsqueda/filtro de activos y paginate_by=9. Activa/desactiva mediante PermitsPositionMixin, sin política de destinatario por cargo. Desactivación protege propia cuenta/superusuario; activación no incorpora esas protecciones. User.objects.get puede fallar sin 404 controlado.
- `core/mixins.py`: usuario_tiene_cargo admite superusuario activo sin perfil y no interpreta is_staff como cargo. Ese contrato global se conserva; 004 delimita acciones por destinatario.
- Formularios/modelos/rutas/listado/pruebas/configuración aislada leídos. No existe ruta ni formulario de restablecimiento administrativo. User es el de Django; cargos pueden estar ausentes. AUTH_PASSWORD_VALIDATORS contiene los cuatro validadores estándar.
- ZIP leído sin extraer ni ejecutar: permissions.py, views.py, forms.py y urls.py. Aporta formulario basado en SetPasswordForm con confirmación del operador y funciones por destinatario. También modifica registro/perfil/auditoría/recuperación pública y depende de FruticulaApp: esos cambios no se importan. No contiene las plantillas de la captura.
- SHA-256 inicial de 211 archivos versionados no Markdown conservado para comprobar que esta fase no modifica código/recursos. No se leen .env, bases ni media personal.

## Diseño aprobado e implementado

Las propuestas de archivos/contratos que siguen se ejecutaron: permissions.py, AdministrativePasswordForm/View, UserPasswordReset, flags por fila y plantilla restablecer_password.html. Activar/desactivar comparten vista de estado y política, con escrituras mínimas/transacciones. La página 500 existente recibió el contexto account_management_error y retorno al listado para fallos previstos. No se modificó ningún helper global, modelo o migración.

Inspección previa a código: main/8f9adda; cambios locales de los ocho documentos y carpeta 004 de la fase documental, conservados. Snapshot acotado de 123 archivos en .recovery-004/antes-implementacion.zip con SHA-256. .venv vuelve a fallar por Python312 inexistente; verificación con runtime de Codex/dependencias exactas temporales. Helpers previos .recovery-002/003 no estaban presentes en esta sesión; no se dependió de ellos ni se restauraron archivos del propietario.

Ampliar UsuarioApp, sin nueva app ni cambios a LOCAL_APPS/core/urls.py. Incorporar política pequeña `UsuarioApp/permissions.py` (archivo **propuesto, todavía inexistente**) que obtiene cargo seguro y responde por acción/actor/destinatario. No usar usuario_tiene_cargo como autorización final en estas acciones porque permite root sin cargo: comprobar autenticación/actividad y cargo de forma explícita según P-004-01. El helper global y su excepción permanecen intactos para las otras vistas. Un mixin acotado a gestión administrativa reutilizará LoginRequiredMixin y esta política, sin copiar dependencias de otro proyecto.

Evitar comparaciones de cargo duplicadas en templates: UserListView adjuntará permisos por destinatario para activar, desactivar y restablecer; cada vista comprobará la misma política. Mantener verification_users y los flags globales usados en navegación/Registro; esos flags no bastan para autorizar una fila.

| RF | Archivos existentes / propuestos | Cambio previsto | Evidencia prevista, no ejecutada |
|---|---|---|---|
| RF-004-01/05 | UsuarioApp/forms.py, views.py, urls.py; nueva plantilla restablecer_password.html | Formulario administrativo y GET/POST privado | Hash nuevo, campos/validadores, cero correo |
| RF-004-02/03/04 | Nuevo UsuarioApp/permissions.py; views.py; usuarios_lista.html | Política por actor/destinatario y activación/desactivación | Matriz cruzada de roles/estados, URL y HTML |
| RF-004-05/06 | forms.py, views.py | Reconfirmación, CSRF, caché, escritura mínima y errores | Rechazos sin cambios/secretos y sesiones A/B |
| RF-004-07 | Listado/formulario; layouts existentes, tokens y componentes reutilizados | Acciones coherentes con identidad 002/003 | Navegador claro/oscuro, teclado y móvil |
| Todos | UsuarioApp/tests.py y regresión homeApp | Tests significativos con core.test_settings | Resultados reales después de autorización |

La nueva plantilla propuesta irá en `templates/pages/UsuarioApp/restablecer_password.html`, extenderá `components/Layout/base_pages.html` y usará content_pages/crispy. El listado sigue en `templates/pages/UsuarioApp/usuarios_lista.html`, sobre base_extendido/content_main. Reutilizar controles, etiquetas, errores y botones semánticos de la [guía visual](../../docs/PERSONALIZACION_VISUAL.md); no copiar el diseño del otro proyecto ni rediseñar filas/paletas.

## Contratos y validación

- Ruta nueva propuesta: `/usuarios/<int:pk>/restablecer-contrasena/`, nombre `UserPasswordReset`. Búsqueda estática no encontró colisión en rutas actuales.
- GET: comprobar permiso de acción, buscar destinatario con 404, comprobar política por objeto y mostrar formulario; sin escrituras/correos. Aplicar never_cache a respuestas del formulario, incluidos errores. Marcar admin_password/new_password1/new_password2 como parámetros sensibles para los informes de error de Django; no registrar POST ni variables con contraseñas al manejar fallos.
- POST: CSRF middleware, comprobar actor autenticado/activo y política de acción antes de consultar el destinatario; obtener actor/destinatario vigentes y volver a comprobar cargo/protecciones, sin fiarse del GET anterior ni campos hidden. No aceptar un ID de operador desde el cliente.
- Formulario propuesto `AdministrativePasswordForm`: heredar SetPasswordForm, añadir `admin_password` con PasswordInput/autocomplete=current-password; campos new_password1/new_password2 con autocomplete=new-password. Reconfirmar usando check_password del operador actual. No requerir la contraseña anterior del destinatario. Los validadores reciben al destinatario; no guardar contenido recibido para repoblar campos.
- Restablecimiento: form.save(commit=False) para obtener el hash mediante Django; persistir únicamente password con update_fields. No tocar User completo ni Profile.save; ningún cambio de actividad/email/cargo/foto/MFA/modo visual.
- Activación/desactivación: conservar URLs/nombres actuales y POST; guardar únicamente is_active, aplicando las mismas reglas para ambas acciones confirmadas. Reenvío es idempotente y no cambia ningún otro atributo.
- Encerrar cada escritura en transaction.atomic. Si se usa select_for_update, bloquear User sin select_related a relaciones nullable: el patrón con joins nulos de la referencia no es portable. Cargar cargos por separado y comprobar nuevamente en POST. SQLite no demuestra bloqueo de filas de PostgreSQL ni serialización de cambios simultáneos de cargos; registrar ese límite, sin prometer una auditoría/concurrencia universal.
- Anónimo: login con retorno al flujo; autenticado no autorizado: PermissionDenied/403, usando página existente. Destinatario inexistente: 404 para actor autorizado. Activar/desactivar por GET: 405 para actor autorizado. Form inválido: 200 con errores; fallo de escritura previsto: 500 con mensaje contextual sin secretos, sin redirección de éxito. No ocultar excepciones inesperadas con catch general ni registrar request.POST.
- Invalidación de sesiones: utilizar el hash de autenticación existente de Django; al cambiar password, sesiones anteriores del destinatario dejan de autenticar al siguiente request. No llamar update_session_auth_hash sobre el destinatario en la sesión del administrador ni iniciar sesión como el destinatario. No purgar todas las sesiones ni desactivar MFA.

Referencias técnicas primarias consultadas para la versión declarada de la base: [SetPasswordForm](https://docs.djangoproject.com/en/5.1/topics/auth/default/#django.contrib.auth.forms.SetPasswordForm), [invalidación de sesiones](https://docs.djangoproject.com/en/5.1/topics/auth/default/#session-invalidation-on-password-change) y [límites de select_for_update](https://docs.djangoproject.com/en/5.1/ref/models/querysets/#select-for-update). La consulta no autoriza cambiar dependencias ni certifica la implementación futura.

## Plan de pruebas ejecutado y límites

Los casos siguientes se implementaron en 14 métodos nuevos de AdministracionUsuariosTests; dos métodos de gestión recibidos se ajustaron a la nueva política, conservando las pruebas de Registro. Suite completa: 57 métodos OK. MFA después del restablecimiento se verifica en subprocess con core.test_settings: allauth 0.62.1 registra modelos socialaccount al reanudar MFA y afecta cascadas posteriores; el proceso separado evita contaminación sin activar la integración ni alterar la configuración. El fallo observado y su corrección están en validation.md.

1. Matriz actor × destinatario × acción: ADMIN/MANAGER/RESTRICTED, root con y sin cargo, root con cargo inferior, staff sin cargo, perfiles/cargos ausentes, código desconocido, propia cuenta, destinatario root/ADMIN, anónimo e inactivos. Cubrir GET/POST directos y ausencia/presencia de controles por fila, en filtros activo/inactivo.
2. Restablecimiento válido para MANAGER/RESTRICTED, con/sin email y destinatario inactivo; contraseña previa incorrecta después, nueva válida; backend de correo que lanza si se invoca y cero correo generado. Cancelación y GET sin cambios.
3. Operador incorrecto/no usable, campos omitidos, nueva débil/similar/solo numérica/no coincidente, CSRF ausente/presente, IDs inexistentes/manipulados, permisos cambiados entre GET y POST; hashes/datos intactos ante denegación.
4. Dos clientes del destinatario ya autenticados y un tercero operador: invalidación en próxima petición privada de ambos destinatarios, operador continúa; login con contraseña nueva conserva desafío MFA existente cuando aplique.
5. Fallo de escritura simulado, repetición de activar/desactivar, conservación de atributos y cero llamada a Profile.save/fotos/preferencia. No afirmar atomicidad de cambios de cargos concurrentes con SQLite.
6. Regresión de UsuarioApp/homeApp incluyendo allauth login/cambio propio/recuperación de correo/MFA, navegación/Registro y modo visual. Adaptar expectativas de gestión de RenovacionUsuariosTests a la nueva denegación 403/jerarquía; conservar escenarios históricos equivalentes y añadir casos nuevos, no borrar pruebas para obtener verde. La evidencia anterior de 002 no se modifica.
7. Navegador con usuarios sintéticos: listado y formulario claro/oscuro, móvil/escritorio, nombres largos/errores, Tab/Enter/foco, cancelar y guardar. Verificar respuesta sin secretos y navegación con JS desactivado para el formulario. No usar captura de contraseñas reales.

Comandos aprobados ejecutados mediante .recovery-004/ejecutar.py con settings aislado (no se ejecutaron durante DOCUMENTAR):

```text
python manage.py check --settings=core.test_settings
python manage.py makemigrations --check --dry-run --settings=core.test_settings
python manage.py test UsuarioApp homeApp --settings=core.test_settings
python manage.py tailwind --settings=core.test_settings build
```

Regresión anterior: 43 métodos registrados para 003; no se vuelve a certificar ese resultado por inspección. Build requerido si cambia HTML/clases/fuentes. El nuevo permissions.py cae bajo la raíz UsuarioApp ya registrada en @source; no añadir una app o dependencia. Consultar [entorno](../../docs/ENTORNO_Y_VERIFICACION.md) y no usar configuración normal/.env/DB de desarrollo. .venv sigue documentado como roto; preparar verificación aislada solo al implementar, sin repararlo por esta spec.

## Migraciones, recuperación y límites

Sin cambios de modelos/esquema/datos iniciales ni migraciones nuevas. No aplicar 0002 de 003 a datos reales como consecuencia de este cambio. Antes de implementar: comprobar otra vez cambios locales y preparar recuperación acotada de archivos afectados, sin copiar secretos/bases/media personal. Recuperar código no restaura contraseñas/estados cambiados: no registrar hashes previos en logs ni inventar rollback de credenciales.

La jerarquía se aplica a los tres endpoints de gestión de UsuarioApp definidos aquí; no convierte Django admin, shell, registro o futuras apps en un sistema global de permisos. Otras superficies necesitan su propia spec si el producto quiere esa ampliación.

## Decisiones y documentos

P-004-02 recibida: misma jerarquía al activar/desactivar. P-004-01 recibida: ningún actor, incluido superusuario, actúa sin el cargo pertinente. No aparecieron decisiones críticas nuevas ni migraciones. La instrucción posterior de implementación del alcance completo se recibió y ejecutó; no repetirla. Quedan revisión manual del envío válido de credenciales por interfaz y aceptación funcional, sin dar por aplicada 0002 a la base existente.

Actualizar spec/plan/tasks, índice, PROYECTO, ESTADO_PROYECTO, DECISIONES, TRAZABILIDAD, ARQUITECTURA_BASE, OBSERVACIONES_BASE y VERIFICACION como propuesta ahora; al ejecutar registrar archivos/comandos/evidencia real en validation.md. No alterar AGENTS, constitución ni decisiones/evidencias históricas para legitimar resultados.
