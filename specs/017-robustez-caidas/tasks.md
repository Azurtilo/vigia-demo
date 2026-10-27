# Tareas — 017 / Robustez de la detección de caídas

Spec: [spec.md](spec.md). Plan: [plan.md](plan.md).
Estado: en implementación. Implementación autorizada: SÍ, T-017-01..12 (2026-10-27).
No ejecutar tareas de código por el hecho de aparecer aquí. Rama prevista: `feature/017-robustez-caidas` desde `develop`, un commit por tarea y PR hacia `develop` (D-059).

## Edge

- [ ] T-017-01 — Rama y línea base.
  - RF: todos (regresión).
  - Depende de: autorización.
  - Archivos previstos: ninguno.
  - Hecho cuando: la rama existe desde `develop`, y las suites Django, Edge y Flutter pasan sin cambios. Se registran los conteos y un `edge.bench` de referencia con el mismo video sintético en `validation.md`.
- [ ] T-017-02 — Zona de cama y calibración local.
  - RF: RF-017-01.
  - Depende de: T-017-01.
  - Archivos previstos: `edge/bed.py` (nuevo: `BedZone`, `python -m edge.bed --calibrate`), `edge/test_fall.py`.
  - Hecho cuando: las pruebas cubren JSON con menos de 3 vértices, vértice fuera de 0–1, clave desconocida, polígono degenerado, esquinas en cualquier orden y punto sobre el borde. Además, la calibración no escribe imágenes, cosa que se comprueba revisando el código. La prueba con ventana y cámara queda en T-017-13.
- [ ] T-017-03 — Punto de referencia y regla «acostado fuera de la cama».
  - RF: RF-017-02, RF-017-03, RF-017-04.
  - Depende de: T-017-02.
  - Archivos previstos: `edge/bed.py` (`BedConfig`, `body_reference`, `BedFallRule`), `edge/test_fall.py`.
  - Hecho cuando: pasan las secuencias sintéticas:
    - deslizarse de la cama (una caída ≈ 5 s);
    - de pie o sentada fuera de la cama 60 s (sin caída);
    - acostada 3 s y se incorpora (sin caída);
    - sábana que aparece en el suelo (sin caída, «sin persona»);
    - caderas tapadas con hombros visibles (caída);
    - solo la cabeza (sin caída);
    - cambio de punto de referencia sin salto.

    Las pruebas de 012 pasan sin modificarse.
- [ ] T-017-04 — Integración en `Monitor`, cerrojo común y argumentos.
  - RF: RF-017-05, RF-017-13 (caídas).
  - Depende de: T-017-03.
  - Archivos previstos: `edge/run.py`, `edge/bench.py`, `edge/test_run.py`.
  - Hecho cuando: las pruebas comprueban:
    - un solo `fall` cuando cumplen las dos reglas;
    - dos caídas separadas por 3 s de pie;
    - un cuadro de pie suelto entre vacíos que no rearma;
    - `rule_version="fall-bed-v1"` en la observación;
    - log sin coordenadas;
    - sin `--bed-config`, la misma secuencia de observaciones que hoy.

    `--bed-*` inválidos detienen el inicio con un mensaje en es-CL, y `edge.bench --bed-config` reporta la latencia.
- [ ] T-017-05 — Estado de monitoreo: persona no visible, sin imagen y poca luz.
  - RF: RF-017-06, RF-017-07, RF-017-08, RF-017-13 (estados).
  - Depende de: T-017-01 (independiente de T-017-02..04).
  - Archivos previstos: `edge/monitoring.py` (nuevo), `edge/run.py`, `edge/test_run.py`.
  - Hecho cuando: las pruebas con reloj inyectado comprueban:
    - 10 s sin persona tras haberla visto, y nunca vista;
    - dos personas no cuentan como no visible;
    - cámara que no entrega cuadros 12 s y vuelve, sin que el proceso termine;
    - video de archivo que termina y cierra el proceso;
    - lease denegado sin `sin_imagen`;
    - poca luz con histéresis y oscilación en el umbral;
    - prioridad entre estados.

    `edge.bench` muestra el costo del cálculo de brillo.
- [ ] T-017-06 — Envío del estado en la renovación.
  - RF: RF-017-09 (nodo).
  - Depende de: T-017-05.
  - Archivos previstos: `edge/run.py` (`Uplink`), `edge/test_run.py`.
  - Hecho cuando: las pruebas con sesión simulada comprueban:
    - el parámetro `monitor_state` en cada renovación;
    - la renovación adelantada al cambiar de estado;
    - solo valores de la lista cerrada;
    - un servidor que ignora el parámetro no altera el lease.

    `SlowNetworkTests`, `OutageTests` y `RetryTests` siguen pasando.

## Backend

- [ ] T-017-07 — Estado del nodo en el backend.
  - RF: RF-017-09 (servidor), RF-017-10 (API).
  - Depende de: T-017-01.
  - Archivos previstos: `web/CuidadosApp/mobile_models.py`, `web/CuidadosApp/migrations/0010_detectionnode_monitor_state.py` (nueva, aditiva), `web/CuidadosApp/api/detection.py`, `web/CuidadosApp/test_mobile.py`, `web/CuidadosApp/test_access.py`.
  - Hecho cuando: las pruebas comprueban:
    - estado válido guardado con `monitor_since`, que no cambia si el estado se repite;
    - parámetro desconocido, valor inválido o repetido → 400;
    - sin parámetro, estado intacto;
    - nodo revocado, sin plan, fuera de cupo o sin consentimiento → sin cambios;
    - `nodes` devuelve `monitor_state` (`desconocido` si vacío) solo al titular, y otro usuario recibe 404.

    `makemigrations --check` queda sin cambios tras crear `0010`, y la migración se prueba en avance y reversión.
- [ ] T-017-08 — Avisos de monitoreo ciego y de nodo sin señal.
  - RF: RF-017-11, RF-017-12.
  - Depende de: T-017-07.
  - Archivos previstos: `web/CuidadosApp/push.py`, `web/CuidadosApp/management/commands/send_mobile_reminders.py`, `web/CuidadosApp/test_push.py`, `docs/OPERACION.md`.
  - Hecho cuando: las pruebas con Firebase simulado comprueban:
    - `persona_no_visible` y `sin_imagen` envían un aviso por episodio y por dispositivo a titular, familiar y cuidador, con texto genérico, visibilidad privada y sin prioridad alta;
    - un nuevo episodio tras `normal` vuelve a avisar;
    - `poca_luz` no genera push;
    - sin `risk_alerts` o con consentimiento retirado, no hay aviso;
    - nodo sin señal 60 s → un aviso, salvo si está revocado o denegado por `allowed()`;
    - un episodio de más de 1 h no se anuncia;
    - las caídas siguen primero.

    OPERACION.md explica que la demora depende de la cadencia del comando.

## App

- [ ] T-017-09 — Estado en la tarjeta del nodo (titular).
  - RF: RF-017-10.
  - Depende de: T-017-07.
  - Archivos previstos: `mobile/lib/features/patients/patient_screen.dart` (función pura de texto e icono), prueba en `mobile/test/`.
  - Hecho cuando: la prueba cubre los cinco estados (incluido `desconocido`) y los casos revocado, sin plan y sin señal, que tienen prioridad. `flutter analyze` queda sin problemas y `flutter test` pasa completo.
- [ ] T-017-10 — Estado de la cámara para titular, familiar y cuidador (D-077).
  - RF: RF-017-10 (ficha del paciente).
  - Depende de: T-017-07, T-017-09.
  - Archivos previstos: `web/CuidadosApp/api/views.py` (`PatientView`, campo `camera_state`), `web/CuidadosApp/test_access.py`, `mobile/lib/features/patients/patient_screen.dart`, prueba Flutter.
  - Hecho cuando:
    - la matriz por rol de `test_access` comprueba que titular, familiar y cuidador reciben `camera_state`, que la respuesta no expone nombre, id ni `last_seen_at` del nodo y que un usuario sin acceso recibe 404;
    - sin nodos activos, `camera_state` es `null` y la línea no aparece;
    - con varios estados, gana el de mayor prioridad;
    - la prueba Flutter muestra la línea de solo lectura a los tres roles, sin opción de revocar.

## Documentación y cierre

- [ ] T-017-11 — Guía de instalación, calibración y protocolo ampliado.
  - RF: RF-017-14, RF-017-15.
  - Depende de: T-017-02, T-017-05 (para documentar los comandos y estados reales).
  - Archivos previstos: `edge/README.md`.
  - Hecho cuando: el README tiene:
    - guía de montaje (altura, vista diagonal que incluya la cama y el suelo, luz tenue, corriente);
    - comando de calibración y recalibración al mover la cámara;
    - parámetros nuevos con defectos;
    - estados de monitoreo y qué hacer ante cada uno;
    - casos difíciles (sábanas, persona tapada, caída en línea con la cámara, dos personas);
    - protocolo con los casos nuevos y el denominador fijado de nuevo antes de ejecutarlo.

    Además, los enlaces son válidos.
- [ ] T-017-12 — Validación y cierre documental.
  - RF: RF-017-01..15.
  - Depende de: T-017-02..11.
  - Archivos previstos: `specs/017-robustez-caidas/validation.md` (nuevo), `specs/README.md`, `docs/ESTADO_PROYECTO.md`, `docs/TRAZABILIDAD.md`.
  - Hecho cuando:
    - `validation.md` registra comandos y conteos reales de las tres suites, check, `makemigrations --check`, `edge.bench` antes/después y lo no comprobado;
    - la trazabilidad mantiene RT-03 y HU-05 como «Parcial» o «Sin evidencia» mientras no haya protocolo ni Firebase;
    - existe la PR hacia `develop`, sin merge.
- [ ] T-017-13 — Pruebas en vivo (fuera del entorno automático).
  - RF: RF-017-01, RF-017-02, RF-017-06..08, RF-017-11, RF-017-12.
  - Depende de: T-017-12, cámara autorizada, nodo vinculado a un servidor de prueba, y Firebase de prueba (D-054) para el push.
  - Responsable: Propietario.
  - Hecho cuando: quedan registrados en `validation.md`, con equipo, cámara y fecha:
    - calibración con ventana;
    - salida de cama y deslizamiento simulado sobre colchoneta;
    - tapar la cámara;
    - desconectarla;
    - apagar la luz;
    - cortar la red del nodo;
    - recepción de los avisos.

    Las cifras de precisión siguen en el protocolo (D-053).

## Autorización posterior

2026-10-27: «Autorizo T-017-01 a T-017-12, sin merge, migración real ni despliegue». Autoriza implementar T-017-01..12 en `feature/017-robustez-caidas` y abrir la PR hacia `develop`. No autoriza merge, migraciones en bases reales ni despliegue. T-017-13 sigue a cargo del propietario.

## Ejecución

| Fecha | Tarea | Archivos / comando | Resultado / pendiente |
|---|---|---|---|

## Reanudación

Última acción real: spec, plan y tareas redactados el 2026-10-27 (fase DOCUMENTAR), con D-073..D-077. Siguiente paso: autorizar las tareas que corresponda. Fase permitida: solo documentación. Bloqueos: T-017-13 por cámara, servidor de prueba y Firebase.

## Aceptación del usuario

Pendiente; no marcarla automáticamente después de ejecutar tests.
