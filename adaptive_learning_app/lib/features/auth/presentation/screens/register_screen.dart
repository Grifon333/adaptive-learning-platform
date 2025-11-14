import 'package:adaptive_learning_app/app/app_context_ext.dart';
import 'package:adaptive_learning_app/features/auth/domain/bloc/bloc/auth_bloc.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

/// {@template register_screen}
/// Registration screen
/// {@endtemplate}
class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _firstNameController = TextEditingController();
  final _lastNameController = TextEditingController();

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _firstNameController.dispose();
    _lastNameController.dispose();
    super.dispose();
  }

  void _submit() {
    if (_formKey.currentState?.validate() ?? false) {
      context.read<AuthBloc>().add(
        AuthRegisterRequested(
          email: _emailController.text,
          password: _passwordController.text,
          firstName: _firstNameController.text,
          lastName: _lastNameController.text,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(context.l10n.registerScreenTitle)),
      body: BlocConsumer<AuthBloc, AuthState>(
        listener: (context, state) {
          if (state is AuthUnauthenticated && state.error != null) {
            ScaffoldMessenger.of(
              context,
            ).showSnackBar(SnackBar(content: Text('Registration Failed: ${state.error}'), backgroundColor: Colors.red));
          }
          if (state is AuthRegisterSuccess) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Registration Successful! Please login.'), backgroundColor: Colors.green),
            );
          }
        },
        builder: (context, state) {
          final isLoading = state is AuthLoading;

          return Form(
            key: _formKey,
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: ListView(
                children: [
                  TextFormField(
                    controller: _firstNameController,
                    decoration: InputDecoration(labelText: context.l10n.firstNameLabel),
                    validator: (value) => (value?.isEmpty ?? true) ? 'Enter first name' : null,
                  ),
                  TextFormField(
                    controller: _lastNameController,
                    decoration: InputDecoration(labelText: context.l10n.lastNameLabel),
                    validator: (value) => (value?.isEmpty ?? true) ? 'Enter last name' : null,
                  ),
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
                      : ElevatedButton(onPressed: _submit, child: Text(context.l10n.registerButton)),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}
