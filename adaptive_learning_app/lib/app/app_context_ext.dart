import 'package:adaptive_learning_app/di/di_container.dart';
import 'package:adaptive_learning_app/l10n/gen/app_localizations.dart';
import 'package:adaptive_learning_app/l10n/localization_notifier.dart';
import 'package:flutter/widgets.dart';
import 'package:provider/provider.dart';

/// {@template app_context_ext}
/// Class that implements the extension for BuildContext
/// {@endtemplate}
extension AppContextExt on BuildContext {
  DiContainer get di => read<DiContainer>();
  AppLocalizations get l10n => AppLocalizations.of(this);
  LocalizationNotifier get localization => read<LocalizationNotifier>();
}
