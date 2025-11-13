import 'package:adaptive_learning_app/di/di_container.dart';
import 'package:flutter/widgets.dart';
import 'package:provider/provider.dart';

/// {@template depends_providers}
/// Class for implementing global dependencies (DI) and BLoCs
/// {@endtemplate}
final class DependsProviders extends StatelessWidget {
  const DependsProviders({required this.child, required this.diContainer, super.key});

  final Widget child;
  final DiContainer diContainer;

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        Provider<DiContainer>.value(value: diContainer),
        // TODO: Global BLoCs
      ],
      child: child,
    );
  }
}
