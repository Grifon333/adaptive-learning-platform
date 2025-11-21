import 'package:adaptive_learning_app/di/di_container.dart';
import 'package:adaptive_learning_app/features/auth/domain/bloc/auth_bloc.dart';
import 'package:adaptive_learning_app/features/learning_path/domain/bloc/learning_path_bloc.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:provider/provider.dart';

/// {@template depends_providers}
/// Class for implementing global dependencies (DI) and BLoCs
/// {@endtemplate}
final class DependsProviders extends StatelessWidget {
  const DependsProviders({
    required this.child,
    required this.diContainer,
    required this.authBloc,
    required this.learningPathBloc,
    super.key,
  });

  final Widget child;
  final DiContainer diContainer;
  final AuthBloc authBloc;
  final LearningPathBloc learningPathBloc;

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        Provider<DiContainer>.value(value: diContainer),
        BlocProvider.value(value: authBloc),
        BlocProvider.value(value: learningPathBloc),
      ],
      child: child,
    );
  }
}
