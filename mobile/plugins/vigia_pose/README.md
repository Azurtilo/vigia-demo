# VIGIA Pose

Plugin local Android/iOS para inferencia MediaPipe Pose Landmarker IMAGE. Recibe ruta de captura temporal local y devuelve landmarks al proceso Flutter; no realiza llamadas de red. Inferencia en cola serial fuera del hilo UI, máximo dos personas para rechazar encuadre múltiple. El cliente usa cámara trasera sin audio, elimina capturas tras inferencia y libera cámara/modelo al salir o pasar a segundo plano.

Android: tasks-vision1.0.0 (versión del ejemplo oficial consultado). iOS: MediaPipeTasksVision0.10.21 mediante CocoaPods; Swift Package Manager no sustituye esta dependencia. Falta resolver/build nativo y probar compatibilidad en este equipo por SDK ausente/disco lleno. No se acredita paridad solo porque haya código en ambos lenguajes.

Modelo: asset compartido assets/models/pose_landmarker_lite.task. No cargar un modelo proporcionado por una URL recibida en API. El hash/procedencia figuran en assets/models/README.md.

Fuentes consultadas el20 de octubre de2026:
- https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker/android
- https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker/ios
- https://pub.dev/packages/camera (plugin oficial Flutter0.12.1; SDK Android24+, iOS13+)

La salida geométrica se clasifica con referencias capturadas en esa sesión. Tres capturas coincidentes son un filtro técnico; no validación clínica, medición de presión ni detección de caída. No reutilizar calibración al mover cámara, cambiar paciente o reabrir sesión.
