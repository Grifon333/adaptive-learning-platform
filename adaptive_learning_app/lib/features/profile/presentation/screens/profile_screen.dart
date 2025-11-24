import 'package:flutter/material.dart';
import 'package:adaptive_learning_app/app/app_context_ext.dart';
import 'package:adaptive_learning_app/features/auth/domain/bloc/auth_bloc.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:adaptive_learning_app/features/profile/domain/bloc/profile_bloc.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final profileRepository = context.di.repositories.profileRepository;
    final authState = context.read<AuthBloc>().state;
    String userId = 'unknown';
    if (authState is AuthAuthenticated) userId = authState.userId;

    return BlocProvider(
      create: (context) => ProfileBloc(profileRepository)..add(ProfileFetchProfileEvent(id: userId)),
      child: const _ProfileScreenView(),
    );
  }
}

class _ProfileScreenView extends StatelessWidget {
  const _ProfileScreenView();

  void _logout(BuildContext context) {
    context.read<AuthBloc>().add(AuthLogoutRequested());
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Profile')),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              BlocBuilder<ProfileBloc, ProfileState>(
                builder: (context, state) {
                  return switch (state) {
                    ProfileSuccessState() => Card(
                      child: ListTile(
                        leading: const Icon(Icons.person, size: 40),
                        title: Text('Name: ${state.props.first}'),
                        subtitle: const Text('Your level: Beginner'),
                      ),
                    ),
                    ProfileErrorState() => Text('Error: ${state.message}'),
                    _ => const Center(child: CircularProgressIndicator()),
                  };
                },
              ),
              const SizedBox(height: 32),

              ElevatedButton.icon(
                onPressed: () => _logout(context),
                icon: const Icon(Icons.logout),
                label: const Text('Log out'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.red,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
