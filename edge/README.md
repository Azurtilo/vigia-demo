# Nodo local MediaPipe de VIGIA

Piloto técnico, sin validación clínica. Clasifica supina/lateral izquierda/lateral derecha por referencias calibradas; devuelve indeterminada ante baja calidad, ambigüedad, oclusión o varias personas. La inmovilidad es una regla temporal experimental de 60/90/120 minutos; no una evaluación del riesgo clínico. Desde la [spec 012](../specs/012-deteccion-caidas/spec.md) detecta caídas con una regla determinista (RT-03), descrita más abajo. Desde la [spec 017](../specs/017-robustez-caidas/spec.md) suma una segunda regla con la zona de la cama y avisa cuando la cámara no puede vigilar. Su sensibilidad y su tasa de falsos positivos se miden con el protocolo de este documento y no se dan por cumplidas sin esa medición.

## Preparación

Usar Python 3.12 y un entorno separado: `.venv-edge` en macOS y `.venv-edge-win` en Windows. Cada integrante lo crea localmente y nunca se sube al repositorio; los comandos por sistema operativo están en el [README raíz](../README.md#entorno-por-sistema-operativo). Instalar `edge/requirements.txt`.

El modelo oficial Pose Landmarker Lite va en `edge/models/pose_landmarker_lite.task`, que es la ruta por defecto de `--model`. La carpeta `edge/models/` está en `.gitignore`. Copiar el modelo desde `mobile/assets/models/pose_landmarker_lite.task` o descargarlo desde la [documentación de MediaPipe](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker). Las referencias de calibración se guardan en la misma carpeta, fuera del repositorio.

Los ejemplos usan el intérprete de macOS (`.venv-edge/bin/python`). En Windows, usar `.venv-edge-win\Scripts\python.exe`.

Antes de conectar una cámara, contar con consentimiento, ubicación y protocolo de prueba acordados. No se abrió una cámara personal durante esta entrega. Utilizar inicialmente un video de prueba autorizado, sin datos de pacientes reales.

Calibrar las tres posturas en la misma posición de cámara y contexto. Cada comando toma 60 observaciones válidas; repetir sustituyendo la postura y video. El JSON guarda solo referencias geométricas locales:

```bash
.venv-edge/bin/python -m edge.run --references edge/models/referencias.json --camera /ruta/video-autorizado.mp4 --calibrate supina
```

Desde una cuenta Premium, paciente → Monitoreo → Vincular nodo local. La credencial se muestra una sola vez; almacenarla fuera del repositorio mediante variable `VIGIA_NODE_TOKEN`. Hay un nodo activo por paciente en este piloto.

```bash
.venv-edge/bin/python -m edge.run --references edge/models/referencias.json --camera 0 --server http://127.0.0.1:8000 --allow-local-http --immobility-minutes 120
```

HTTP solo se admite en loopback con opción explícita; para otro servidor se exige HTTPS. El nodo renueva su autorización (lease de 15 s) en un hilo de envío aparte, detiene la lectura si la pierde o se le deniega y publica únicamente postura, calidad, versión, fecha, UUID y riesgo temporal. La API revalida revocación, propiedad y capacidad Premium; rechaza imágenes/campos adicionales y deduplica reintentos. No reinicia el reloj manual ni marca cuidados realizados.

## Detección de caídas (RT-03)

Código: [fall.py](fall.py). Usa los landmarks **normalizados de imagen** (`pose_landmarks`), no los de mundo: estos tienen el origen en la cadera y no permiten medir su altura. Solo procesa cuadros con una única persona. Las longitudes se expresan en **troncos** (distancia del punto medio de los hombros al de las caderas, el mayor valor de la ventana), por lo que no dependen de la distancia a la cámara.

1. **Impacto.** En la ventana temporal deben cumplirse a la vez:
   - velocidad de descenso del punto medio de la cadera ≥ `descent_velocity`;
   - descenso de la cadera respecto del punto más alto de la ventana ≥ `min_drop`;
   - ángulo del tronco respecto de la vertical ≥ `trunk_angle`;
   - relación ancho/alto del rectángulo de landmarks visibles ≥ `aspect_ratio`, y aumento respecto del mínimo de la ventana ≥ `aspect_change`.
2. **Confirmación.** Durante `confirm_seconds` el tronco sigue ≥ `recover_angle` y la cadera sigue al menos `stay_down_drop` bajo el nivel previo (y bajo `floor_hip_y`, si se calibró). Si se incorpora, se cancela. Si la señal falta más de `max_gap_seconds`, se reinicia sin aviso.
3. **Aviso.** Se emite una sola caída. No se emite otra hasta ver a la persona incorporada.

| Parámetro | Defecto | Unidad |
|---|---|---|
| `window_seconds` | 1.5 | s |
| `min_interval_seconds` | 0.2 | s (intervalo mínimo para estimar velocidad) |
| `descent_velocity` | 1.5 | troncos/s |
| `min_drop` | 0.8 | troncos |
| `trunk_angle` | 60 | grados (0 = de pie, 90 = tendido) |
| `aspect_ratio` | 1.0 | ancho/alto |
| `aspect_change` | 1.5 | factor |
| `confirm_seconds` | 5.0 | s |
| `recover_angle` | 45 | grados |
| `stay_down_drop` | 0.5 | troncos |
| `max_gap_seconds` | 2.0 | s |
| `min_visibility` | 0.5 | 0–1 |
| `floor_hip_y` | `null` | 0–1, altura de imagen (opcional) |

`python -m edge.fall` imprime los valores por defecto en JSON. Hay dos formas de cambiarlos: un archivo con `--fall-config caidas.json`, que admite solo las claves de la tabla, o un argumento por parámetro, como `--fall-confirm-seconds 4` o `--fall-trunk-angle 65`. Si se usan ambos, el argumento prevalece. Los valores inválidos detienen el arranque.

Por qué no alertan las actividades cotidianas (pruebas sintéticas de [test_fall.py](test_fall.py)): al sentarse o hacer una sentadilla, el tronco no pasa de unos 40°. Al inclinarse a recoger algo, la cadera no baja y la silueta sigue más alta que ancha. Al acostarse en una cama elevada, la cadera baja poco y despacio.

Límites conocidos: requiere una cámara fija y nivelada, con vista lateral u oblicua. Una caída hacia la cámara puede no ensanchar la silueta. Un colchón en el suelo o un desplome lento no se distinguen bien. Con dos personas en el cuadro no hay detección.

Al confirmar, el nodo envía a `edge/observations` una observación con `risk="fall"` y `rule_version="fall-v1"`, con el mismo contrato y la misma credencial que el resto de las observaciones, sin imágenes ni coordenadas. El envío ocurre en un hilo aparte con cola en memoria, de modo que un servidor lento no detiene el procesamiento de cuadros ni reinicia las reglas. Si el envío falla, se reintenta con backoff (1 → 30 s) y el mismo `event_id`; el backend deduplica. Las observaciones de riesgo se conservan hasta 55 min (el backend las acepta hasta 1 h) y las ordinarias 110 s. Si el lease vence durante una desconexión, la captura se detiene, pero lo pendiente se envía al reconectar con su hora original. El backend la guarda en el historial con `received_at`, registra la recepción en su log y envía el push en cuanto la guarda (D-051) a titular, familiares y cuidadores, con el texto genérico «VIGIA: alerta de riesgo, abre la app» (D-058) y prioridad alta en Android. `send_mobile_reminders` reintenta si ese envío falla.

## Zona de cama (spec 017)

Código: [bed.py](bed.py). Una persona que se desliza despacio de la cama al suelo no tiene un descenso rápido, así que la regla de impacto no la ve. Con una zona de cama calibrada, una segunda regla avisa cuando la persona queda **acostada fuera de la cama**:

1. **Punto de referencia.** El punto medio de las caderas; si están tapadas, el de los hombros; si tampoco, el promedio de nariz y orejas. El ángulo del tronco se mide con el mejor par disponible. Fuera de la cama con un solo punto, la postura es desconocida y el cuadro cuenta como «sin persona».
2. **Dentro o fuera.** Mayoría de los últimos `smoothing_frames` cuadros, para que un cuadro ruidoso no cambie el resultado. El borde del polígono cuenta como dentro.
3. **Seguimiento.** La persona tiene que haberse visto en la cama, o no acostada, sin saltos: una forma «acostada» que aparece de golpe en el suelo (una sábana, ropa) no es caída. Un salto es moverse más de `max_track_speed` troncos/s o perder la señal más de `track_gap_seconds`.
4. **Aviso.** Fuera de la cama y con el tronco ≥ `lying_angle` durante `lying_seconds` → observación `risk="fall"` con `rule_version="fall-bed-v1"`, por la misma vía que la regla de impacto.
5. **Un aviso por evento.** Si las dos reglas ven la misma caída, se envía una sola. No se envía otra hasta que la persona vuelve a la cama o se ve no acostada `rearm_upright_seconds` seguidos; cuadros sueltos entre huecos no cuentan.

Sin `--bed-config`, el nodo se comporta como en la spec 012.

**Calibración.** Con la cámara ya montada en su lugar definitivo:

```bash
.venv-edge/bin/python -m edge.bed --camera 0 --out edge/models/cama.json
```

Se abre una ventana local con la imagen en vivo: marca con clics las esquinas de la cama (3 a 8, en cualquier orden), Enter guarda, `r` reinicia y Esc cancela sin guardar. El archivo guarda solo las coordenadas normalizadas (`{"bed": [[x, y], …]}`); no se escribe ninguna imagen y el polígono no sale del equipo. **Si se mueve la cámara, hay que recalibrar**: el nodo no lo detecta. Después:

```bash
.venv-edge/bin/python -m edge.run --references edge/models/referencias.json --bed-config edge/models/cama.json --camera 0 --server https://…
```

| Parámetro | Defecto | Unidad |
|---|---|---|
| `lying_angle` | 60 | grados |
| `lying_seconds` | 5.0 | s |
| `smoothing_frames` | 8 | cuadros |
| `track_gap_seconds` | 1.5 | s |
| `max_track_speed` | 8.0 | troncos/s (por ajustar con el protocolo) |
| `rearm_upright_seconds` | 3.0 | s |
| `min_visibility` | 0.5 | 0–1 |

Se cambian como los de caídas: `--bed-settings cama-umbrales.json` o `--bed-lying-seconds 4`, etc. Los valores inválidos detienen el arranque.

## Estado de monitoreo (spec 017)

Código: [monitoring.py](monitoring.py). Un detector que no ve no debe fallar en silencio. El nodo calcula su estado y lo informa en cada renovación de autorización (D-073), solo como una palabra, sin imágenes, coordenadas ni brillo:

| Estado | Cuándo | Qué hacer |
|---|---|---|
| `normal` | Vigilando | — |
| `persona_no_visible` | La persona se vio y lleva `lost_seconds` sin verse (también una forma «acostada» sin seguimiento, o solo la cabeza fuera de la cama). Con dos personas en cuadro no se activa | Revisar que no haya caído fuera del cuadro; si sale a menudo, ampliar la vista |
| `poca_luz` | El brillo medio queda bajo `min_brightness` durante `low_light_seconds`; vuelve a `normal` con un 30 % más de luz | Dejar una luz tenue encendida de noche |
| `sin_imagen` | La cámara lleva `no_image_seconds` sin entregar cuadros. El nodo **no termina**: reintenta abrirla con espera creciente hasta 30 s | Revisar el cable o si otra aplicación tomó la cámara |

Si hay varios a la vez se informa el más grave: `sin_imagen` > `poca_luz` > `persona_no_visible`. La pausa por lease (plan, consentimiento, revocación) reinicia el estado: es una detención intencional, no una cámara ciega. Un video local que termina sí cierra el proceso.

En la app, el titular ve el estado en la tarjeta del nodo, y titular, familiar y cuidador ven la línea «Cámara: …» en la ficha (D-077). `persona_no_visible` y `sin_imagen` generan un push genérico; `poca_luz` solo se muestra (D-074). Si el nodo deja de renovar más de 60 s, el backend avisa «sin señal» (D-075). Esos avisos los envía `send_mobile_reminders`; la demora depende de su intervalo ([OPERACION.md](../docs/OPERACION.md)).

| Parámetro | Defecto | Unidad |
|---|---|---|
| `lost_seconds` | 10.0 | s |
| `no_image_seconds` | 10.0 | s |
| `min_brightness` | 0.12 | 0–1 (menor que 0,77) |
| `low_light_seconds` | 5.0 | s |

Se cambian con `--monitor-settings monitoreo.json` o `--monitor-lost-seconds 20`, etc.

## Instalación de la cámara

- **Altura:** 1,8 a 2,5 m, inclinada hacia abajo y nivelada (la vertical de la imagen debe ser la vertical real).
- **Vista:** diagonal u oblicua, desde una esquina de la pieza, que abarque **toda la cama y el suelo alrededor**. Si el suelo junto a la cama no se ve, una caída queda fuera de cuadro y solo llegará «persona no visible».
- **Luz:** de noche, una luz tenue (velador o luz de pasillo). MediaPipe no detecta a una persona a oscuras.
- **Equipo:** conectado a la corriente y sin suspensión. Una sola cámara activa por paciente.
- **Después de instalar:** calibrar las posturas y la zona de cama en esa posición, y revisar con la luz de noche que el estado sea `normal`.

## Casos difíciles conocidos

- **Persona tapada:** si las caderas no se ven, se usan los hombros, y si tampoco, la cabeza (regla de cama). La regla de impacto necesita hombros y caderas.
- **Sábanas o ropa en el suelo:** no generan caída porque no hay seguimiento desde la cama. El costo: si una caída real ocurre justo mientras MediaPipe perdió a la persona más de 1,5 s, llega como «persona no visible» y no como caída.
- **Caída en línea con la cámara:** si la persona queda tendida apuntando hacia la cámara, el tronco se ve vertical y ninguna regla la reconoce. Queda como limitación (D-076); la vista diagonal la reduce.
- **Dos personas en cuadro** (por ejemplo, el cuidador): no se evalúan caídas ni se informa «persona no visible».
- **Persona que se tiende a propósito fuera de la cama** (en el suelo o en un sillón fuera de la zona): la regla de cama puede avisar. Se mide en el protocolo.
- **Persona vista por primera vez ya tendida en el suelo** (el nodo arrancó después de la caída): no hay seguimiento previo y no se avisa caída.

## Métricas (KPI)

`edge.run` escribe en su log (stdout y, opcionalmente, `--log-file edge/models/nodo.log`):

- cada `--metrics-seconds` (60 por defecto): cuadros procesados y tiempo de inferencia por cuadro (promedio, p95 y máximo) y FPS;
- por cada caída: `event_id`, hora UTC estimada del impacto y hora de confirmación; después, la hora de envío y el retraso desde la confirmación.

El backend registra `Riesgo fall recibido` con `observed_at`, `received_at` y el retraso. `received_at` también aparece en `GET patients/<id>/observations`.

Benchmark sin servidor ni credencial, con los mismos umbrales `--fall-*`:

```bash
.venv-edge/bin/python -m edge.bench videos/caida_01.mp4 videos/caida_02.mp4 --json > edge/models/bench.json
```

Por cada video reporta los cuadros, los cuadros con una sola persona, la inferencia (promedio, p95 y máximo), los FPS de procesamiento (lectura + inferencia + regla, sin la pausa de 50 ms de `run.py`) y las caídas con su segundo de impacto y de confirmación. Usa la marca de tiempo del video, por lo que la regla ve el tiempo real de la grabación.

## Protocolo de prueba de caídas simuladas

Objetivo: estimar la sensibilidad y la tasa de falsos positivos de la regla con la cámara y la ubicación reales. No es una validación clínica.

**Seguridad y consentimiento.** Participan solo adultos sanos que hayan dado su consentimiento escrito, sin pacientes. Las caídas se hacen sobre una colchoneta de al menos 5 cm, con un observador presente, controladas y desde la propia altura (sin saltos). Cualquiera puede detener la sesión. Los videos se guardan solo en local, fuera del repositorio, y se borran al terminar el análisis.

**Preparación.**

1. Cámara fija a 1,5–2,5 m de altura, nivelada, con la colchoneta y la cama completas en el cuadro y vista lateral u oblicua. Anotar el modelo de cámara, la resolución, los FPS y el equipo de cómputo.
2. Fijar los umbrales en un `caidas.json` y no cambiarlos durante la sesión. Si después se ajustan, repetir el protocolo completo.
3. Grabar cada prueba en un clip independiente que empiece con 3 s de pie y termine 10 s después de la acción.

**Pruebas positivas (20 caídas).** 5 hacia delante, 5 hacia atrás, 5 laterales a la izquierda y 5 a la derecha, repartidas entre al menos 2 participantes. En cada una, la persona permanece en la colchoneta ≥ 10 s sin incorporarse.

**Pruebas negativas (al menos 40 actividades, 10 de cada tipo).** Sentarse rápido en una silla, agacharse (sentadilla y recoger un objeto del suelo), acostarse en la cama a velocidad normal y dejarse caer sentado en la cama. Opcional: tenderse despacio en la colchoneta y caer y levantarse antes de `confirm_seconds` (lo esperado es que no haya alerta).

**Ampliación de la spec 017 (RF-017-15), con la zona de cama calibrada.** Se agrega a las pruebas positivas: **5 deslizamientos lentos de la cama a la colchoneta**. Se agregan a las negativas, 5 de cada tipo: persona sentada junto a la cama 60 s, sábana o ropa que cae al suelo, persona tapada en la cama y habitación en penumbra. **Denominador fijado antes de ejecutar: 25 caídas y 60 actividades normales** (sustituye la propuesta 20/40 de D-053). Con 25 caídas, el objetivo de sensibilidad ≥ 90 % exige 23 o más detecciones (IC 95 % de Wilson para 23/25 ≈ 75–98 %), y el de falsos positivos ≤ 5 % admite hasta 3 de 60. Además, en la misma sesión y sin contarlas en esos totales, se prueban los estados de monitoreo: tapar la cámara, desconectarla, apagar la luz y cortar la red del nodo (T-017-13).

**Ejecución.** Para cada clip se puede usar `python -m edge.bench clip.mp4 --fall-config caidas.json --json`, o bien el nodo en vivo con `--log-file`, registrando a mano la hora de inicio de cada acción. Anotar en una tabla: clip, tipo, resultado esperado, caídas detectadas, segundo de impacto y de confirmación, y observaciones (oclusión, dos personas en el cuadro, etc.).

**Cálculo.**

- VP = caídas con al menos una detección dentro de los 15 s del clip; FN = caídas sin detección.
- FP = actividades negativas con al menos una detección; VN = actividades sin detección.
- **Sensibilidad** = VP / (VP + FN) = VP / 20. El objetivo del informe (≥ 90 %) exige 18 o más detecciones.
- **Tasa de falsos positivos** = FP / (FP + VN), con su conteo (por ejemplo, 2/40 = 5 %). El objetivo del informe es ≤ 5 %.
- Latencia de confirmación por caída = segundo de confirmación − segundo de inicio de la caída anotado en el video. Reportar la mediana y el máximo, y en vivo sumar el retraso de envío y de recepción del log del backend.
- Con 20 caídas el intervalo de confianza es amplio: 18/20 da un IC 95 % de Wilson de ≈ 70–97 %. Informarlo junto al porcentaje.

**Registro.** Se anotan en `specs/012-deteccion-caidas/validation.md` (y la ampliación en `specs/017-robustez-caidas/validation.md`) la fecha, el equipo, el `caidas.json`, la zona de cama usada, la tabla resumida y las métricas, separadas por regla (`fall-v1` y `fall-bed-v1`), sin videos ni datos personales. Ninguna cifra se declara cumplida sin esta evidencia.

## Verificación

```bash
.venv-edge/bin/python -m unittest edge.test_posture edge.test_fall edge.test_run
.venv-edge/bin/python -m edge.smoke
```

`edge.bench` acepta también `--bed-config` y reporta aparte el costo del brillo y de la regla de cama, y las caídas `fall-bed-v1`.

Las pruebas geométricas, de caídas, de la zona de cama y del estado de monitoreo son sintéticas: verifican la regla con siluetas generadas, no la precisión con personas reales. La prueba de humo carga el modelo y procesa una imagen vacía; no acredita precisión con personas. Falta validar en hardware/cámara elegidos, calibración lateral, oclusiones, iluminación, tiempos y métricas acordadas con el responsable del proyecto.
