# 012 — Detección de caídas en el nodo Edge (RT-03)

Estado: implementada en la misma sesión; verificación técnica sintética registrada en [validation.md](validation.md). Fecha: 2026-10-22.
Módulo: nodo `edge/` + `CuidadosApp` (endpoint `edge/observations`, historial y avisos). Fuente: pedido del usuario 2026-10-22 («El nodo Edge hoy NO detecta caídas… Te autorizo crear specs/012-deteccion-caidas/ (spec, plan, tasks) e implementarla completa en la misma sesión»).
Implementación autorizada: SÍ, en el mismo mensaje (2026-10-22). Sin producción, sin migración real, sin cámara personal. Revisión del usuario: pendiente.

## Problema y resultado

El informe exige RT-03 (detectar caídas por cambio brusco de altura) y HU-05 (familiar recibe push ante eventos de riesgo). Hasta 011 el nodo Edge solo clasifica postura en cama y detecta inmovilidad; `edge/README.md` declaraba «No detecta caídas».

Resultado esperado: el nodo aplica una regla determinista sobre una ventana de landmarks de MediaPipe, confirma que la persona quedó en el suelo y envía una observación `risk="fall"` con solo metadatos; el backend la guarda en el historial del paciente y la incluye en la misma vía de avisos push del dueño. Además, el nodo y el backend registran tiempos para medir los KPI del informe, y existe un protocolo reproducible para medir sensibilidad y falsos positivos.

## Actores y permisos

| Acción / datos | Anónimo | Nodo con credencial activa | Dueño del paciente (Premium) | Otro usuario | Superusuario |
|---|---|---|---|---|---|
| Enviar observación `fall` | 401 | Sí, si el paciente está habilitado y el plan incluye detección (igual que 010) | No aplica (no usa credencial de nodo) | 401 | Sin excepción: necesita credencial de nodo |
| Ver caída en historial | 401 | No | Sí (`patients/<id>/observations`) | 404 | Igual que la API móvil vigente |
| Recibir push de caída | — | — | Sí, si `risk_alerts` del plan y dispositivo activo | No | Igual que cualquier usuario |

Nodo revocado, plan vencido o paciente archivado: rechazo 401/403 como en 010, sin cambios.

## Alcance y exclusiones

Incluye: regla de caída en `edge/fall.py`, umbrales configurables por argumento o JSON, integración en `edge/run.py`, envío con reintento idempotente, métricas de inferencia en el log, `edge/bench.py`, riesgo `fall` en el backend (validación, historial, log de recepción, push), texto en la app móvil, pruebas sintéticas y protocolo de prueba de 20 caídas.

No incluye: validación clínica, entrenamiento de modelos, detección con varias personas en cuadro, cámaras no niveladas, almacenamiento de imágenes, envío inmediato de push en la petición del nodo (la vía existente es el comando periódico `send_mobile_reminders`; sustituido el 2026-10-25 por D-051, pendiente de tareas), ni declarar cumplidos los RNF sin medición en hardware real.

## Historias y flujo

1. El nodo procesa cada cuadro con MediaPipe (VIDEO). Si hay exactamente una persona, entrega a la regla los landmarks normalizados de imagen.
2. La regla detecta un **impacto** cuando, en la ventana temporal, coinciden descenso rápido de la cadera, caída suficiente de altura, tronco inclinado, silueta más ancha que alta y aumento de la relación de aspecto.
3. Durante la **confirmación** (N segundos) la persona debe seguir abajo y sin incorporarse. Si se incorpora o se pierde la señal más de lo tolerado, se cancela sin aviso.
4. Al confirmarse se encola una observación `risk="fall"`; un hilo de envío la entrega sin bloquear el procesamiento de cuadros. Si el envío falla, se reintenta con backoff y el mismo `event_id` hasta que expira la ventana de aceptación del backend (corrección 2026-10-22, RF-012-11/12).
5. El backend la valida, la guarda con `received_at`, registra la recepción en el log y el comando de avisos la incluye con un texto específico.

## Requisitos funcionales

- RF-012-01: CUANDO en la ventana temporal se cumplen a la vez velocidad de descenso de la cadera ≥ umbral, caída de altura ≥ umbral, ángulo del tronco ≥ umbral, relación de aspecto ≥ umbral y aumento de la relación de aspecto ≥ umbral, EL SISTEMA marca un impacto candidato.
- RF-012-02: CUANDO un impacto candidato se mantiene durante `confirm_seconds` (tronco inclinado y cadera abajo del nivel previo), EL SISTEMA emite una única caída; SI la persona se incorpora o la señal falta más de `max_gap_seconds`, ENTONCES cancela sin emitir.
- RF-012-03: Tras emitir, EL SISTEMA no emite otra caída hasta observar a la persona incorporada o perder la señal.
- RF-012-04: Todos los umbrales son configurables por argumento `--fall-*` o archivo JSON `--fall-config`; los valores por defecto están documentados; valores fuera de rango o claves desconocidas se rechazan al iniciar.
- RF-012-05: AL confirmar una caída, el nodo envía a `POST /api/v1/edge/observations`, con la autenticación de nodo existente, una observación con `risk="fall"` y el mismo contrato de metadatos (sin imágenes ni coordenadas); reintenta con el mismo `event_id` si falla el envío.
- RF-012-11 (2026-10-22, QA-2026-10-22-01): el envío y la renovación de autorización ocurren en un hilo aparte con cola en memoria; una demora o caída de la red no retrasa el procesamiento de cuadros ni reinicia la regla de caída ni la de inmovilidad. Solo la expiración o denegación de la autorización (lease) detiene la captura (fail-closed) y reinicia las reglas.
- RF-012-12 (2026-10-22, QA-2026-10-22-01): las observaciones pendientes se conservan durante la desconexión y se envían al reconectar con su `observed_at` y `event_id` originales, con backoff exponencial (1 → 30 s) y prioridad a los riesgos. Las observaciones ordinarias expiran a los 110 s; las de riesgo (`fall`, `immobility`) a los 55 min, y el backend las acepta hasta 1 h de antigüedad. Un rechazo permanente (400/409/413) descarta la observación con log de error.
- RF-012-06: El backend acepta `risk="fall"` también con postura `indeterminada`, sigue rechazando `immobility` con `indeterminada` y cualquier otro riesgo; guarda la observación y la expone en el historial del paciente con `received_at`.
- RF-012-07: El comando de avisos incluye las caídas recientes del dueño con un texto específico, sin datos del paciente, con prioridad alta en Android y sin duplicar avisos por dispositivo. Corrección 2026-10-22 (QA-2026-10-22-02): «recientes» = recibidas en la última hora (`received_at`), no observadas en los últimos 2 minutos; todo riesgo (`fall` o `immobility`) sin `PushReceipt` en el dispositivo se reintenta en cada ejecución hasta que FCM lo acepte, y el recibo impide el duplicado.
- RF-012-08: El nodo registra en su log el tiempo de inferencia por cuadro (promedio y p95 por intervalo) y la marca de tiempo de impacto y confirmación de cada caída; el backend registra la hora de recepción y el retraso respecto de `observed_at`.
- RF-012-09: `edge/bench.py` procesa uno o más videos locales sin servidor y reporta latencia de inferencia (promedio, p95, máx.), FPS de procesamiento y conteo de caídas.
- RF-012-10: Las secuencias sintéticas de sentarse, agacharse (sentadilla e inclinarse) y acostarse en la cama no disparan caída; la secuencia de caída sí, una vez.

Ajustes del 2026-10-25 (decisiones D-051, D-057, D-058, D-063 y hallazgos QA-2026-10-22-09/16):

- RF-012-07, precisión (D-058, D-063): el texto del push de riesgo es genérico e igual para caída e inmovilidad («VIGIA: alerta de riesgo, abre la app»), con visibilidad privada en la pantalla de bloqueo de Android y prioridad alta solo para caída. Lo reciben el titular, los familiares y los cuidadores con acceso vigente (spec 013), según el plan del titular.
- RF-012-13 (D-051): CUANDO el backend guarda una caída nueva, EL SISTEMA intenta el push a los destinatarios después de confirmar la transacción y en segundo plano, sin demorar la respuesta al nodo. El comando periódico `send_mobile_reminders` queda como reintento. La inmovilidad sigue solo por el comando (decisión del propietario, 2026-10-25: «prefiero solo caídas, al menos por ahora»).
- RF-012-14 (QA-09): EL SISTEMA no llama a FCM dentro de una transacción con filas bloqueadas. Reserva el recibo por dispositivo en una transacción corta, envía fuera de ella y confirma el recibo al aceptar FCM; si el envío falla, libera la reserva para reintentar. Una reserva sin confirmar por más de 2 minutos se considera abandonada. Ningún aviso se duplica por dispositivo entre el envío inmediato y el comando.
- RF-012-15 (D-057): la app Android exige como mínimo Android 8.0 (API 26).
- RF-012-16 (QA-16): en el historial móvil de observaciones, una caída se titula «Posible caída» aunque la postura sea indeterminada.

## Datos y reglas

Coordenadas: landmarks normalizados de imagen (`x`, `y` en [0, 1], `y` hacia abajo). `x` se multiplica por la relación ancho/alto del cuadro para medir en unidades de altura de imagen. La escala corporal es la mayor longitud de tronco (punto medio hombros → punto medio caderas) en la ventana, de modo que los umbrales no dependen de la distancia a la cámara.

| Parámetro | Defecto | Unidad | Significado |
|---|---|---|---|
| `window_seconds` | 1.5 | s | Ventana temporal analizada para el impacto |
| `min_interval_seconds` | 0.2 | s | Intervalo mínimo para estimar velocidad (evita ruido de un cuadro) |
| `descent_velocity` | 1.5 | troncos/s | Velocidad mínima de descenso del punto medio de la cadera |
| `min_drop` | 0.8 | troncos | Descenso mínimo de la cadera respecto del punto más alto de la ventana |
| `trunk_angle` | 60 | grados | Ángulo mínimo del tronco respecto de la vertical para considerar «tendido» |
| `aspect_ratio` | 1.0 | ancho/alto | Relación mínima del rectángulo de landmarks visibles |
| `aspect_change` | 1.5 | factor | Aumento mínimo de la relación de aspecto respecto del mínimo de la ventana |
| `confirm_seconds` | 5.0 | s | Tiempo que debe seguir en el suelo sin incorporarse |
| `recover_angle` | 45 | grados | Si el tronco baja de este ángulo, se considera incorporado |
| `stay_down_drop` | 0.5 | troncos | La cadera debe seguir al menos esto bajo el nivel previo al impacto |
| `max_gap_seconds` | 2.0 | s | Falta de señal tolerada; más tiempo cancela/reinicia |
| `min_visibility` | 0.5 | 0–1 | Visibilidad y presencia mínimas por landmark |
| `floor_hip_y` | `null` | 0–1 | Opcional: la cadera debe quedar bajo esta altura de imagen (calibración de suelo) |

Contrato de la observación de caída: el mismo de 010 (`event_id`, `observed_at`, `posture`, `confidence`, `model_version`, `rule_version`, `risk`) con `risk="fall"` y `rule_version="fall-v1"`. `posture`/`confidence` son los del clasificador calibrado en ese cuadro (puede ser `indeterminada`, 0). Sin campos nuevos.

Base de datos: se añade la opción `("fall", "Caída")` a `PostureObservation.risk` (migración aditiva de `choices`, sin cambio de columna). `received_at` ya existía.

## Criterios de aceptación

| RF | Dado / cuando | Entonces |
|---|---|---|
| RF-012-01/02 | Secuencia sintética de caída lateral y 8 s en el suelo | Una caída emitida ≈ `confirm_seconds` después del impacto |
| RF-012-02 | Caída y se levanta a los 2 s | Sin caída |
| RF-012-02 | Caída y la señal se pierde 3 s | Sin caída |
| RF-012-03 | Sigue en el suelo 30 s tras emitir | Solo una caída |
| RF-012-10 | Sentarse rápido, sentadilla, inclinarse, acostarse lento y rápido en la cama | Ninguna caída |
| RF-012-04 | JSON con clave desconocida o umbral negativo | Error al iniciar |
| RF-012-05/06 | Nodo envía `fall` con postura `indeterminada` | 201, aparece en historial con `risk="fall"` y `received_at` |
| RF-012-06 | Nodo envía `immobility` con `indeterminada` o riesgo `otro` | 400 |
| RF-012-07 | Caída reciente y dispositivo activo con Premium | Un push con texto de caída; segunda ejecución no duplica |
| RF-012-08/09 | `edge.metrics` con muestras conocidas; `bench.py --help` | Promedio/p95 correctos; script ejecutable |
| RF-012-11 | Servidor que tarda 2,5 s o 5 s en responder durante una caída | La caída se confirma y se entrega una vez; ningún cuadro espera a la red |
| RF-012-12 | Red caída y recuperada; respuesta perdida tras guardar | Entrega al reconectar con `observed_at` original; reintento sin duplicado |
| RF-012-07 | Caída de hace 30 min recibida tarde; FCM falla dos veces | Push de caída y de inmovilidad una vez cada uno en la ejecución siguiente |
| RF-012-07 | Push de caída o inmovilidad | Texto genérico, visibilidad privada; prioridad alta solo en caída; titular, familiar y cuidador lo reciben |
| RF-012-13 | El nodo envía una caída con push habilitado | El push sale tras confirmar la transacción, la respuesta al nodo no espera a FCM y el comando posterior no lo repite |
| RF-012-14 | FCM tarda o falla durante el envío | Ninguna fila bloqueada durante la llamada; la reserva se libera y el reintento envía una vez |
| RF-012-15 | `build.gradle.kts` | `minSdk` 26 |
| RF-012-16 | Observación `fall` con postura indeterminada en la app | Título «Posible caída» |

## No funcionales

- Privacidad: ningún cuadro sale del nodo; la observación de caída no lleva coordenadas.
- Objetivos del informe (alerta ≤ 10 s, inferencia < 100 ms, sensibilidad ≥ 90 %, FP ≤ 5 %): **no se declaran cumplidos**. Con los valores por defecto, el nodo confirma ≈ 5–6,5 s después del inicio de la caída; el tiempo total hasta el teléfono depende además de FCM (desde el 2026-10-25 el push sale al recibir la caída, RF-012-13; antes dependía de la frecuencia de `send_mobile_reminders`). Las cifras reales se registran con `bench.py` y el protocolo de `edge/README.md`.

## Compatibilidad

Se preservan clasificación de postura, regla de inmovilidad, contrato y autenticación del nodo (010), deduplicación por `event_id`, observaciones del teléfono (sin riesgo) y el comando de avisos. Spec relacionada: [010](../010-aplicacion-movil/spec.md), [011](../011-ecosistema-instalable/spec.md).

## Supuestos y decisiones pendientes

- Supuesto: cámara fija aproximadamente nivelada (vertical de la imagen ≈ vertical real) y vista lateral u oblicua del área. Con la persona cayendo hacia la cámara (vista de frente al eje del cuerpo) la relación de aspecto puede no superar el umbral: limitación conocida.
- Supuesto: una cama elevada separa «acostarse» de «caer»; un colchón o futón en el suelo puede confundirse con una caída lenta, pero la velocidad lo filtra.
- P-012-01 (pendiente del responsable): frecuencia de ejecución de `send_mobile_reminders` en el despliegue (necesaria ≤ ~3 s para el objetivo de 10 s) o un envío inmediato en la recepción. No se decide en esta spec. **Resuelta 2026-10-25 (D-051):** push inmediato tras guardar la caída (`transaction.on_commit`, timeout corto, deduplicación por `PushReceipt`); el comando periódico queda como reintento.
- P-012-02 (pendiente): ajustar umbrales con los resultados del protocolo de 20 caídas. **Resuelta 2026-10-25 (D-053):** protocolo con voluntarios, colchoneta y video autorizado procesado solo en local, más actividades normales para medir falsos positivos. El denominador se fija antes de ejecutarlo (propuesta 20 caídas / 40 actividades). Pendiente de ejecución.
- QA-14 **resuelta 2026-10-25 (D-058):** el push de riesgo usa un texto genérico con visibilidad privada en la pantalla de bloqueo, en lugar de «Posible caída». Precisa RF-012-07; pendiente de tareas.
- RNF disponibilidad (D-060): objetivo de diseño no medido; no aplica medición en esta spec.

## Revisión y cambios

2026-10-22: creada e implementada por autorización explícita del usuario en el mismo mensaje. Aceptación funcional pendiente.

2026-10-22 (posterior): correcciones de la revisión [QA_2026-10-22](../../docs/QA_2026-10-22.md) autorizadas por el usuario: RF-012-11/12 nuevos y RF-012-07 precisado (QA-01, QA-02, QA-03). Decisión [D-012-02](../../docs/DECISIONES.md).

2026-10-25: el propietario resuelve P-012-01 (D-051), P-012-02 (D-053) y QA-14 (D-058). Los cambios de RF y las tareas fechadas se documentan en una fase posterior; no hay autorización de implementación.

2026-10-25 (posterior): RF-012-07 precisado y RF-012-13..16 añadidos (D-051, D-057, D-058, D-063, QA-09, QA-16). Tareas T-012-13..21 en tasks.md. Implementación pendiente de autorización.
