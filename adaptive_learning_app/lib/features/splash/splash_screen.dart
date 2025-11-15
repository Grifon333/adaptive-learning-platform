import 'package:flutter/material.dart';

/// {@template splash_screen}
/// Application loading screen
/// {@endtemplate}
class SplashScreen extends StatelessWidget {
  const SplashScreen({this.isFullScreen = false, super.key});

  final bool isFullScreen;

  @override
  Widget build(BuildContext context) {
    const splash = Center(child: CircularProgressIndicator());
    if (!isFullScreen) return splash;
    return const MaterialApp(home: Scaffold(body: splash), debugShowCheckedModeBanner: false);
  }
}
