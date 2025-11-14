import 'package:adaptive_learning_app/app/app_context_ext.dart';
import 'package:adaptive_learning_app/features/auth/domain/bloc/bloc/auth_bloc.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

/// {@template login_screen}
/// Login screen
/// {@endtemplate}
class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  void _submit() {
    if (_formKey.currentState?.validate() ?? false) {
      context.read<AuthBloc>().add(
        AuthLoginRequested(email: _emailController.text, password: _passwordController.text),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(context.l10n.loginScreenTitle)),
      body: BlocConsumer<AuthBloc, AuthState>(
        listener: (context, state) {
          if (state is AuthUnauthenticated && state.error != null) {
            ScaffoldMessenger.of(
              context,
            ).showSnackBar(SnackBar(content: Text('Login failed: ${state.error}'), backgroundColor: Colors.red));
          }
        },
        builder: (context, state) {
          final isLoading = state is AuthLoading;

          return Form(
            key: _formKey,
            child: Padding(
              padding: EdgeInsets.all(16),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  TextFormField(
                    controller: _emailController,
                    decoration: InputDecoration(labelText: context.l10n.emailLabel),
                    keyboardType: TextInputType.emailAddress,
                    validator: (value) => (value?.isEmpty ?? true) ? 'Enter an email' : null,
                  ),
                  TextFormField(
                    controller: _passwordController,
                    decoration: InputDecoration(labelText: context.l10n.passwordLabel),
                    obscureText: true,
                    validator: (value) => (value?.isEmpty ?? true) ? 'Enter a password' : null,
                  ),
                  const SizedBox(height: 20),
                  isLoading
                      ? const CircularProgressIndicator()
                      : ElevatedButton(onPressed: _submit, child: Text(context.l10n.loginButton)),
                  TextButton(
                    onPressed: isLoading ? null : () => context.pushNamed('register'),
                    child: Text(context.l10n.dontHaveAccount),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}
