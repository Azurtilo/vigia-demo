# Cámaras

## Cámara disponible: GoPro HERO7 Silver

Información recopilada en la Fase 0 (2026-10-22). **Nada de esto ha sido probado todavía con el equipo real.**

| Capacidad | HERO7 Silver |
|---|---|
| Modo webcam oficial por USB | ❌ No (introducido en modelos posteriores) |
| API oficial Open GoPro | ❌ No (HERO9 en adelante) |
| Salida HDMI | ❌ No (solo la HERO7 Black) |
| Livestream RTMP | ❌ No (solo la HERO7 Black) |
| Wi‑Fi / Bluetooth con la app GoPro Quik | ✅ Sí |
| Vista previa por Wi‑Fi accesible desde un PC (API no oficial) | ❓ Por verificar en la Fase 9 |
| Grabación de video a microSD | ✅ Sí |

### Consecuencia

La HERO7 Silver **no permite, por vías oficiales, enviar video en vivo** a un PC o a Flutter. Opciones a evaluar en la Fase 9:

1. **Análisis de video grabado (recomendada para la prueba con GoPro).** Se graba con la GoPro, se transfiere el archivo y el Edge lo procesa con MediaPipe. Es hardware y modelo reales, pero **no es monitoreo en tiempo real**.
2. **Vista previa por Wi‑Fi (experimental).** Comprobar si la cámara expone el stream de previsualización. Sin garantía ni soporte oficial.
3. **Monitoreo en vivo con otra fuente:** webcam USB del PC o cámara del teléfono.

El Edge usará un **adaptador de cámara intercambiable** (archivo de video, webcam, stream de red) para no depender de un modelo concreto.
