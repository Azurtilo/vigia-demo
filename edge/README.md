# Nodo local MediaPipe de VIGIA

Piloto técnico, sin validación clínica. Clasifica supina/lateral izquierda/lateral derecha por referencias calibradas; devuelve indeterminada ante baja calidad, ambigüedad, oclusión o varias personas. No detecta caídas. La inmovilidad es una regla temporal experimental de 60/90/120 minutos; no una evaluación del riesgo clínico.

## Preparación

Usar Python 3.12 y un entorno separado. Instalar `edge/requirements.txt`. Obtener el modelo oficial Pose Landmarker Lite desde la [documentación de MediaPipe](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker). En esta máquina se descargó `/tmp/vigia-pose-landmarker.task`; esa ruta es temporal.

Antes de conectar una cámara, contar con consentimiento, ubicación y protocolo de prueba acordados. No se abrió una cámara personal durante esta entrega. Utilizar inicialmente un video de prueba autorizado, sin datos de pacientes reales.

Calibrar las tres posturas en la misma posición de cámara y contexto. Cada comando toma 60 observaciones válidas; repetir sustituyendo la postura y video. El JSON guarda solo referencias geométricas locales:

```bash
.venv-edge/bin/python -m edge.run --model /tmp/vigia-pose-landmarker.task --references /tmp/vigia-referencias.json --camera /ruta/video-autorizado.mp4 --calibrate supina
```

Desde una cuenta Premium, paciente → Monitoreo → Vincular nodo local. La credencial se muestra una sola vez; almacenarla fuera del repositorio mediante variable `VIGIA_NODE_TOKEN`. Hay un nodo activo por paciente en este piloto.

```bash
.venv-edge/bin/python -m edge.run --model /tmp/vigia-pose-landmarker.task --references /tmp/vigia-referencias.json --camera 0 --server http://127.0.0.1:8000 --allow-local-http --immobility-minutes 120
```

HTTP solo se admite en loopback con opción explícita; para otro servidor se exige HTTPS. El nodo solicita autorización periódica, detiene lectura si pierde autorización/conexión y publica únicamente postura, calidad, versión, fecha, UUID y riesgo temporal. La API revalida revocación, propiedad y capacidad Premium; rechaza imágenes/campos adicionales y deduplica reintentos. No reinicia el reloj manual ni marca cuidados realizados.

## Verificación

```bash
.venv-edge/bin/python -m unittest edge.test_posture
.venv-edge/bin/python -m edge.smoke --model /tmp/vigia-pose-landmarker.task
```

Las cinco pruebas geométricas son sintéticas. La prueba de humo carga el modelo y procesa una imagen vacía; no acredita precisión con personas. Falta validar en hardware/cámara elegidos, calibración lateral, oclusiones, iluminación, tiempos y métricas acordadas con el responsable del proyecto.
