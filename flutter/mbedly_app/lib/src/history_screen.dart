import 'package:flutter/material.dart';

import '../src/api_client.dart';
import '../src/models.dart';

/// Read-only list of past downloads, newest first - mirrors the dashboard's
/// history modal.
class HistoryScreen extends StatefulWidget {
  final ApiClient api;

  const HistoryScreen({super.key, required this.api});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  List<HistoryEntry> _entries = const [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final entries = await widget.api.history();
      final sorted = [...entries]..sort((a, b) => b.at.compareTo(a.at));
      if (mounted) {
        setState(() {
          _entries = sorted;
          _loading = false;
        });
      }
    } on ApiException catch (e) {
      if (mounted) {
        setState(() {
          _error = e.message;
          _loading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('History')),
      body: _error != null
          ? Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Text(_error!,
                    style: TextStyle(color: theme.colorScheme.error)),
              ),
            )
          : _loading
              ? const Center(child: CircularProgressIndicator())
              : _entries.isEmpty
                  ? const Center(child: Text('nothing downloaded yet'))
                  : ListView.separated(
                      padding: const EdgeInsets.all(12),
                      itemCount: _entries.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 8),
                      itemBuilder: (context, i) {
                        final e = _entries[i];
                        return Card(
                          child: ListTile(
                            leading: const Icon(Icons.check_circle_outline),
                            title: Text(
                              e.title.isNotEmpty ? e.title : e.url,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                            subtitle: Text(
                              '${e.quality.isNotEmpty ? '${e.quality}  ·  ' : ''}${e.at}',
                              style: const TextStyle(fontSize: 12),
                            ),
                            trailing: e.destination.isNotEmpty
                                ? IconButton(
                                    tooltip: e.destination,
                                    icon: const Icon(Icons.folder_open, size: 18),
                                    onPressed: () {},
                                  )
                                : null,
                          ),
                        );
                      },
                    ),
    );
  }
}
