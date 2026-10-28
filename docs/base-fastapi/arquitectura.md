# Arquitectura de VIGIA

## Diagrama de componentes

```
 ┌──────────────┐   ┌──────────────┐
 │ App Flutter  │   │ Portal React │
 │ Android/iOS  │   │ Admin/Client │
 └──────┬───────┘   └──────┬───────┘
        │ 1) Login           │
        ▼                    ▼
 ┌──────────────────────────────────┐
 │   Firebase Authentication        │──► entrega ID token (JWT)
 └──────────────────────────────────┘
        │ 2) HTTPS + "Authorization: Bearer <ID token>"
        ▼
 ┌──────────────────────────────────┐        ┌───────────────────┐
 │  FastAPI (backend único)         │◄─HTTPS─│ Edge (PC)         │
 │  · verifica token (Admin SDK)    │ eventos│ cámara → MediaPipe│
 │  · roles y permisos por paciente │ y      │ → reglas → evento │
 │  · límites de plan (transacción) │ metadat│ (sin video a nube)│
 │  · auditoría y alertas           │        └───────────────────┘
 └──────┬───────────────┬───────────┘
        ▼               ▼
 ┌────────────┐   ┌──────────────┐
 │ Firestore  │   │ FCM (push)   │
 └────────────┘   └──────────────┘
 Recordatorios programados: Cloud Scheduler → endpoint protegido del backend
```

## Principios

1. **Un solo backend y una sola base de datos.** La app y el portal consumen la misma API REST.
2. **Las reglas de negocio viven solo en FastAPI.** Los clientes no escriben directo en Firestore; las reglas de Firestore niegan el acceso directo por defecto.
3. **Autenticación ≠ autorización.** Firebase Auth dice *quién eres*; FastAPI decide *qué puedes hacer* (rol, relación con el paciente, permiso, plan, estado de la cuenta).
4. **El análisis de imágenes está desacoplado.** Si la cámara o el modelo fallan, el resto del sistema sigue funcionando.
5. **No se transmite ni almacena video por defecto.** El Edge envía solo eventos y metadatos.
6. **Entornos separados.** Desarrollo y pruebas con Firebase Emulator Suite (proyecto `demo-vigia`, sin datos reales); producción en un proyecto Firebase propio.
