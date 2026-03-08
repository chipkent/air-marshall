import 'package:flutter/material.dart';

void main() {
  runApp(const App());
}

/// Root widget for the air-marshall mobile application.
class App extends StatelessWidget {
  const App({super.key});

  @override
  Widget build(BuildContext context) {
    return const MaterialApp(
      title: 'air-marshall',
      home: Scaffold(body: Center(child: Text('air-marshall'))),
    );
  }
}
