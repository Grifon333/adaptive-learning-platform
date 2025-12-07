import 'dart:async';
import 'package:adaptive_learning_app/features/auth/domain/bloc/auth_bloc.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

/// Wraps the application to detect user inactivity.
/// Logs out after [duration] of no user interaction.
class SessionTimeoutWrapper extends StatefulWidget {
  const SessionTimeoutWrapper({
    required this.child,
    this.duration = const Duration(hours: 24),
    super.key,
  });

  final Widget child;
  final Duration duration;

  @override
  State<SessionTimeoutWrapper> createState() => _SessionTimeoutWrapperState();
}

class _SessionTimeoutWrapperState extends State<SessionTimeoutWrapper> {
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _resetTimer();
  }

  void _resetTimer() {
    _timer?.cancel();
    _timer = Timer(widget.duration, _logOut);
  }

  void _logOut() {
    // Only logout if currently authenticated
    final state = context.read<AuthBloc>().state;
    if (state is AuthAuthenticated) {
      context.read<AuthBloc>().add(AuthLogoutRequested());
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Session expired due to inactivity.')));
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Listener(
      behavior: HitTestBehavior.translucent,
      onPointerDown: (_) => _resetTimer(),
      onPointerMove: (_) => _resetTimer(),
      onPointerUp: (_) => _resetTimer(),
      child: widget.child,
    );
  }
}
