// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Ukrainian (`uk`).
class AppLocalizationsUk extends AppLocalizations {
  AppLocalizationsUk([String locale = 'uk']) : super(locale);

  @override
  String get helloWorld => 'Привіт, Світ!';

  @override
  String get loginScreenTitle => 'Вхід';

  @override
  String get registerScreenTitle => 'Реєстрація';

  @override
  String get emailLabel => 'Електронна пошта';

  @override
  String get passwordLabel => 'Пароль';

  @override
  String get firstNameLabel => 'Ім\'я';

  @override
  String get lastNameLabel => 'Прізвище';

  @override
  String get loginButton => 'Увійти';

  @override
  String get registerButton => 'Зареєструватися';

  @override
  String get dontHaveAccount => 'Немає акаунту? Зареєструватися';
}
