# VIGIA móvil

Cliente Flutter Android/iOS para la API del proyecto Django existente. Android primero e iOS en el alcance (D-068); iOS se compila solo en macOS. Instalación en el teléfono: [docs/INSTALACION_CELULAR.md](../docs/INSTALACION_CELULAR.md).

[Guía de instalación, cuentas demo y pruebas](../docs/MOVIL_DESARROLLO.md).
[Requisitos y alcance](../specs/010-aplicacion-movil/spec.md).
[Resultados y pendientes](../specs/010-aplicacion-movil/validation.md).

Código: `lib/main.dart` (acceso), `lib/app/` (navegación), `lib/core/api.dart` (sesión/transporte), `lib/features/*` (agenda, pacientes, medicinas, postura, detección, plan y perfil), `lib/shared/` (widgets comunes) y `lib/notifications/` (avisos locales). `web/` permite una vista previa local; Android es el objetivo móvil principal e iOS está en el alcance desde el 2026-10-26 (D-068, compilado en macOS).
