# Nodo local MediaPipe de VIGIA

Piloto técnico, sin validación clínica. Clasifica supina/lateral izquierda/lateral derecha por referencias calibradas; devuelve indeterminada ante baja calidad, ambigüedad, oclusión o varias personas. La inmovilidad es una regla temporal experimental de 60/90/120 minutos; no una evaluación del riesgo clínico. Desde la [spec 012](../specs/012-deteccion-caidas/spec.md) detecta caídas con una regla determinista (RT-03), descrita más abajo; su sensibilidad y su tasa de falsos positivos se miden con el protocolo de este documento y no se dan por cumplidas sin esa medición.

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

HTTP solo se admite en loopback con opción explícita; para otro servidor se exige HTTPS. El nodo solicita autorización periódica, detiene lectura si pierde autorización/conexión y publica únicamente postura, calidad, versión, fecha, UUID y riesgo temporal. La API revalida revocación, propiedad y capacidad Premium; rechaza imágenes/campos adicionales y deduplica reintentos. No reinicia el reloj manual ni marca cuidados realizados.

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

Al confirmar, el nodo envía a `edge/observations` una observación con `risk="fall"` y `rule_version="fall-v1"`, con el mismo contrato y la misma credencial que el resto de las observaciones, sin imágenes ni coordenadas. Si el envío falla, la reintenta con el mismo `event_id` durante 110 s; el backend deduplica. El backend la guarda en el historial con `received_at`, registra la recepción en su log y `send_mobile_reminders` envía al dueño el aviso «Posible caída detectada», con prioridad alta en Android. El tiempo hasta el teléfono depende de cada cuánto se ejecute ese comando (P-012-01).

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

## Protocolo de prueba: 20 caídas simuladas

Objetivo: estimar la sensibilidad y la tasa de falsos positivos de la regla con la cámara y la ubicación reales. No es una validación clínica.

**Seguridad y consentimiento.** Participan solo adultos sanos que hayan dado su consentimiento escrito, sin pacientes. Las caídas se hacen sobre una colchoneta de al menos 5 cm, con un observador presente, controladas y desde la propia altura (sin saltos). Cualquiera puede detener la sesión. Los videos se guardan solo en local, fuera del repositorio, y se borran al terminar el análisis.

**Preparación.**

1. Cámara fija a 1,5–2,5 m de altura, nivelada, con la colchoneta y la cama completas en el cuadro y vista lateral u oblicua. Anotar el modelo de cámara, la resolución, los FPS y el equipo de cómputo.
2. Fijar los umbrales en un `caidas.json` y no cambiarlos durante la sesión. Si después se ajustan, repetir el protocolo completo.
3. Grabar cada prueba en un clip independiente que empiece con 3 s de pie y termine 10 s después de la acción.

**Pruebas positivas (20 caídas).** 5 hacia delante, 5 hacia atrás, 5 laterales a la izquierda y 5 a la derecha, repartidas entre al menos 2 participantes. En cada una, la persona permanece en la colchoneta ≥ 10 s sin incorporarse.

**Pruebas negativas (al menos 40 actividades, 10 de cada tipo).** Sentarse rápido en una silla, agacharse (sentadilla y recoger un objeto del suelo), acostarse en la cama a velocidad normal y dejarse caer sentado en la cama. Opcional: tenderse despacio en la colchoneta y caer y levantarse antes de `confirm_seconds` (lo esperado es que no haya alerta).

**Ejecución.** Para cada clip se puede usar `python -m edge.bench clip.mp4 --fall-config caidas.json --json`, o bien el nodo en vivo con `--log-file`, registrando a mano la hora de inicio de cada acción. Anotar en una tabla: clip, tipo, resultado esperado, caídas detectadas, segundo de impacto y de confirmación, y observaciones (oclusión, dos personas en el cuadro, etc.).

**Cálculo.**

- VP = caídas con al menos una detección dentro de los 15 s del clip; FN = caídas sin detección.
- FP = actividades negativas con al menos una detección; VN = actividades sin detección.
- **Sensibilidad** = VP / (VP + FN) = VP / 20. El objetivo del informe (≥ 90 %) exige 18 o más detecciones.
- **Tasa de falsos positivos** = FP / (FP + VN), con su conteo (por ejemplo, 2/40 = 5 %). El objetivo del informe es ≤ 5 %.
- Latencia de confirmación por caída = segundo de confirmación − segundo de inicio de la caída anotado en el video. Reportar la mediana y el máximo, y en vivo sumar el retraso de envío y de recepción del log del backend.
- Con 20 caídas el intervalo de confianza es amplio: 18/20 da un IC 95 % de Wilson de ≈ 70–97 %. Informarlo junto al porcentaje.

**Registro.** Se anotan en `specs/012-deteccion-caidas/validation.md` la fecha, el equipo, el `caidas.json`, la tabla resumida y las métricas, sin videos ni datos personales. Ninguna cifra se declara cumplida sin esta evidencia.

## Verificación

```bash
.venv-edge/bin/python -m unittest edge.test_posture edge.test_fall
.venv-edge/bin/python -m edge.smoke
```

Las pruebas geométricas y de caídas son sintéticas: verifican la regla con siluetas generadas, no la precisión con personas reales. La prueba de humo carga el modelo y procesa una imagen vacía; no acredita precisión con personas. Falta validar en hardware/cámara elegidos, calibración lateral, oclusiones, iluminación, tiempos y métricas acordadas con el responsable del proyecto.
