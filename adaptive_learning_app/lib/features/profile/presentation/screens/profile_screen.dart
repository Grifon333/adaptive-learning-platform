import 'package:adaptive_learning_app/app/app_context_ext.dart';
import 'package:adaptive_learning_app/features/auth/domain/bloc/auth_bloc.dart';
import 'package:adaptive_learning_app/features/profile/data/dto/student_profile_dto.dart';
import 'package:adaptive_learning_app/features/profile/domain/bloc/profile_bloc.dart';
import 'package:adaptive_learning_app/features/profile/presentation/screens/edit_profile_screen.dart';
import 'package:adaptive_learning_app/features/profile/presentation/screens/profile_preferences_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    // Re-inject Bloc to ensure it lives in this scope or use existing from Di
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
      appBar: AppBar(
        title: const Text('My Profile'),
        actions: [
          BlocBuilder<ProfileBloc, ProfileState>(
            builder: (context, state) {
              if (state is ProfileLoaded) {
                return IconButton(
                  icon: const Icon(Icons.edit),
                  onPressed: () => Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => BlocProvider.value(
                        value: context.read<ProfileBloc>(),
                        child: EditProfileScreen(profile: state.profile),
                      ),
                    ),
                  ),
                );
              }
              return const SizedBox.shrink();
            },
          ),
        ],
      ),
      body: BlocBuilder<ProfileBloc, ProfileState>(
        builder: (context, state) {
          if (state is ProfileLoading) return const Center(child: CircularProgressIndicator());
          if (state is ProfileError) return Center(child: Text('Error: ${state.message}'));

          if (state is ProfileLoaded) {
            final p = state.profile;
            return RefreshIndicator(
              onRefresh: () async => context.read<ProfileBloc>().add(ProfileLoadRequested()),
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  _ProfileHeader(profile: p),
                  const SizedBox(height: 24),
                  _InfoSection(
                    title: "Learning Goals",
                    children: p.learningGoals.isEmpty
                        ? [const Text("No goals set yet.", style: TextStyle(color: Colors.grey))]
                        : p.learningGoals.map((g) => _BulletPoint(g)).toList(),
                  ),
                  const Divider(height: 32),
                  _SettingsTile(
                    icon: Icons.tune,
                    title: "Learning Preferences",
                    subtitle: "Adjust style, pace, and content types",
                    onTap: () => Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (_) => BlocProvider.value(
                          value: context.read<ProfileBloc>(),
                          child: ProfilePreferencesScreen(profile: p),
                        ),
                      ),
                    ),
                  ),
                  _SettingsTile(
                    icon: Icons.admin_panel_settings,
                    title: "Knowledge Graph Admin",
                    subtitle: "Manage concepts and resources",
                    onTap: () => context.pushNamed('admin_graph'),
                  ),
                  const SizedBox(height: 32),
                  OutlinedButton.icon(
                    icon: const Icon(Icons.logout),
                    label: const Text('Log Out'),
                    onPressed: () => context.read<AuthBloc>().add(AuthLogoutRequested()),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: Colors.red,
                      side: const BorderSide(color: Colors.red),
                    ),
                  ),
                ],
              ),
            );
          }
          return const SizedBox.shrink();
        },
      ),
    );
  }
}

class _ProfileHeader extends StatelessWidget {
  const _ProfileHeader({required this.profile});
  final StudentProfileDto profile;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        CircleAvatar(
          radius: 50,
          backgroundImage: profile.avatarUrl != null ? NetworkImage(profile.avatarUrl!) : null,
          child: profile.avatarUrl == null ? const Icon(Icons.person, size: 50) : null,
        ),
        const SizedBox(height: 16),
        Text(profile.fullName, style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold)),
        Text(profile.email, style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Colors.grey)),
        const SizedBox(height: 8),
        Chip(label: Text(profile.role.toUpperCase()), backgroundColor: Colors.blue.shade50),
      ],
    );
  }
}

class _InfoSection extends StatelessWidget {
  const _InfoSection({required this.title, required this.children});
  final String title;
  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        ...children,
      ],
    );
  }
}

class _BulletPoint extends StatelessWidget {
  const _BulletPoint(this.text);
  final String text;
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 4),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text("• ", style: TextStyle(fontWeight: FontWeight.bold)),
        Expanded(child: Text(text)),
      ],
    ),
  );
}

class _SettingsTile extends StatelessWidget {
  const _SettingsTile({required this.icon, required this.title, required this.subtitle, required this.onTap});
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Container(
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(color: Colors.blue.shade50, borderRadius: BorderRadius.circular(8)),
        child: Icon(icon, color: Colors.blue),
      ),
      title: Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
      subtitle: Text(subtitle, style: const TextStyle(fontSize: 12)),
      trailing: const Icon(Icons.chevron_right),
      onTap: onTap,
    );
  }
}
