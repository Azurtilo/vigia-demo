# Plan técnico — 017 / Robustez de la detección de caídas

Spec: [spec.md](spec.md). Estado: aprobado para implementar T-017-01..12.
Autorización de implementación: T-017-01..12, 2026-10-27.

## Inspección de la base

Leídos el 2026-10-27 sobre `develop` limpio (`2fedd78`):

- **Edge.**
  - [edge/fall.py](../../edge/fall.py): `FallConfig`, `frame_features()` y `FallDetector` (`idle → confirming → alerted`). Un hueco mayor que `max_gap_seconds` llama a `reset()` sin avisar.
  - [edge/run.py](../../edge/run.py): `Uplink` (lease por `GET edge/status` cada 10 s y cola de observaciones en un hilo) y `Monitor` (postura, inmovilidad y caída; envía por la cola). En `main()`, `capture.read()` fallido → `break`, y el proceso termina. Con dos personas en cuadro, `landmarks` e `image_landmarks` quedan vacíos.
  - [edge/posture.py](../../edge/posture.py), [edge/bench.py](../../edge/bench.py), [edge/test_fall.py](../../edge/test_fall.py), [edge/test_run.py](../../edge/test_run.py).
  - `edge/requirements.txt` trae `opencv-contrib-python`, que tiene ventanas (highgui): sirve para calibrar en local.
- **Backend.**
  - [web/CuidadosApp/api/detection.py](../../web/CuidadosApp/api/detection.py): `EdgeView` bloquea al titular, revalida el nodo y `allowed()` (plan, cupo, consentimiento). En `GET` actualiza `last_seen_at`. `node_data()` calcula `connected` a 90 s.
  - [mobile_models.py](../../web/CuidadosApp/mobile_models.py): `DetectionNode`, `PushReceipt` único por (dispositivo, clave).
  - [push.py](../../web/CuidadosApp/push.py): `deliver()` reserva → envía fuera de transacción → confirma. `build()` aplica prioridad alta solo a `fall`.
  - [send_mobile_reminders.py](../../web/CuidadosApp/management/commands/send_mobile_reminders.py): `candidates()` junta los riesgos de `risk_patient_ids(user)` en la última hora.
  - [access.py](../../web/CuidadosApp/access.py): `recipients()` y `risk_patient_ids()`.
  - Última migración: `0009_pushreceipt_confirmed`.
- **App.** [patient_screen.dart](../../mobile/lib/features/patients/patient_screen.dart) muestra la tarjeta del nodo con `connected` y `last_seen_at`.
- **Prototipo `pose_app`.** `DetectorCaidas.kt`, `Geometria.kt`, `ConfigCaidas.kt`, `MonitoreoService.kt` y sus pruebas. De ahí se toma la lógica, no el código.

## Diseño propuesto

### Edge

**`edge/bed.py` (nuevo, Python puro).** Separado de `fall.py` porque la regla de impacto de 012 no cambia y esta tiene otro ciclo de vida.

- `BedZone`: carga y valida el polígono (RF-017-01), lo ordena por ángulo, y prueba si un punto está dentro, con el borde contando como dentro (ray casting más distancia al segmento, como `Geometria.puntoEnPoligono`). `python -m edge.bed --calibrate --camera 0 --out edge/models/cama.json` abre una ventana OpenCV local con la imagen en vivo. Se hacen clics en las esquinas: Enter guarda, Esc cancela y `r` reinicia. No escribe imágenes.
- `BedConfig`: dataclass con los parámetros `bed_*`, `track_*` y `rearm_upright_seconds`. Usa la misma validación y los mismos argumentos que `FallConfig`, generados como `--bed-*` desde el dataclass, y la misma carga JSON (`--bed-settings`). El polígono va en `--bed-config` (archivo de la zona).
- `body_reference(landmarks, frame_aspect, min_visibility)`: devuelve el punto de referencia y su tipo (caderas → hombros → cabeza), el ángulo del tronco con el mejor par y la escala del tronco (RF-017-04). Si falta el tronco, la escala es la última conocida en la sesión; sin escala previa, no se aplica el control de velocidad.
- `BedFallRule.observe(landmarks, now)` → `"fall"`, `""` o `"no_person"`. Hace el seguimiento continuo (RF-017-03), suaviza dentro/fuera por mayoría (RF-017-02) y lleva el temporizador de acostado. También expone `upright_since`/`in_bed` para el rearme.

**`edge/monitoring.py` (nuevo, Python puro).** `MonitorStatus` con tres detectores independientes:

- persona no visible (RF-017-06);
- sin imagen (RF-017-07);
- poca luz con histéresis × 1,3 (RF-017-08).

`update(now, *, frame, person, brightness)` y `tick(now)` devuelven el estado efectivo según la prioridad `sin_imagen > poca_luz > persona_no_visible > normal`, y un indicador de cambio. Recibe solo booleanos y el número de brillo, nunca cuadros.

**`edge/run.py`.**

- `Monitor` crea `BedFallRule` si hay `--bed-config`.
- Un **cerrojo común** (`fall_latched`) suprime la segunda caída del mismo evento. Se libera cuando `BedFallRule` informa que la persona volvió a la cama o lleva `rearm_upright_seconds` de pie (RF-017-05). Sin zona de cama no hay cerrojo, y la 012 queda idéntica.
- Brillo: `cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)` sobre el cuadro reducido a 160 px de ancho, `mean()/255`. Se mide en `bench.py` (RNF).
- Lectura fallida: si `--camera` es un índice, se libera la cámara, se espera con backoff (1 → 30 s) sin bloquear el `tick` del estado y se reabre. Si es un archivo, termina como hoy (RF-017-07).
- La pausa por lease (fail-closed) reinicia `MonitorStatus`. No es `sin_imagen`.
- `Uplink`:
  - `set_monitor_state(state)` guarda el último valor; si cambió, adelanta la renovación (`next_lease = now`) y despierta el hilo.
  - `_renew()` envía `params={"monitor_state": state}`.
  - Un backend anterior ignora el parámetro, así que es compatible.
- Log de cada cambio de estado y de cada caída `fall-bed-v1` con inicio y confirmación (RF-017-13).

**`edge/bench.py`.** Acepta `--bed-config` y reporta la latencia con y sin el cálculo de brillo y la regla de cama.

### Backend

**`DetectionNode`.** Campos aditivos:

- `monitor_state`: `CharField(max_length=24, blank=True, default="", choices=…)`; `""` = desconocido.
- `monitor_since`: `DateTimeField(null=True)`.

**`EdgeView`, `GET`.**

- Admite solo el parámetro `monitor_state`. Una clave desconocida, un valor fuera de la lista o más de un valor → 400 con mensaje en es-CL.
- Si el valor difiere del guardado, actualiza `monitor_state` y `monitor_since=now` en el mismo `update()` que `last_seen_at`.
- Sin parámetro, no toca el estado (nodo anterior).
- Todo ocurre después de `allowed()`: un nodo denegado no actualiza nada.

**`node_data()`.** Agrega `monitor_state` (`"desconocido"` si está vacío) y `monitor_since`. Sin cambios de permisos: lo ve quien hoy ve los nodos.

**`push.py`.**

- `MONITOR_TEXT = "VIGIA: revisa la cámara de monitoreo, abre la app."` Es genérico (D-058): no nombra al paciente ni el evento.
- `build()` ya aplica visibilidad privada a todo lo que tenga `risk`. Se pasa `risk="monitor"`, que no recibe prioridad alta porque esta solo aplica a `fall`.

**`send_mobile_reminders.candidates()`.** Agrega avisos de nodo, junto a los riesgos de `risk_patient_ids(user)`, para nodos activos:

- `persona_no_visible` o `sin_imagen`, con el nodo conectado (`last_seen_at` < 90 s) → clave `node:{id}:{state}:{monitor_since}`.
- Sin señal: `last_seen_at` < ahora − 60 s y dentro de la última hora → clave `node:{id}:offline:{last_seen_at}`. Requiere que `allowed(titular, patient)` no lance `PermissionDenied`, para no avisar de nodos detenidos a propósito por plan, cupo o consentimiento.
- Las claves identifican el episodio: `PushReceipt` impide repetir por dispositivo, y uno nuevo genera otra clave.
- Orden: caídas, luego avisos de nodo, luego inmovilidad y cuidados.
- Un episodio de más de 1 h no se anuncia (como `RISK_PUSH_MAX_AGE`), así un dispositivo nuevo no recibe avisos antiguos.

### App

En la tarjeta del nodo, con el nodo conectado y la detección en el plan, `subtitle` agrega el estado:

| Estado | Texto |
|---|---|
| `normal` | «Monitoreo activo» |
| `persona_no_visible` | «No se ve a la persona» |
| `sin_imagen` | «La cámara no entrega imagen» |
| `poca_luz` | «Poca luz: el monitoreo no es confiable» |
| `desconocido` | Sin cambio |

El icono pasa a advertencia en los tres estados ciegos. Los textos se extraen a una función pura para probarlos.

## Mapa por requisito

| RF | Archivos existentes / propuestos | Cambio previsto | Evidencia prevista |
|---|---|---|---|
| RF-017-01 | `edge/bed.py` (nuevo) | `BedZone`, validación y calibración local | `edge.test_fall` (zona): JSON inválidos, orden, borde |
| RF-017-02..04 | `edge/bed.py` | `body_reference`, `BedFallRule` | `edge.test_fall`: deslizamiento, de pie/sentado fuera, sábana, caderas tapadas, solo cabeza |
| RF-017-05 | `edge/run.py` (`Monitor`) | Cerrojo común y rearme | `edge.test_run`: un solo `fall` con ambas reglas; dos caídas con 3 s de pie; cuadro suelto; sin zona = 012 |
| RF-017-06..08 | `edge/monitoring.py` (nuevo), `edge/run.py` | `MonitorStatus`, brillo, reapertura de cámara | `edge.test_run`: tiempos, prioridad, histéresis, nunca visto, lease ≠ sin imagen, cámara que falla y vuelve |
| RF-017-09 | `edge/run.py` (`Uplink`), `api/detection.py`, `mobile_models.py`, migración `0010` | Parámetro en la renovación y guardado | `edge.test_run` (renovación anticipada con el parámetro); `CuidadosApp.test_mobile` (aceptado, 400, nodo anterior, nodo denegado) |
| RF-017-10 | `api/detection.py` (`node_data`), `patient_screen.dart` | Estado en la API y en la tarjeta | `test_access` (roles 013 y 404); prueba Flutter de los textos |
| RF-017-11/12 | `push.py`, `send_mobile_reminders.py` | Candidatos de nodo, claves por episodio | `CuidadosApp.test_push` con Firebase simulado: un aviso por episodio, `poca_luz` sin push, sin `risk_alerts`, consentimiento retirado, nodo revocado, sin señal |
| RF-017-13 | `edge/run.py` | Log | `edge.test_run` con `assertLogs`, sin coordenadas |
| RF-017-14/15 | `edge/README.md` | Guía, calibración, casos difíciles, protocolo | Revisión del documento y enlaces |

## Datos y contratos

- **Observación de caída de cama:** contrato de 7 claves sin cambios; `rule_version="fall-bed-v1"`. El backend ya la acepta (`risk="fall"`, `rule_version` de 1–80 caracteres).
- **Renovación:** `GET /api/v1/edge/status?monitor_state=<valor>`. La respuesta no cambia (`enabled`, `lease_seconds`, `server_time`).
- **Matriz de compatibilidad:**

  | Nodo / backend | Resultado |
  |---|---|
  | Anterior / nuevo | Estado `desconocido` |
  | Nuevo / anterior | Parámetro ignorado |
  | Anterior / anterior | Sin cambios |

  Un 400 en la renovación lo trata `Uplink` como un fallo transitorio y la captura se detiene al vencer el lease. Por eso el nodo solo envía valores de su lista cerrada, y existe una prueba que lo fija.
- **API móvil:** `nodes` agrega dos claves. La app instalada las ignora.
- **Zona de cama:** `{"bed": [[x, y], …]}` en `edge/models/` (ignorada por Git). Nunca se transmite.

## Permisos e interfaz

Sin permisos nuevos:

- El estado del nodo sigue `patient_for(user, pk, "manage_nodes")` en `NodesView`: en la tarjeta del nodo solo lo ve el titular, como hoy.
- **D-077 (P-017-05 A):** la respuesta del paciente (`patients/<id>`, permiso `view`, que ya tienen los tres roles) agrega `camera_state`. Es el estado agregado de sus nodos activos: el de mayor prioridad entre `sin_señal`, `sin_imagen`, `poca_luz`, `persona_no_visible` y `normal`, o `null` sin nodos activos. No incluye nombre, id ni `last_seen_at`. La ficha muestra una línea de solo lectura «Cámara: <estado>» a titular, familiar y cuidador (T-017-10).
- Los avisos usan `risk_patient_ids()` (titular, familiar y cuidador con acceso vigente, y el plan del titular con `risk_alerts`) y, para nodo sin señal, también `allowed()`.

El superusuario no recibe excepción en la API del nodo. La interfaz solo cambia el texto de la tarjeta.

## Migraciones y reversión

- `0010_detectionnode_monitor_state`: `AddField` × 2, con valores por defecto y sin datos.
- Reversión: `migrate CuidadosApp 0009`, que pierde solo el último estado, que se regenera con la siguiente renovación.
- Se prueba avance y reversión con `core.test_settings`. No se aplica a ninguna base real (pendiente 8 del estado).

## Plan de pruebas

Las pruebas Edge nuevas van en `edge/test_fall.py` (zona y regla de cama) y `edge/test_run.py` (estado, cerrojo, uplink). Así no cambia el comando de pruebas documentado en AGENTS.md, CLAUDE.md, CI y `qa-vigia`. Son secuencias sintéticas con reloj inyectado, como en la 012.

- **Escenarios traídos de `pose_app`:**
  - salir de la cama y caer;
  - deslizarse;
  - caminar fuera de la cama;
  - sábana que aparece en el suelo;
  - caderas tapadas con hombros visibles;
  - solo la cabeza;
  - cambio de punto de referencia sin salto;
  - dos caídas con rearme;
  - cuadro de pie suelto entre vacíos;
  - poca luz con histéresis;
  - cámara sin cuadros y recuperación;
  - persona nunca vista.
- **Regresión:** todas las pruebas de 012 sin tocar, y el caso «sin `--bed-config`, mismo resultado que hoy».
- **Backend:**
  - renovación con estado válido, inválido, duplicado y ausente;
  - nodo revocado, sin plan o sin consentimiento (no se actualiza);
  - `node_data` por rol;
  - push por episodio con Firebase simulado y `VIGIA_PUSH_INLINE`;
  - nodo sin señal sí/no según `allowed()`;
  - episodio de más de 1 h.
- **Migración:** `makemigrations --check` tras crear `0010`, y avance y reversión.
- **App:** `flutter analyze`, y una prueba de textos y del icono por estado.
- **Rendimiento:** `edge.bench` con el mismo video antes y después (sintético mientras no exista video del protocolo; se registra que no mide el KPI).
- **Fuera del entorno automático (se registra como pendiente):**
  - calibración con ventana y cámara real;
  - ejecución en vivo de `edge.run` con la cámara;
  - push real (D-054).

## Riesgos, alternativas y dependencias

- **Falsos positivos de la regla de cama:** alguien que se tiende en el suelo o en un sillón fuera de la zona. Se mitiga con el seguimiento continuo y se mide con el protocolo ampliado (RF-017-15). El umbral `max_track_speed` (8 troncos/s propuesto) se ajusta ahí.
- **Escala del tronco con oclusión:** se usa la última conocida. Sin ella, no se aplica el control de velocidad: es un riesgo de aceptar un objeto como persona, y queda cubierto por la exigencia de antecedente válido.
- **Avisos de «persona no visible» con la persona fuera de cuadro por motivos normales** (fue al baño): son esperables. El texto dice «revisa la cámara» y no «caída». Si molestan, se sube `lost_seconds`; queda registrado como límite.
- **Demora del aviso de nodo sin señal y del monitoreo ciego:** 60 s más la cadencia de `send_mobile_reminders` (5 min propuestos en [OPERACION.md](../../docs/OPERACION.md)). No hay push inmediato para estos avisos: no son caídas y D-074 los deja sin prioridad alta. Se documenta.
- **Un 400 en la renovación detiene la captura:** se mitiga con la lista cerrada en el nodo y una prueba de contrato compartida (los mismos valores en ambos lados).
- **Alternativa descartada:** portar `DetectorCaidas.kt` al plugin `vigia_pose` (D-057, iOS).
- Sin paquetes nuevos: OpenCV y MediaPipe ya están en `edge/requirements.txt`.

## Documentos afectados

- **Durante la implementación:**
  - [edge/README.md](../../edge/README.md): zona de cama, calibración, parámetros nuevos, estados de monitoreo, guía de instalación, casos difíciles y protocolo ampliado.
  - [docs/OPERACION.md](../../docs/OPERACION.md): `send_mobile_reminders` también avisa del estado de los nodos; efecto de la cadencia.
  - `validation.md` (nuevo, con resultados reales).
- **Al cerrar:** `specs/README.md`, [ESTADO_PROYECTO.md](../../docs/ESTADO_PROYECTO.md) y [TRAZABILIDAD.md](../../docs/TRAZABILIDAD.md) (RT-03 y HU-05 siguen «Parcial» o «Sin evidencia» hasta el protocolo y Firebase). La política de privacidad no cambia: no se agregan datos personales nuevos.

## Decisiones para implementar

Ninguna bloqueante: P-017-01..05 quedaron resueltas (D-073..D-077). Valores ajustables tras el protocolo: `max_track_speed`, `lost_seconds` y `min_brightness`. Esta fase termina antes del código.
