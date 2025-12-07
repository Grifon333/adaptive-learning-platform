import 'package:adaptive_learning_app/features/auth/domain/bloc/auth_bloc.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

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

  void _onForgotPassword() {
    final emailCtrl = TextEditingController(text: _emailController.text);
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Reset Password'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('Enter your email to receive a reset link.'),
            const SizedBox(height: 16),
            TextField(
              controller: emailCtrl,
              decoration: const InputDecoration(labelText: 'Email', border: OutlineInputBorder()),
              keyboardType: TextInputType.emailAddress,
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () {
              if (emailCtrl.text.isNotEmpty) {
                context.read<AuthBloc>().add(AuthForgotPasswordRequested(emailCtrl.text));
                Navigator.pop(ctx);
                ScaffoldMessenger.of(
                  context,
                ).showSnackBar(const SnackBar(content: Text('If the account exists, a reset email has been sent.')));
              }
            },
            child: const Text('Send'),
          ),
        ],
      ),
    );
  }

  // Mock Social Login Trigger
  void _mockSocialLogin(String provider) {
    // In a real app, you would use google_sign_in or similar packages here
    // to get the OAuth token and user info.
    // For this implementation, we simulate the data returned by the native SDK.
    context.read<AuthBloc>().add(
      AuthSocialLoginRequested(
        email: 'test_user@$provider.com',
        provider: provider,
        providerId: 'mock_provider_id_123',
        firstName: 'Test',
        lastName: 'User',
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Login')),
      body: BlocConsumer<AuthBloc, AuthState>(
        listener: (context, state) {
          if (state is AuthLoginFailure) {
            ScaffoldMessenger.of(
              context,
            ).showSnackBar(SnackBar(content: Text('Login failed: ${state.error}'), backgroundColor: Colors.red));
          }
        },
        builder: (context, state) {
          final isLoading = state is AuthLoading;

          return Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: Form(
                key: _formKey,
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // --- Email/Pass Form ---
                    TextFormField(
                      controller: _emailController,
                      decoration: const InputDecoration(
                        labelText: 'Email',
                        prefixIcon: Icon(Icons.email_outlined),
                        border: OutlineInputBorder(),
                      ),
                      keyboardType: TextInputType.emailAddress,
                      validator: (value) => (value?.isEmpty ?? true) ? 'Enter an email' : null,
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: _passwordController,
                      decoration: const InputDecoration(
                        labelText: 'Password',
                        prefixIcon: Icon(Icons.lock_outline),
                        border: OutlineInputBorder(),
                      ),
                      obscureText: true,
                      validator: (value) => (value?.isEmpty ?? true) ? 'Enter a password' : null,
                    ),

                    // --- Forgot Password ---
                    Align(
                      alignment: Alignment.centerRight,
                      child: TextButton(
                        onPressed: isLoading ? null : _onForgotPassword,
                        child: const Text('Forgot Password?'),
                      ),
                    ),

                    const SizedBox(height: 8),

                    // --- Login Button ---
                    ElevatedButton(
                      onPressed: isLoading ? null : _submit,
                      style: ElevatedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 16)),
                      child: isLoading
                          ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2))
                          : const Text('Login'),
                    ),

                    const SizedBox(height: 32),

                    // --- Social Login Divider ---
                    const Row(
                      children: [
                        Expanded(child: Divider()),
                        Padding(padding: EdgeInsets.symmetric(horizontal: 16), child: Text('OR')),
                        Expanded(child: Divider()),
                      ],
                    ),
                    const SizedBox(height: 24),

                    // --- Social Buttons ---
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                      children: [
                        _SocialButton(
                          icon: Icons.g_mobiledata, // Replace with actual asset
                          label: 'Google',
                          color: Colors.red,
                          onPressed: isLoading ? null : () => _mockSocialLogin('google'),
                        ),
                        _SocialButton(
                          icon: Icons.window, // Replace with actual asset
                          label: 'Microsoft',
                          color: Colors.blue,
                          onPressed: isLoading ? null : () => _mockSocialLogin('microsoft'),
                        ),
                      ],
                    ),

                    const SizedBox(height: 32),

                    // --- Register Link ---
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Text("Don't have an account?"),
                        TextButton(
                          onPressed: isLoading ? null : () => context.pushNamed('register'),
                          child: const Text('Register'),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}

class _SocialButton extends StatelessWidget {
  const _SocialButton({required this.icon, required this.label, required this.color, this.onPressed});

  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) {
    return OutlinedButton.icon(
      onPressed: onPressed,
      icon: Icon(icon, color: color),
      label: Text(label),
      style: OutlinedButton.styleFrom(padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12)),
    );
  }
}
