/// Texto de la política vigente (spec 014, versión 2026-10-25), ajustado a los datos que guarda
/// el backend de la rama 019. La revisión legal sigue pendiente (D-067).
const policyTextVersion = '2026-10-25';

const policySections = <(String, List<String>)>[
  (
    'Qué datos tratamos',
    [
      'De tu cuenta: correo, nombre, plan (los cambios de plan son simulados, sin datos de pago) y los teléfonos '
          'donde recibes avisos.',
      'De cada paciente que registras: nombre, fecha de nacimiento, información para el cuidado, contactos de '
          'emergencia, medicamentos y horarios, tareas, registros de lo realizado u omitido con su autor, cambios de '
          'posición y, si activas la detección, observaciones de postura, inmovilidad y caídas.',
      'Los datos de salud son datos sensibles. Solo se registran con el consentimiento del propio paciente o de su '
          'representante, que la cuenta responsable declara en la ficha del paciente.',
    ],
  ),
  (
    'Para qué los usamos',
    [
      'Para organizar y registrar el cuidado, enviar recordatorios y avisos de riesgo a las personas con acceso, y '
          'gestionar tu suscripción. No los vendemos ni los usamos para publicidad.',
    ],
  ),
  (
    'Video y cámaras',
    [
      'El nodo de detección analiza el video en el domicilio y nunca lo envía ni lo guarda: al servidor solo llegan '
          'metadatos (postura estimada, confianza, hora y tipo de riesgo).',
    ],
  ),
  (
    'Quién accede',
    [
      'El responsable del paciente y las personas que él invite como familiar o cuidador, cada una según sus '
          'permisos. Los avisos se envían mediante Firebase Cloud Messaging con un texto genérico que no revela el '
          'paciente ni el evento.',
    ],
  ),
  (
    'Cuánto tiempo los conservamos',
    [
      'Registros de cuidado de un paciente activo: mientras siga activo.',
      'Paciente archivado: 2 años desde el archivo.',
      'Observaciones de detección: 30 días; las de riesgo y las alertas, 1 año.',
      'Recibos de avisos: 30 días. Invitaciones cerradas: 90 días.',
    ],
  ),
  (
    'Tus derechos',
    [
      'Puedes acceder a tus datos y descargarlos en formato JSON, corregirlos desde la ficha del paciente, revocar un '
          'consentimiento y eliminar un paciente o tu cuenta completa. Estas opciones están en Cuenta › Privacidad y en '
          'la ficha de cada paciente.',
    ],
  ),
  (
    'Cambios',
    ['Si esta política cambia, te pediremos aceptarla de nuevo antes de seguir usando VIGIA.'],
  ),
];

const policyFrame = 'Marco de referencia: Ley 21.719 sobre protección de datos personales y Ley 20.584 sobre '
    'derechos de los pacientes. Este texto no certifica su cumplimiento.';
