import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/api.dart';

class LoginScreen extends StatefulWidget {
  final VigiaApi api;
  final VoidCallback onSuccess;
  const LoginScreen({super.key, required this.api, required this.onSuccess});
  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final user = TextEditingController(),
      password = TextEditingController(),
      code = TextEditingController();
  bool busy = false, mfa = false;
  String? message;
  @override
  void dispose() {
    user.dispose();
    password.dispose();
    code.dispose();
    super.dispose();
  }

  Future<void> run(Future<void> Function() work) async {
    setState(() {
      busy = true;
      message = null;
    });
    try {
      await work();
      await widget.api.get('me');
      widget.onSuccess();
    } on ApiError catch (e) {
      final flows = e.response['data']?['flows'] as List? ?? [];
      final pendingMfa = flows.any(
        (f) => f['id'] == 'mfa_authenticate' && f['is_pending'] == true,
      );
      if (mounted) {
        setState(() {
          mfa = pendingMfa || mfa;
          message = pendingMfa
              ? 'Ingresa el código de tu autenticador o un código de recuperación.'
              : e.message;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(
          () => message =
              'No se completó el acceso. Revisa tu conexión o configuración.',
        );
      }
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> submit() => run(() async {
    if (mfa) {
      await widget.api.auth('auth/2fa/authenticate', {
        'code': code.text.trim(),
      });
    } else {
      await widget.api.auth('auth/login', {
        user.text.contains('@') ? 'email' : 'username': user.text.trim(),
        'password': password.text,
      });
    }
  });
  Future<void> google() => run(() async {
    const client = String.fromEnvironment('GOOGLE_CLIENT_ID');
    const server = String.fromEnvironment('GOOGLE_SERVER_CLIENT_ID');
    if (server.isEmpty) {
      throw ApiError(
        'Google todavía no está configurado en este entorno. Usa correo y contraseña.',
        0,
      );
    }
    await GoogleSignIn.instance.initialize(
      clientId: client.isEmpty ? null : client,
      serverClientId: server,
    );
    final account = await GoogleSignIn.instance.authenticate();
    final idToken = account.authentication.idToken;
    await widget.api.auth('auth/provider/token', {
      'provider': 'google',
      'process': 'login',
      'token': {'client_id': server, 'id_token': idToken},
    });
  });
  @override
  Widget build(BuildContext context) => Scaffold(
    body: SafeArea(
      child: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 440),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                if (kDebugMode)
                  Align(
                    alignment: Alignment.centerRight,
                    child: TextButton.icon(
                      icon: const Icon(Icons.settings_outlined),
                      label: const Text('Servidor de pruebas'),
                      onPressed: busy
                          ? null
                          : () async {
                              final input = TextEditingController(
                                text: widget.api.baseUrl,
                              );
                              final value = await showDialog<String>(
                                context: context,
                                builder: (ctx) => AlertDialog(
                                  title: const Text('Servidor de pruebas'),
                                  content: TextField(
                                    controller: input,
                                    decoration: const InputDecoration(
                                      labelText: 'Dirección del servidor',
                                    ),
                                  ),
                                  actions: [
                                    TextButton(
                                      onPressed: () => Navigator.pop(ctx),
                                      child: const Text('Volver'),
                                    ),
                                    FilledButton(
                                      onPressed: () =>
                                          Navigator.pop(ctx, input.text),
                                      child: const Text('Guardar'),
                                    ),
                                  ],
                                ),
                              );
                              if (value != null) {
                                try {
                                  await widget.api.setServer(value);
                                } catch (e) {
                                  if (mounted) {
                                    setState(() => message = e.toString());
                                  }
                                }
                              }
                            },
                    ),
                  ),
                const Icon(
                  Icons.spa_outlined,
                  color: Color(0xff5057a0),
                  size: 52,
                ),
                const SizedBox(height: 12),
                const Text(
                  'VIGIA',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 30, fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: 28),
                Text(
                  mfa ? 'Verifica tu acceso' : 'Cuidar, un día a la vez.',
                  style: Theme.of(context).textTheme.headlineLarge,
                ),
                const SizedBox(height: 12),
                Text(
                  mfa ? 'Tu cuenta mantiene la protección de la plataforma.' : 'Ingresa con la misma cuenta que creaste en la web de VIGIA.',
                ),
                const SizedBox(height: 28),
                if (!mfa) ...[
                  TextField(
                    controller: user,
                    decoration: const InputDecoration(
                      labelText: 'Correo o usuario',
                    ),
                    autofillHints: const [AutofillHints.username],
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: password,
                    obscureText: true,
                    decoration: const InputDecoration(labelText: 'Contraseña'),
                    onSubmitted: (_) {
                      if (!busy) submit();
                    },
                  ),
                ] else
                  TextField(
                    controller: code,
                    decoration: const InputDecoration(
                      labelText: 'Código de verificación',
                    ),
                    onSubmitted: (_) {
                      if (!busy) submit();
                    },
                  ),
                if (message != null)
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    child: Text(
                      message!,
                      style: TextStyle(
                        color: Theme.of(context).colorScheme.error,
                      ),
                    ),
                  ),
                const SizedBox(height: 20),
                FilledButton(
                  onPressed: busy ? null : submit,
                  child: Text(
                    busy
                        ? 'Comprobando…'
                        : mfa
                        ? 'Verificar'
                        : 'Ingresar',
                  ),
                ),
                if (!mfa) ...[
                  const SizedBox(height: 12),
                  OutlinedButton.icon(
                    onPressed: busy ? null : google,
                    icon: const Icon(Icons.account_circle_outlined),
                    label: const Text('Continuar con Google'),
                  ),
                  TextButton(
                    onPressed: busy
                        ? null
                        : () async {
                            final opened = await launchUrl(
                              Uri.parse(
                                '${widget.api.baseUrl}/accounts/signup/',
                              ),
                              mode: LaunchMode.externalApplication,
                            );
                            if (!opened && mounted) {
                              setState(
                                () => message = 'No se pudo abrir el registro web. Inténtalo desde tu navegador.',
                              );
                            }
                          },
                    child: const Text('Crear cuenta en la web'),
                  ),
                  TextButton(
                    onPressed: () => launchUrl(
                      Uri.parse(
                        '${widget.api.baseUrl}/accounts/password/reset/',
                      ),
                      mode: LaunchMode.externalApplication,
                    ),
                    child: const Text('Recuperar contraseña'),
                  ),
                ] else
                  TextButton(
                    onPressed: busy
                        ? null
                        : () async {
                            await widget.api.forget();
                            if (mounted) setState(() => mfa = false);
                          },
                    child: const Text('Volver al ingreso'),
                  ),
              ],
            ),
          ),
        ),
      ),
    ),
  );
}
