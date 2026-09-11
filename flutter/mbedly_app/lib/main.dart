import 'package:flutter/material.dart';

import 'src/api_client.dart';
import 'src/downloads_screen.dart';
import 'src/history_screen.dart';
import 'src/home_screen.dart';

void main() {
  const override = String.fromEnvironment('API_BASE_URL');
  runApp(MbedlyApp(api: ApiClient(baseUrl: override.isNotEmpty ? override : defaultApiBase)));
}

/// Where the app looks for the local `mbedly-api` server.
///
/// Override at build time for real devices / remote hosts:
///   flutter build apk --dart-define=API_BASE_URL=http://192.168.1.20:8765
String get defaultApiBase {
  if (!kIsWeb && defaultTargetPlatform == TargetPlatform.android) {
    return 'http://10.0.2.2:8765'; // Android emulator -> host machine
  }
  return 'http://127.0.0.1:8765'; // web / desktop: same machine as the API
}

class MbedlyApp extends StatelessWidget {
  final ApiClient api;

  const MbedlyApp({super.key, required this.api});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'mbedly',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF00FF41),
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
      ),
      home: Root(api: api),
    );
  }
}

class Root extends StatefulWidget {
  final ApiClient api;
  const Root({super.key, required this.api});

  @override
  State<Root> createState() => _RootState();
}

class _RootState extends State<Root> {
  int _index = 0;

  void _openHistory() {
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => HistoryScreen(api: widget.api)),
    );
  }

  Future<void> _startDownload(List<String> urls, String quality) async {
    try {
      await widget.api.download(urls, quality: quality);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('$e')));
    }
    setState(() => _index = 1);
  }

  @override
  Widget build(BuildContext context) {
    final pages = [
      HomeScreen(
        api: widget.api,
        startDownload: _startDownload,
        openHistory: _openHistory,
      ),
      DownloadsScreen(api: widget.api, onDismissed: () => setState(() => _index = 0)),
    ];
    return Scaffold(
      body: IndexedStack(index: _index, children: pages),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (i) => setState(() => _index = i),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.search),
            label: 'Search',
          ),
          NavigationDestination(
            icon: Icon(Icons.download),
            label: 'Downloads',
          ),
        ],
      ),
    );
  }
}
