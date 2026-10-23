import 'package:flutter/material.dart';

import '../../core/api.dart';
import '../home/care_home.dart';
import 'login_screen.dart';

class SessionGate extends StatefulWidget {
  final VigiaApi api;
  const SessionGate({super.key, required this.api});
  @override
  State<SessionGate> createState() => _SessionGateState();
}

class _SessionGateState extends State<SessionGate> {
  bool loading = true, signed = false;
  @override
  void initState() {
    super.initState();
    restore();
  }

  Future<void> restore() async {
    try {
      await widget.api.restore();
      if (widget.api.token != null) {
        await widget.api.get('me');
        signed = true;
      }
    } catch (e) {
      if (e is ApiError && e.status == 401) await widget.api.forget();
    }
    if (mounted) setState(() => loading = false);
  }

  @override
  Widget build(BuildContext context) => loading
      ? const Scaffold(body: Center(child: CircularProgressIndicator()))
      : signed
      ? CareHome(
          api: widget.api,
          onLogout: () {
            if (mounted) setState(() => signed = false);
          },
        )
      : LoginScreen(
          api: widget.api,
          onSuccess: () => setState(() => signed = true),
        );
}
