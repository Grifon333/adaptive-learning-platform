import 'package:adaptive_learning_app/features/profile/presentation/screens/profile_preferences_screen.dart';
import 'package:flutter/material.dart';
import 'package:adaptive_learning_app/app/app_context_ext.dart';
import 'package:adaptive_learning_app/features/auth/domain/bloc/auth_bloc.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:adaptive_learning_app/features/profile/domain/bloc/profile_bloc.dart';
import 'package:go_router/go_router.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (context) => ProfileBloc(context.di.repositories.profileRepository)..add(ProfileLoadRequested()),
      child: const _ProfileScreenView(),
    );
  }
}

class _ProfileScreenView extends StatelessWidget {
  const _ProfileScreenView();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Profile')),
      body: BlocBuilder<ProfileBloc, ProfileState>(
        builder: (context, state) {
          if (state is ProfileLoading) {
            return const Center(child: CircularProgressIndicator());
          }
          if (state is ProfileError) {
            return Center(child: Text('Error: ${state.message}'));
          }
          if (state is ProfileLoaded) {
            final p = state.profile;
            return ListView(
              padding: const EdgeInsets.all(16),
              children: [
                const CircleAvatar(radius: 40, child: Icon(Icons.person, size: 40)),
                const SizedBox(height: 16),
                Center(
                  child: Text('User ID: ...${p.userId.substring(0, 6)}', style: const TextStyle(color: Colors.grey)),
                ),
                const SizedBox(height: 32),

                Card(
                  child: ListTile(
                    leading: const Icon(Icons.tune, color: Colors.blue),
                    title: const Text('Learning Preferences'),
                    subtitle: const Text('Adjust how AI generates your path'),
                    trailing: const Icon(Icons.arrow_forward_ios, size: 16),
                    onTap: () {
                      Navigator.of(context).push(
                        MaterialPageRoute(
                          builder: (_) => BlocProvider.value(
                            value: context.read<ProfileBloc>(),
                            child: ProfilePreferencesScreen(profile: p),
                          ),
                        ),
                      );
                    },
                  ),
                ),

                const SizedBox(height: 16),
                // Card(
                //   color: Colors.blue.shade50,
                //   child: ListTile(
                //     leading: const Icon(Icons.admin_panel_settings, color: Colors.blue),
                //     title: const Text('Manage Knowledge Graph'),
                //     onTap: () => context.pushNamed('admin_graph'),
                //   ),
                // ),
                Card(
                  color: Colors.blue.shade50,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                    side: BorderSide(color: Colors.blue.shade200),
                  ),
                  child: ListTile(
                    leading: const Icon(Icons.admin_panel_settings, color: Colors.blue),
                    title: const Text(
                      'Manage Knowledge Graph',
                      style: TextStyle(color: Colors.blue, fontWeight: FontWeight.bold),
                    ),
                    trailing: const Icon(Icons.arrow_forward_ios, size: 16, color: Colors.blue),
                    onTap: () => context.pushNamed('admin_graph'),
                  ),
                ),

                const SizedBox(height: 32),
                OutlinedButton(
                  onPressed: () => context.read<AuthBloc>().add(AuthLogoutRequested()),
                  child: const Text('Log Out'),
                ),
              ],
            );
          }
          return const SizedBox.shrink();
        },
      ),
    );
  }
}




// Card(
//                 color: Colors.blue.shade50,
//                 shape: RoundedRectangleBorder(
//                   borderRadius: BorderRadius.circular(12),
//                   side: BorderSide(color: Colors.blue.shade200),
//                 ),
//                 child: ListTile(
//                   leading: const Icon(Icons.admin_panel_settings, color: Colors.blue),
//                   title: const Text(
//                     'Manage Knowledge Graph',
//                     style: TextStyle(color: Colors.blue, fontWeight: FontWeight.bold),
//                   ),
//                   trailing: const Icon(Icons.arrow_forward_ios, size: 16, color: Colors.blue),
//                   onTap: () => context.pushNamed('admin_graph'),
//                 ),
//               ),
