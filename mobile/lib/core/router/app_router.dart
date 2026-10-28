import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../features/account/plan_screen.dart';
import '../../features/alerts/alerts_screen.dart';
import '../../features/account/presentation/account_screen.dart';
import '../../features/auth/application/session_controller.dart';
import '../../features/auth/presentation/complete_profile_screen.dart';
import '../../features/auth/presentation/create_account_screen.dart';
import '../../features/auth/presentation/forgot_password_screen.dart';
import '../../features/auth/presentation/loading_screen.dart';
import '../../features/auth/presentation/login_screen.dart';
import '../../features/auth/presentation/session_problem_screen.dart';
import '../../features/care/presentation/medication_form_screen.dart';
import '../../features/history/history_screen.dart';
import '../../features/members/members_screen.dart';
import '../../features/care/presentation/task_form_screen.dart';
import '../../features/patients/presentation/archived_patients_screen.dart';
import '../../features/patients/presentation/join_patient_screen.dart';
import '../../features/patients/presentation/patient_detail_screen.dart';
import '../../features/patients/presentation/patient_form_screen.dart';
import '../../features/patients/presentation/patients_screen.dart';
import '../../features/privacy/patient_privacy_screen.dart';
import '../../features/privacy/privacy_screens.dart';
import '../../features/shell/presentation/home_shell.dart';
import '../../features/shell/presentation/pending_section_screen.dart';
import '../../features/today/presentation/today_screen.dart';

abstract final class Routes {
  static const loading = '/cargando';
  static const login = '/ingresar';
  static const createAccount = '/crear-cuenta';
  static const forgotPassword = '/recuperar-contrasena';
  static const completeProfile = '/completar-perfil';
  static const problem = '/sin-acceso';
  static const acceptPolicy = '/aceptar-politica';
  static const today = '/hoy';
  static const patients = '/pacientes';
  static const alerts = '/alertas';
  static const posture = '/posturas';
  static const account = '/cuenta';
  static const newPatient = '/pacientes/nuevo';
  static const joinPatient = '/pacientes/unirse';
  static const archivedPatients = '/pacientes/archivados';
  static String patientDetail(String id) => '/pacientes/$id';
  static String editPatient(String id) => '/pacientes/$id/editar';
  static String newMedication(String id) => '/pacientes/$id/medicamentos/nuevo';
  static String editMedication(String id, String medId) => '/pacientes/$id/medicamentos/$medId';
  static String newTask(String id) => '/pacientes/$id/tareas/nueva';
  static String patientHistory(String id) => '/pacientes/$id/historial';
  static String patientMembers(String id) => '/pacientes/$id/personas';
  static const plan = '/cuenta/plan';
  static const privacy = '/cuenta/privacidad';
  static const policy = '/cuenta/privacidad/politica';
  static const myData = '/cuenta/privacidad/mis-datos';
  static String patientPrivacy(String id) => '/pacientes/$id/privacidad';
  static String patientExport(String id) => '/pacientes/$id/privacidad/exportar';
  static String editTask(String id, String taskId) => '/pacientes/$id/tareas/$taskId';

  static const public = {login, createAccount, forgotPassword};
}

/// Regla de navegación según la sesión. Función pura: se prueba sin dibujar pantallas.
/// Devuelve la ruta a la que hay que ir, o null para quedarse donde se está.
String? redirectFor(SessionState session, String location) {
  String? goTo(String target) => location == target ? null : target;
  return switch (session) {
    SessionLoading() => goTo(Routes.loading),
    SessionUnavailable() || SessionBlocked() => goTo(Routes.problem),
    SignedOut() => Routes.public.contains(location) ? null : Routes.login,
    NeedsProfile() => goTo(Routes.completeProfile),
    NeedsPolicy() => goTo(Routes.acceptPolicy),
    SessionReady() => (Routes.public.contains(location) ||
            location == Routes.loading ||
            location == Routes.completeProfile ||
            location == Routes.acceptPolicy ||
            location == Routes.problem)
        ? Routes.today
        : null,
  };
}

final routerProvider = Provider<GoRouter>((ref) {
  // go_router vuelve a evaluar `redirect` cada vez que cambia este notificador.
  final session = ValueNotifier<SessionState>(ref.read(sessionControllerProvider));
  ref.listen(sessionControllerProvider, (_, next) => session.value = next);

  final router = GoRouter(
    initialLocation: Routes.loading,
    refreshListenable: session,
    redirect: (context, state) => redirectFor(session.value, state.matchedLocation),
    routes: [
      GoRoute(path: Routes.loading, builder: (_, _) => const LoadingScreen()),
      GoRoute(path: Routes.login, builder: (_, _) => const LoginScreen()),
      GoRoute(path: Routes.createAccount, builder: (_, _) => const CreateAccountScreen()),
      GoRoute(path: Routes.forgotPassword, builder: (_, _) => const ForgotPasswordScreen()),
      GoRoute(path: Routes.completeProfile, builder: (_, _) => const CompleteProfileScreen()),
      GoRoute(path: Routes.problem, builder: (_, _) => const SessionProblemScreen()),
      GoRoute(path: Routes.acceptPolicy, builder: (_, _) => const AcceptPolicyScreen()),
      StatefulShellRoute.indexedStack(
        builder: (context, state, shell) => HomeShell(shell: shell),
        branches: [
          StatefulShellBranch(routes: [
            GoRoute(path: Routes.today, builder: (_, _) => const TodayScreen()),
          ]),
          StatefulShellBranch(routes: [
            GoRoute(
              path: Routes.patients,
              builder: (_, _) => const PatientsScreen(),
              routes: [
                // Las rutas fijas van antes de ':id' para que "nuevo" no se lea como un identificador.
                GoRoute(path: 'nuevo', builder: (_, _) => const PatientFormScreen()),
                GoRoute(path: 'unirse', builder: (_, _) => const JoinPatientScreen()),
                GoRoute(path: 'archivados', builder: (_, _) => const ArchivedPatientsScreen()),
                GoRoute(
                  path: ':id',
                  builder: (_, state) => PatientDetailScreen(patientId: state.pathParameters['id']!),
                  routes: [
                    GoRoute(
                      path: 'editar',
                      builder: (_, state) => PatientFormScreen(patientId: state.pathParameters['id']!),
                    ),
                    GoRoute(
                      path: 'medicamentos/nuevo',
                      builder: (_, state) => MedicationFormScreen(patientId: state.pathParameters['id']!),
                    ),
                    GoRoute(
                      path: 'medicamentos/:medId',
                      builder: (_, state) => MedicationFormScreen(
                        patientId: state.pathParameters['id']!,
                        medicationId: state.pathParameters['medId'],
                      ),
                    ),
                    GoRoute(
                      path: 'historial',
                      builder: (_, state) => HistoryScreen(patientId: state.pathParameters['id']!),
                    ),
                    GoRoute(
                      path: 'privacidad',
                      builder: (_, state) => PatientPrivacyScreen(patientId: state.pathParameters['id']!),
                      routes: [
                        GoRoute(
                          path: 'exportar',
                          builder: (_, state) => ExportScreen(
                            title: 'Datos del paciente',
                            provider: patientExportProvider(state.pathParameters['id']!),
                          ),
                        ),
                      ],
                    ),
                    GoRoute(
                      path: 'personas',
                      builder: (_, state) => MembersScreen(patientId: state.pathParameters['id']!),
                    ),
                    GoRoute(
                      path: 'tareas/nueva',
                      builder: (_, state) => TaskFormScreen(patientId: state.pathParameters['id']!),
                    ),
                    GoRoute(
                      path: 'tareas/:taskId',
                      builder: (_, state) => TaskFormScreen(
                        patientId: state.pathParameters['id']!,
                        taskId: state.pathParameters['taskId'],
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ]),
          StatefulShellBranch(routes: [
            GoRoute(path: Routes.alerts, builder: (_, _) => const AlertsScreen()),
          ]),
          StatefulShellBranch(routes: [
            GoRoute(
              path: Routes.posture,
              builder: (_, _) => const PendingSectionScreen(title: 'Posturas'),
            ),
          ]),
          StatefulShellBranch(routes: [
            GoRoute(
              path: Routes.account,
              builder: (_, _) => const AccountScreen(),
              routes: [
                GoRoute(path: 'plan', builder: (_, _) => const PlanScreen()),
                GoRoute(
                  path: 'privacidad',
                  builder: (_, _) => const PrivacyScreen(),
                  routes: [
                    GoRoute(path: 'politica', builder: (_, _) => const PolicyScreen()),
                    GoRoute(
                      path: 'mis-datos',
                      builder: (_, _) => ExportScreen(title: 'Mis datos', provider: myDataProvider),
                    ),
                  ],
                ),
              ],
            ),
          ]),
        ],
      ),
    ],
  );
  ref.onDispose(() {
    router.dispose();
    session.dispose();
  });
  return router;
});
