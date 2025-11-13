import 'package:flutter/material.dart';

/// {@template error_screen}
/// Screen when a fatal error occurred in the application
/// {@endtemplate}
class ErrorScreen extends StatelessWidget {
  const ErrorScreen({required this.error, required this.stackTrace, super.key, this.onRetry});

  final Object? error;
  final StackTrace? stackTrace;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: Scaffold(
        body: SafeArea(
          child: Center(
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                const Text(
                  'Something went wrong',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                ),
                if (onRetry != null) ...[
                  const SizedBox(height: 16),
                  ElevatedButton(onPressed: onRetry, child: const Text('Reload the application')),
                ],
                const SizedBox(height: 16),
                Text(
                  'Error: $error\n\nStackTrace: $stackTrace',
                  textAlign: TextAlign.left,
                  style: const TextStyle(fontSize: 12),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
