# Operación: tareas programadas

Guía para quien administra el servidor de VIGIA. Hay dos tareas que dependen de ejecutarse periódicamente (spec 016, QA-2026-10-26-04); sin ellas, el sistema funciona pero deja de cumplir dos promesas.

| Tarea | Comando | Frecuencia | Qué pasa si no corre |
|---|---|---|---|
| Purga de datos vencidos | `manage.py purge_expired_data` | Una vez al día | No se cumplen los plazos de conservación de la política de privacidad (D-064, spec 014) |
| Avisos al teléfono | `manage.py send_mobile_reminders` | Cada 5 minutos (propuesta; P-012-01 sigue abierta) | No llegan los avisos de inmovilidad, de cuidados pendientes ni de la cámara (spec 017), ni el reintento de una caída cuyo push inmediato falló (D-051) |

La caída se avisa de inmediato al recibirla (D-051); esta tarea no la reemplaza, la respalda.

Desde la spec 017, la misma tarea avisa también cuando la cámara no puede vigilar: el nodo informa «persona no visible» o «sin imagen» (D-074), o deja de renovar su autorización por más de 60 s (D-075). Estos avisos **solo** salen con esta tarea, sin push inmediato: la demora real es de hasta 10 s en el nodo, más 60 s para el nodo sin señal, más el intervalo de la tarea. Con 5 minutos, un nodo apagado puede tardar hasta unos 6 minutos en avisarse. Se avisa una vez por episodio y por teléfono; un nodo detenido a propósito (plan, cupo, consentimiento o revocación) no genera aviso.

Los ejemplos usan marcadores: `<ruta-del-proyecto>` (carpeta raíz de VIGIA en el servidor) y `<ruta-de-logs>`. Los comandos usan la configuración de producción (`core.settings`, por defecto en `manage.py`). Nunca programes estas tareas con `core.mobile_demo_settings` ni con `core.test_settings`.

## 1. Purga de datos

Antes de programarla, simula la primera ejecución. `--dry-run` solo cuenta y no borra nada:

```bash
cd <ruta-del-proyecto>/web
<ruta-del-proyecto>/.venv/bin/python manage.py purge_expired_data --dry-run
```

La salida informa solo cantidades, por ejemplo: `Simulación (sin borrar): access_code_attempts=1, …, expired_sessions=21`. Haz un respaldo de la base antes de la primera purga real.

**Linux (cron)**, todos los días a las 03:15 del servidor:

```cron
15 3 * * * cd <ruta-del-proyecto>/web && <ruta-del-proyecto>/.venv/bin/python manage.py purge_expired_data >> <ruta-de-logs>/purga.log 2>&1
```

**Windows (Programador de tareas)**:

```bat
schtasks /Create /TN "VIGIA purga" /SC DAILY /ST 03:15 /TR "cmd /c cd /d <ruta-del-proyecto>\web && <ruta-del-proyecto>\.venv\Scripts\python.exe manage.py purge_expired_data >> <ruta-de-logs>\purga.log 2>&1"
```

**Comprobar que corre.** Cada purga real deja una línea `Purga realizada: …` en el log y un registro `PrivacyOperation` de tipo `purge` en la base, con las cantidades borradas. Para ver el último:

```bash
<ruta-del-proyecto>/.venv/bin/python manage.py shell -c "from PrivacidadApp.models import PrivacyOperation as P; print(P.objects.filter(kind='purge').order_by('-pk').values('pk', 'counts').first())"
```

Responde `None` si nunca se ha hecho una purga real. Si pasa más de un día sin registro nuevo, la tarea no está corriendo.

## 2. Avisos al teléfono

Requisitos antes de programarla:

1. Instalar `web/requirements-push.txt` en el entorno del servidor.
2. Credenciales de Firebase fuera del repositorio, mediante Application Default Credentials (D-054). Nunca se versionan.
3. Activar el envío con `VIGIA_PUSH_ENABLED = True`. **Hoy ese valor no está definido en ninguna configuración ni se lee del entorno.** Hay que decidir cómo se activa en producción antes de programar la tarea.

Sin esos requisitos, el comando termina con error y no envía nada:

```text
CommandError: VIGIA_PUSH_ENABLED está desactivado; no se enviaron notificaciones.
```

No programes la tarea hasta cumplirlos, o el log se llenará con ese error cada 5 minutos.

**Linux (cron)**, cada 5 minutos:

```cron
*/5 * * * * cd <ruta-del-proyecto>/web && <ruta-del-proyecto>/.venv/bin/python manage.py send_mobile_reminders >> <ruta-de-logs>/avisos.log 2>&1
```

**Windows (Programador de tareas)**:

```bat
schtasks /Create /TN "VIGIA avisos" /SC MINUTE /MO 5 /TR "cmd /c cd /d <ruta-del-proyecto>\web && <ruta-del-proyecto>\.venv\Scripts\python.exe manage.py send_mobile_reminders >> <ruta-de-logs>\avisos.log 2>&1"
```

Si dos ejecuciones se superponen, no hay avisos duplicados: cada envío reserva un recibo por dispositivo antes de llamar a Firebase. Un aviso que Firebase rechaza se reintenta en la siguiente ejecución, hasta una hora después del evento.

## 3. Si el hosting no admite tareas cada 5 minutos

Algunos planes de hosting solo permiten tareas diarias u horarias. En ese caso:

- programa la purga igual (es diaria);
- registra la limitación de los avisos y su efecto en `validation.md`. Con una tarea cada hora, un aviso de inmovilidad puede llegar hasta una hora tarde.

Decidir la cadencia definitiva es P-012-01.

## Estado

- Comandos probados en local contra la demo el 2026-10-26: `purge_expired_data --dry-run` informa cantidades sin borrar; `send_mobile_reminders` sin push activado termina con el error esperado.
- **Pendiente del propietario:** configurar las tareas en el servidor real y decidir cómo se activa `VIGIA_PUSH_ENABLED`.
