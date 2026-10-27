# 017 — Robustez de la detección de caídas: zona de cama y avisos de monitoreo ciego

Estado: implementada en `feature/017-robustez-caidas` (T-017-01..12); verificación técnica sintética en [validation.md](validation.md). Fecha: 2026-10-27.
Módulo: nodo `edge/` + `CuidadosApp` (API del nodo, historial, avisos) + app móvil (tarjeta del nodo). Fuente: pedido del usuario 2026-10-27, tras revisar el prototipo `pose_app` (`C:\Users\josea\Downloads\pose_app`, módulo «Vigía · detector de caídas de la cama» en Kotlin): «redacta la spec 017», sobre la propuesta de traer a VIGIA (1) avisos de detector ciego, (2) zona de cama con regla secundaria, (3) heurísticas de robustez y (4) documentación de instalación y casos difíciles.
Implementación autorizada: SÍ, T-017-01..12 el 2026-10-27, sin merge, migración real ni despliegue. Revisión del usuario: decisiones P-017-01..05 aceptadas el 2026-10-27 (D-073..D-077). Plan y tareas: [plan.md](plan.md), [tasks.md](tasks.md).

## Problema y resultado

La regla de caída de la [spec 012](../012-deteccion-caidas/spec.md) mira el **impacto** (descenso rápido de la cadera, ángulo del tronco, silueta ancha) y confirma que la persona sigue abajo. Tiene tres huecos:

1. **Monitoreo ciego en silencio.** Si se pierde la señal más de `max_gap_seconds` (2 s), la regla se reinicia sin aviso ([edge/fall.py](../../edge/fall.py)). Una caída que termina fuera del cuadro, detrás de un mueble o a oscuras no genera nada. Si la cámara deja de entregar imágenes, `edge/run.py` registra «Sin imagen de cámara» y **termina el proceso**; nadie se entera salvo por la tarjeta del nodo en la app («Conectado» deja de aparecer a los 90 s).
2. **Caídas lentas o deslizándose** desde la cama (el caso típico de una persona dependiente de noche) pueden no superar la velocidad de descenso y no generar impacto.
3. **Falsos positivos o negativos por la escena:** sábanas o ropa en el suelo, persona tapada (caderas no visibles), una sola persona asomada.

El prototipo `pose_app` resuelve estos casos con una regla de **estado final** (persona acostada fuera de un polígono de cama calibrado) y alertas de monitoreo ciego (persona no visible, poca luz, sin imagen), con 40 pruebas JUnit sintéticas. No se porta su código (Kotlin, Android, sin red) sino su lógica, al nodo Edge en Python, que es la vía principal de detección (D-057).

Resultado esperado: el nodo avisa también cuando **no puede vigilar** (persona perdida tras haber sido vista, cámara sin imagen, poca luz, nodo sin conexión), y detecta además a la persona **acostada fuera de la cama** durante unos segundos, con defensas contra sábanas y oclusiones. Las dos reglas de caída se complementan sin duplicar avisos. Todo sigue sin enviar imágenes ni coordenadas.

## Actores y permisos

Sin cambios respecto de 012/013/014. La autenticación del nodo, la matriz por rol de la [spec 013](../013-cuidado-delegado/spec.md) y el consentimiento de detección de la [spec 014](../014-privacidad/spec.md) se aplican igual a lo nuevo.

| Acción / datos | Anónimo | Nodo con credencial activa | Titular / familiar / cuidador con acceso (013) | Otro usuario | Superusuario |
|---|---|---|---|---|---|
| Enviar caída de la regla de cama (`risk="fall"`) | 401 | Sí, con las condiciones de 012 (plan, cupo, consentimiento) | No aplica | 401 | Sin excepción: necesita credencial de nodo |
| Informar el estado de monitoreo (RF-017-09) | 401 | Sí, mismas condiciones | No aplica | 401 | Igual |
| Ver el estado de monitoreo del nodo | 401 | No | Titular, en la tarjeta del nodo (`manage_nodes`, como hoy). Titular, familiar y cuidador: línea de solo lectura «Cámara: <estado>» en la ficha del paciente (`view`), sin nombre, id ni última señal del nodo (D-077) | 404 | Igual que la API móvil vigente |
| Recibir aviso de monitoreo ciego o nodo sin señal | — | — | Los mismos destinatarios del push de riesgo (013), con `risk_alerts` en el plan del titular (D-074) | No | Igual que cualquier usuario |
| Configurar la zona de cama | — | Solo en el equipo del nodo (archivo local) | No desde la app en esta spec | — | — |

Nodo revocado, plan vencido, paciente fuera de cupo o consentimiento retirado: 401/403 como hoy; el nodo deja de capturar (fail-closed) y **no** se informa como monitoreo ciego (es una detención intencional).

## Alcance y exclusiones

Incluye:

- **Zona de cama** calibrada como polígono en el nodo y una **segunda regla de caída** «acostado fuera de la cama» que emite el mismo riesgo `fall`.
- **Heurísticas de robustez** para esa regla: seguimiento continuo (sábanas u objetos), puntos de respaldo caderas → hombros → cabeza, suavizado dentro/fuera y rearme.
- **Estados de monitoreo ciego** en el nodo: persona no visible tras haber sido vista, sin imagen de cámara (sin terminar el proceso), poca luz. Su envío al backend, la visualización en la app y el aviso a los destinatarios.
- **Nodo sin señal** detectado por el backend (`last_seen_at`), D-075.
- Pruebas sintéticas que traduzcan los escenarios de `DetectorCaidasTest.kt` y `GeometriaTest.kt` de `pose_app`.
- Documentación: guía de instalación de la cámara, casos difíciles y nuevos casos negativos del protocolo (D-053) en [edge/README.md](../../edge/README.md).

No incluye:

- Portar el servicio Android de `pose_app` ni detectar caídas con la cámara del teléfono (D-057: el teléfono es alternativa demostrativa; iOS está en el alcance por D-068 y el código Kotlin no aplica).
- La alerta `SALIDA_DE_CAMA` de `pose_app` (fuera de la cama 30 s en cualquier postura). Queda como trabajo futuro.
- La alerta `INMOVIL_FUERA_DE_CAMA` de 60 s (D-076): choca con el significado de inmovilidad de RT-02 (60–120 min en cama) y su propio autor documenta falsas alarmas diarias.
- Calibrar la zona de cama desde la app o el portal, y enviar el polígono al servidor.
- Cambiar los umbrales o el comportamiento de la regla de impacto de 012 (salvo el aviso de RF-017-06 cuando se pierde la señal).
- Validación clínica, varias personas en cuadro, entrenamiento de modelos, declarar cumplidos los RNF.

## Historias y flujo

1. **Instalación.** El técnico o familiar monta la cámara (guía de RF-017-14) y ejecuta la calibración de cama en el equipo del nodo: marca las esquinas de la cama sobre la imagen local o escribe un JSON. El polígono queda en un archivo local, como las referencias de postura.
2. **Caída lenta desde la cama.** La persona se desliza al suelo. La regla de impacto no se activa. La regla de cama ve las caderas fuera del polígono y el tronco ≥ 60° durante 5 s, habiendo seguido a la persona sin saltos desde la cama → caída `fall` con `rule_version="fall-bed-v1"`. Llega por la misma vía de 012 (push inmediato, D-051).
3. **Caída brusca.** La regla de impacto emite primero; la regla de cama no repite el aviso para el mismo evento.
4. **Sábana en el suelo.** MediaPipe detecta algo «acostado» fuera de la cama sin haberse visto salir a la persona → no es caída; si persiste sin persona válida, cuenta como persona no visible.
5. **Caída fuera de cuadro.** La persona se vio, luego desaparece 10 s → estado «persona no visible» → push genérico a los destinatarios (D-074). Al reaparecer, el estado se normaliza.
6. **Cámara desconectada o tomada.** La lectura de cuadros falla → el nodo reintenta abrir la cámara sin terminar; a los 10 s informa «sin imagen» y se envía push. Si el proceso o la red mueren, el backend detecta el nodo sin señal a los 60 s y también avisa (D-075).
7. **Noche sin luz.** El brillo medio del cuadro (un número calculado en el nodo) queda bajo el mínimo 5 s → «poca luz»; se ve en la app, sin push (D-074); se normaliza con histéresis.

## Requisitos funcionales

### Zona de cama y regla «acostado fuera de la cama»

- RF-017-01: EL SISTEMA acepta una zona de cama opcional como polígono de 3 a 8 vértices en coordenadas normalizadas de imagen (0–1), cargada desde un archivo JSON local (`--bed-config`) o creada con un paso de calibración local. Ordena los vértices por ángulo alrededor de su centro (no forma polígonos cruzados) y rechaza al iniciar valores fuera de rango, menos de 3 vértices, área casi nula o claves desconocidas. El borde cuenta como dentro de la cama. El polígono no sale del equipo.
- RF-017-02: CUANDO hay zona de cama y el punto de referencia de la persona (RF-017-04) está fuera del polígono según la mayoría de los últimos `bed_smoothing_frames` cuadros, y el ángulo del tronco respecto de la vertical es ≥ `bed_lying_angle` de forma continua durante `bed_lying_seconds`, EL SISTEMA emite una caída con `risk="fall"` y `rule_version="fall-bed-v1"`, con el mismo contrato, cola y reintentos de RF-012-05/11/12.
- RF-017-03: SI la persona aparece «acostada» fuera de la cama sin haber sido seguida de forma continua desde la cama o desde una postura no acostada (salto mayor que `max_track_speed` o hueco mayor que `track_gap_seconds`), ENTONCES la regla de cama no la considera caída y el cuadro cuenta como «sin persona válida» para RF-017-06.
- RF-017-04: EL SISTEMA usa como punto de referencia el punto medio de las caderas; si no son visibles, el de los hombros; si tampoco, el promedio de nariz y orejas. Mide el ángulo del tronco con el mejor par disponible (hombros–caderas, cabeza–caderas, cabeza–hombros). SI está fuera de la cama con un solo punto disponible, ENTONCES no decide postura y cuenta como sin persona válida. Un cambio de punto de referencia no se interpreta como movimiento ni como salto.
- RF-017-05: Las dos reglas de caída no duplican avisos: tras emitir una caída (de cualquiera de las dos), ninguna emite otra hasta que la persona vuelva a la cama o se vea no acostada de forma continua durante `rearm_upright_seconds`; un cuadro aislado o un hueco sin persona no cuenta para ese rearme. Sin zona de cama, solo funciona la regla de impacto de 012, sin cambios.

### Monitoreo ciego

- RF-017-06: CUANDO la persona ya se vio con pose válida en la sesión de monitoreo y pasan `lost_seconds` sin ninguna pose válida, EL SISTEMA pasa al estado `persona_no_visible`; vuelve a `normal` cuando reaparece. Antes de haber visto a alguien no se activa. Dos personas en cuadro (p. ej., el cuidador) no cuentan como persona no visible (supuesto S-017-02).
- RF-017-07: SI la cámara no entrega cuadros, ENTONCES el nodo no termina el proceso: reintenta abrirla con espera creciente (máx. 30 s) y, tras `no_image_seconds` sin cuadros, pasa al estado `sin_imagen`; vuelve a `normal` al recibir cuadros de nuevo. Un video local de prueba que termina sí finaliza el proceso, como hoy.
- RF-017-08: EL SISTEMA calcula en el nodo el brillo medio de cada cuadro (0–1, un solo número). CUANDO queda bajo `min_brightness` durante `low_light_seconds`, pasa al estado `poca_luz`; vuelve a `normal` cuando supera `min_brightness × 1,3` el mismo tiempo. Funciona aunque nunca se haya visto a nadie.
- RF-017-09: CUANDO cambia el estado de monitoreo del nodo, EL SISTEMA lo comunica al backend sin imágenes, coordenadas ni brillo, solo el estado (`normal`, `persona_no_visible`, `sin_imagen`, `poca_luz`) y su hora, en la renovación de autorización que el nodo ya hace cada 10 s (D-073). Si hay varios estados a la vez, informa el de mayor prioridad: `sin_imagen` > `poca_luz` > `persona_no_visible`. Un nodo que no informa estado (versión anterior) se trata como «estado desconocido», no como error.
- RF-017-10: La app muestra el estado de monitoreo en la tarjeta del nodo del paciente, junto a «Conectado · Última señal», con un texto en es-CL por estado y sin datos clínicos. Además (D-077), la ficha del paciente muestra a todo rol con `view` (titular, familiar y cuidador) una línea de solo lectura «Cámara: <estado>» con el estado agregado de sus nodos activos, sin nombre, id ni última señal del nodo y sin opción de revocar.
- RF-017-11 (D-074): CUANDO un nodo conectado informa `persona_no_visible` o `sin_imagen`, EL SISTEMA avisa una vez por episodio y por dispositivo a los destinatarios del push de riesgo (013), con texto genérico sin datos del paciente (D-058), visibilidad privada y sin prioridad alta. `poca_luz` solo se muestra en la app. Al volver a `normal` el episodio se cierra y uno nuevo puede avisar.
- RF-017-12 (D-075): CUANDO un nodo activo que estaba conectado lleva más de `node_offline_seconds` sin renovar su autorización (`last_seen_at`), EL SISTEMA lo considera «sin señal» y avisa una vez por episodio como en RF-017-11. Un nodo revocado o sin permiso por plan, cupo o consentimiento no genera este aviso.

### Registro, pruebas y documentación

- RF-017-13: El nodo registra en su log cada cambio de estado de monitoreo y cada caída de la regla de cama (con su `rule_version`, inicio y confirmación), sin datos clínicos ni coordenadas.
- RF-017-14: [edge/README.md](../../edge/README.md) incluye la guía de instalación (altura 1,8–2,5 m, vista diagonal u oblicua que abarque la cama **y el suelo alrededor**, luz tenue de noche, equipo conectado a la corriente), la calibración de la zona de cama, los casos difíciles conocidos y los nuevos casos negativos del protocolo (RF-017-15).
- RF-017-15: El protocolo de D-053, **antes de ejecutarse**, agrega como actividades normales: persona sentada junto a la cama, ropa o sábana en el suelo, persona tapada en la cama y habitación en penumbra; y como caídas: deslizarse lentamente de la cama al suelo. El denominador se fija de nuevo antes de la ejecución.

## Datos y reglas

Parámetros nuevos del nodo, configurables por argumento o JSON como los de 012 (RF-012-04), con validación al iniciar. Longitudes y velocidades en **troncos** (como 012) para no depender de la distancia a la cámara; `pose_app` usaba fracciones del cuadro.

| Parámetro | Defecto propuesto | Unidad | Origen en `pose_app` |
|---|---|---|---|
| `bed_lying_angle` | 60 | grados | `anguloAcostado` |
| `bed_lying_seconds` | 5.0 | s | `segundosParaCaida` |
| `bed_smoothing_frames` | 8 | cuadros | `ventanaSuavizado` |
| `track_gap_seconds` | 1.5 | s | `segundosContinuidad` |
| `max_track_speed` | por definir en el plan | troncos/s | `velocidadMaxima` (2 cuadros/s) |
| `rearm_upright_seconds` | 3.0 | s | `SEGUNDOS_DE_PIE_PARA_REARMAR` |
| `lost_seconds` | 10.0 | s | `segundosSinPersona` |
| `no_image_seconds` | 10.0 | s | `segundosSinImagen` |
| `min_brightness` | 0.12 | 0–1 | `brilloMinimo` |
| `low_light_seconds` | 5.0 | s | `segundosPocaLuz` |
| `node_offline_seconds` (backend) | 60 (D-075) | s | — (el backend ya marca «Conectado» a 90 s) |

Archivo de zona de cama: JSON local, p. ej. `{"bed": [[0.21, 0.40], [0.78, 0.38], [0.80, 0.86], [0.18, 0.88]]}`, en `edge/models/` junto a las referencias de postura (carpeta ya ignorada por Git). Una calibración nueva reinicia el estado de la regla de cama. Si la cámara se mueve, hay que recalibrar (se documenta; el nodo no lo detecta).

Caída de la regla de cama: contrato de 7 claves de 010 sin cambios; `risk="fall"`, `rule_version="fall-bed-v1"`, `posture`/`confidence` del clasificador calibrado (puede ser `indeterminada`). El backend ya acepta `fall` con `indeterminada` y una `rule_version` de hasta 80 caracteres: no requiere cambio de API ni migración para esta parte.

Estado de monitoreo: valores `normal`, `persona_no_visible`, `sin_imagen`, `poca_luz`, y `desconocido` para nodos sin informe. Se guarda en el nodo (`DetectionNode`) como último estado y desde cuándo, y viaja en la renovación de autorización (D-073). No es una observación clínica de postura: no entra en el historial de observaciones ni en la purga de datos de salud de 014; solo se conserva el último valor.

## Criterios de aceptación

| RF | Dado / cuando | Entonces |
|---|---|---|
| RF-017-01 | JSON con 2 vértices, vértice fuera de 0–1, clave desconocida o polígono degenerado | Error al iniciar con mensaje en es-CL |
| RF-017-01 | Esquinas en cualquier orden; punto sobre el borde | Polígono no cruzado; el borde cuenta como dentro |
| RF-017-02 | Secuencia sintética: en cama, se desliza al suelo despacio (sin impacto) y queda 8 s tendida | Una caída `fall-bed-v1` ≈ 5 s después de quedar fuera y acostada |
| RF-017-02 | Fuera de la cama de pie o sentada 60 s | Sin caída |
| RF-017-02 | Fuera y acostada 3 s y se incorpora | Sin caída |
| RF-017-03 | Aparece de golpe una forma «acostada» en el suelo sin haber salido de la cama | Sin caída; si dura `lost_seconds`, `persona_no_visible` |
| RF-017-04 | Caderas no visibles, hombros sí, persona tendida fuera de la cama | Caída por la regla de cama |
| RF-017-04 | Solo la cabeza visible fuera de la cama | Sin caída; cuenta como sin persona válida |
| RF-017-05 | Caída brusca que cumple las dos reglas | Un solo `fall` |
| RF-017-05 | Caída, de pie 3 s seguidos, segunda caída | Dos `fall` |
| RF-017-05 | Caída, un cuadro de pie entre cuadros vacíos, sigue en el suelo | Un solo `fall` |
| RF-017-05 | Sin `--bed-config` | Comportamiento y pruebas de 012 sin cambios |
| RF-017-06 | Persona vista y luego 10 s sin pose válida | Estado `persona_no_visible` una vez; al reaparecer, `normal` |
| RF-017-06 | Nunca se vio a nadie desde el inicio | No se activa |
| RF-017-07 | La cámara deja de entregar cuadros 12 s y vuelve | `sin_imagen` y luego `normal`; el proceso no termina |
| RF-017-07 | Lease denegado (plan, consentimiento, revocación) | Detención fail-closed como hoy; sin estado `sin_imagen` |
| RF-017-08 | Brillo 0,05 durante 6 s; luego 0,20 durante 6 s | `poca_luz` y luego `normal`; brillo oscilando alrededor de 0,12 no alterna |
| RF-017-09 | Nodo informa estado en la renovación; parámetro desconocido o valor fuera de la lista | Aceptado solo el estado válido; el resto rechazado con 400 |
| RF-017-09 | Nodo de versión anterior sin informe de estado | Sigue funcionando; estado `desconocido` en la app |
| RF-017-10 | El titular abre la tarjeta del nodo | Ve el estado con texto en es-CL; otro usuario recibe 404 |
| RF-017-10 | Titular, familiar y cuidador abren la ficha del paciente | Ven «Cámara: <estado>» sin datos del nodo; un usuario sin acceso recibe 404; sin nodos activos, la línea no aparece |
| RF-017-11 | Nodo en `persona_no_visible` 2 veces seguidas sin volver a `normal` | Un solo aviso; tras `normal` y un nuevo episodio, otro aviso |
| RF-017-11 | Nodo en `poca_luz` | Visible en la app; sin push |
| RF-017-11 | Plan sin `risk_alerts` o consentimiento retirado | Sin aviso |
| RF-017-12 | Nodo conectado deja de renovar más de `node_offline_seconds` | Un aviso «sin señal»; al reconectar se cierra el episodio |
| RF-017-12 | Nodo revocado o paciente fuera de cupo | Sin aviso |
| RF-017-13 | Revisión del log en las pruebas | Cambios de estado y caídas de cama sin coordenadas ni datos clínicos |
| RF-017-14/15 | Revisión de `edge/README.md` | Guía, calibración, casos difíciles y casos nuevos del protocolo presentes |

## No funcionales

- **Privacidad:** ningún cuadro, polígono, coordenada ni valor de brillo sale del nodo; solo el estado de monitoreo y la caída con el contrato de 010. El estado de monitoreo no es un dato clínico, pero se trata con el mismo control de acceso que el nodo.
- **Rendimiento:** el cálculo de brillo y la regla de cama deben ser despreciables frente a la inferencia de MediaPipe; se comprueba con `edge/bench.py` (RF-012-09) antes y después. El objetivo de < 100 ms por cuadro sigue **sin medir** con personas.
- **Alerta ≤ 10 s:** la regla de cama confirma a los 5 s de quedar fuera y acostada, más el suavizado (≈ 0,3 s a 30 FPS). No se declara cumplido sin la medición de D-054.
- **Precisión:** la regla de cama sube la sensibilidad a cambio de posibles falsos positivos (persona que se tiende en el suelo o en un sillón fuera de la zona). Se mide con el protocolo ampliado (RF-017-15); no se declaran cifras.

## Compatibilidad

- Se preservan la regla de impacto, sus umbrales y pruebas (012), la clasificación de postura y la inmovilidad (RT-02), el contrato de observación de 7 claves, la deduplicación por `event_id`, el push inmediato de caída (D-051) y el texto genérico (D-058).
- Un nodo de versión anterior sigue funcionando con un backend nuevo (estado `desconocido`). Un nodo nuevo con un backend anterior no debe fallar: si la vía de estado no existe, lo registra en el log y sigue vigilando (detalle en el plan según P-017-01).
- La app instalada sin soporte de estado sigue mostrando la tarjeta del nodo como hoy.
- Specs relacionadas: [010](../010-aplicacion-movil/spec.md), [012](../012-deteccion-caidas/spec.md), [013](../013-cuidado-delegado/spec.md), [014](../014-privacidad/spec.md).

## Supuestos y decisiones pendientes

Supuestos (reversibles):

- S-017-01: la cama es un mueble elevado y fijo, y la cámara no se mueve después de calibrar. Un colchón en el suelo hace que «acostado fuera de la cama» dependa solo de la calibración.
- S-017-02: con dos personas en cuadro, el nodo no evalúa caídas (como hoy) y no informa `persona_no_visible`, porque hay alguien presente.
- S-017-03: la regla de cama, como la de `pose_app`, mide el tronco en la imagen; una persona tendida en línea con la cámara se ve vertical y no se detecta. Queda como limitación documentada (D-076).

Decisiones (aceptadas por el usuario el 2026-10-27: «estoy de acuerdo con las recomendaciones»):

- **P-017-01 → D-073.** El estado viaja en la renovación `GET /api/v1/edge/status` y se guarda en `DetectionNode` (último estado y desde cuándo), no como observación clínica; `risk` no cambia. Migración aditiva. Descartadas: nuevos valores de `risk` (mezclan estado técnico con historial clínico) y solo log local (nadie se entera).
- **P-017-02 → D-074.** Push genérico, sin prioridad alta, para `persona_no_visible` y `sin_imagen`, a los destinatarios de riesgo con `risk_alerts`; `poca_luz` solo en la app.
- **P-017-03 → D-075.** El nodo sin señal entra en esta spec: 60 s sin renovar, revisado en `send_mobile_reminders`.
- **P-017-04 → D-076.** Sin alerta de inmóvil fuera de la cama en esta spec; se reevalúa con los resultados del protocolo (D-053).

Detectada al planificar (2026-10-27) y resuelta el mismo día («para P-017-05 opcion A»):

- **P-017-05 → D-077, opción A.** Hoy solo el titular ve los nodos (`manage_nodes`), pero el push de riesgo y el de monitoreo ciego llegan también al familiar y al cuidador (D-063, D-074): al abrir la app no verían por qué se les avisó. (A) Mostrar una línea de solo lectura «Cámara: <estado>» en la ficha del paciente a todo rol con `view`, sin datos del nodo ni opción de revocar; (B) solo a quienes tengan `detection` (titular y familiar); (C) solo el titular. **Recomendación: A**, porque el cuidador suele ser quien está en el domicilio y puede arreglar la cámara o encender una luz.

## Revisión y cambios

2026-10-27: creada en fase DOCUMENTAR a partir de la revisión de `pose_app`. Sin autorización de implementación.

2026-10-27 (posterior): el usuario acepta las recomendaciones de P-017-01..04 (D-073..D-076) y pide plan y tareas. RF-017-09/11/12 precisados con esas decisiones. Implementación no autorizada.

2026-10-27 (posterior): el usuario elige la opción A de P-017-05 (D-077). RF-017-10 y la matriz de permisos se precisan. Implementación no autorizada.

2026-10-27 (posterior): «Autorizo T-017-01 a T-017-12, sin merge, migración real ni despliegue». Implementadas y verificadas con pruebas sintéticas; PR hacia `develop` sin merge. RF-017-15 fija el denominador del protocolo en 25 caídas y 60 actividades normales (sustituye la propuesta 20/40 de D-053). Aceptación funcional pendiente.
