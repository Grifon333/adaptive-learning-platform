import 'package:flutter/widgets.dart';
import 'package:provider/provider.dart';

// Function type for building a widget with localization in mind
typedef LocalizationBuilder = Widget Function();

/// {@template localization_consumer}
/// Widget for subscribing to localization changes.
/// {@endtemplate}
class LocalizationConsumer extends StatelessWidget {
  const LocalizationConsumer({required this.builder, super.key});

  final LocalizationBuilder builder;

  @override
  Widget build(BuildContext context) {
    return Consumer<LocalizationNotifier>(builder: (_, _, _) => builder());
  }
}

/// {@template localization_notifier}
/// Class for managing application localization
/// {@endtemplate}
final class LocalizationNotifier extends ChangeNotifier {
  LocalizationNotifier();

  // TODO: change to 'uk', 'UA'
  Locale _locale = const Locale('en', 'US');

  Locale get locale => _locale;

  void changeLocal(Locale locale) {
    _locale = locale;
    notifyListeners();
  }
}
