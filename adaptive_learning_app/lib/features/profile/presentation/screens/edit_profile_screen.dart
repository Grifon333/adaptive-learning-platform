import 'package:adaptive_learning_app/features/profile/data/dto/student_profile_dto.dart';
import 'package:adaptive_learning_app/features/profile/domain/bloc/profile_bloc.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

class EditProfileScreen extends StatefulWidget {
  const EditProfileScreen({required this.profile, super.key});
  final StudentProfileDto profile;

  @override
  State<EditProfileScreen> createState() => _EditProfileScreenState();
}

class _EditProfileScreenState extends State<EditProfileScreen> {
  final _formKey = GlobalKey<FormState>();
  late TextEditingController _firstCtrl;
  late TextEditingController _lastCtrl;
  late TextEditingController _timezoneCtrl;
  late List<String> _goals;
  late bool _isPublicProfile;

  @override
  void initState() {
    super.initState();
    _firstCtrl = TextEditingController(text: widget.profile.firstName);
    _lastCtrl = TextEditingController(text: widget.profile.lastName);
    _timezoneCtrl = TextEditingController(text: widget.profile.timezone ?? 'UTC');
    _goals = List.from(widget.profile.learningGoals);
    _isPublicProfile = widget.profile.privacySettings['public_profile'] == true;
  }

  @override
  void dispose() {
    _firstCtrl.dispose();
    _lastCtrl.dispose();
    _timezoneCtrl.dispose();
    super.dispose();
  }

  void _save() {
    if (!_formKey.currentState!.validate()) return;

    context.read<ProfileBloc>().add(
      ProfileUpdateRequested(
        firstName: _firstCtrl.text,
        lastName: _lastCtrl.text,
        timezone: _timezoneCtrl.text,
        learningGoals: _goals,
        privacySettings: {'public_profile': _isPublicProfile},
      ),
    );
    Navigator.pop(context);
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Profile updating...')));
  }

  void _addGoal() {
    final ctrl = TextEditingController();
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("Add Goal"),
        content: TextField(
          controller: ctrl,
          decoration: const InputDecoration(hintText: "e.g. Master Flutter Animations"),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Cancel")),
          ElevatedButton(
            onPressed: () {
              if (ctrl.text.isNotEmpty) {
                setState(() => _goals.add(ctrl.text));
                Navigator.pop(ctx);
              }
            },
            child: const Text("Add"),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Edit Profile'),
        actions: [IconButton(icon: const Icon(Icons.save), onPressed: _save)],
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            const Text("Personal Info", style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: TextFormField(
                    controller: _firstCtrl,
                    decoration: const InputDecoration(labelText: 'First Name', border: OutlineInputBorder()),
                    validator: (v) => v!.isEmpty ? 'Required' : null,
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: TextFormField(
                    controller: _lastCtrl,
                    decoration: const InputDecoration(labelText: 'Last Name', border: OutlineInputBorder()),
                    validator: (v) => v!.isEmpty ? 'Required' : null,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _timezoneCtrl,
              decoration: const InputDecoration(
                labelText: 'Timezone',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.map),
              ),
            ),
            const Divider(height: 32),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text("Learning Goals", style: TextStyle(fontWeight: FontWeight.bold)),
                TextButton.icon(onPressed: _addGoal, icon: const Icon(Icons.add), label: const Text("Add")),
              ],
            ),
            ..._goals.asMap().entries.map(
              (entry) => ListTile(
                dense: true,
                title: Text(entry.value),
                trailing: IconButton(
                  icon: const Icon(Icons.close, color: Colors.red),
                  onPressed: () => setState(() => _goals.removeAt(entry.key)),
                ),
              ),
            ),
            const Divider(height: 32),
            SwitchListTile(
              title: const Text("Public Profile"),
              subtitle: const Text("Allow other students to see your achievements"),
              value: _isPublicProfile,
              onChanged: (val) => setState(() => _isPublicProfile = val),
            ),
          ],
        ),
      ),
    );
  }
}
