import 'package:adaptive_learning_app/app/app_context_ext.dart';
import 'package:adaptive_learning_app/app/app_env.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

/// {@template root_screen}
/// Root screen of the application with BottomNavigationBar
/// {@endtemplate}
class RootScreen extends StatefulWidget {
  const RootScreen({required this.navigationShell, super.key});

  final StatefulNavigationShell navigationShell;

  @override
  State<RootScreen> createState() => _RootScreenState();
}

class _RootScreenState extends State<RootScreen> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      // Debug button
      floatingActionButton: context.di.env != AppEnv.prod
          ? FloatingActionButton(
              child: const Icon(Icons.bug_report),
              onPressed: () {
                // TODO: add DebugRoutes
              },
            )
          : null,
      body: widget.navigationShell,
      bottomNavigationBar: BottomNavigationBar(
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.dashboard), label: 'Dashboard'),
          BottomNavigationBarItem(icon: Icon(Icons.person), label: 'Profile'),
        ],
        currentIndex: widget.navigationShell.currentIndex,
        onTap: widget.navigationShell.goBranch,
      ),
    );
  }
}
