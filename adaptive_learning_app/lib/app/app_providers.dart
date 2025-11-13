import 'package:adaptive_learning_app/l10n/localization_notifier.dart';
import 'package:flutter/widgets.dart';
import 'package:provider/provider.dart';

/// {@template app_providers}
/// Class for adding theme providers and localization
/// {@endtemplate}
final class AppProviders extends StatelessWidget {
  const AppProviders({required this.child, super.key});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        // TODO: Add ThemeNotifier
        ChangeNotifierProvider(create: (_) => LocalizationNotifier()),
      ],
      child: child,
    );
  }
}
