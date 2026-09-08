import 'package:flutter/material.dart';

import '../src/api_client.dart';
import '../src/models.dart';
import '../src/quality_selector.dart';

/// The main screen: paste a URL, hit "analyze", see every video with its
/// resolved title, then download the selection or everything.
class HomeScreen extends StatefulWidget {
  final ApiClient api;
  final void Function(List<String> urls, String quality) startDownload;
  final void Function() openHistory;

  const HomeScreen({
    super.key,
    required this.api,
    required this.startDownload,
    required this.openHistory,
  });

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final TextEditingController _urlController = TextEditingController();
  List<MediaItem> _items = const [];
  bool _scraping = false;
  String? _error;
  final Set<String> _selected = <String>{};
  String _quality = '1080p';
  List<String> _qualities = const ['1080p'];

  @override
  void initState() {
    super.initState();
    _loadQualities();
  }

  Future<void> _loadQualities() async {
    try {
      final q = await widget.api.qualities();
      var sel = _quality;
      if (!q.contains(sel) && q.isNotEmpty) sel = q.first;
      if (mounted) {
        setState(() {
          _qualities = q;
          _quality = sel;
        });
      }
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    }
  }

  Future<void> _analyze() async {
    final url = _urlController.text.trim();
    if (url.isEmpty) {
      setState(() => _error = 'enter a URL first');
      return;
    }
    setState(() {
      _scraping = true;
      _error = null;
      _items = const [];
      _selected.clear();
    });
    try {
      final items = await widget.api.scrape(url);
      if (!mounted) return;
      setState(() {
        _items = items;
        if (items.isEmpty) _error = 'no media found at that URL';
      });
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _scraping = false);
    }
  }

  List<String> get _selectedUrls =>
      _items.where((i) => _selected.contains(i.url)).map((i) => i.url).toList();

  void _startDownload({bool onlySelection = false}) {
    final urls = onlySelection
        ? _selectedUrls
        : _items.map((i) => i.url).toList();
    if (urls.isEmpty) return;
    widget.startDownload(urls, _quality);
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('downloading ${urls.length} item(s)…')),
    );
  }

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('mbedly'),
        actions: [
          IconButton(
            tooltip: 'history',
            onPressed: widget.openHistory,
            icon: const Icon(Icons.history),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          TextField(
            controller: _urlController,
            decoration: const InputDecoration(
              labelText: 'URL',
              hintText: 'page, playlist, or direct video link',
              border: OutlineInputBorder(),
              prefixIcon: Icon(Icons.link),
            ),
            onSubmitted: (_) => _analyze(),
          ),
          const SizedBox(height: 12),
          QualitySelector(
            qualities: _qualities,
            selected: _quality,
            onChanged: (q) => setState(() => _quality = q),
          ),
          const SizedBox(height: 12),
          FilledButton.icon(
            onPressed: _scraping ? null : _analyze,
            icon: _scraping
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.search),
            label: Text(_scraping ? 'analyzing…' : 'Analyze URL'),
          ),
          if (_error != null)
            Padding(
              padding: const EdgeInsets.only(top: 12),
              child: Text(
                _error!,
                style: TextStyle(color: theme.colorScheme.error),
              ),
            ),
          const SizedBox(height: 16),
          if (_items.isNotEmpty) ...[
            Row(
              children: [
                Text('${_items.length} item(s)',
                    style: theme.textTheme.titleMedium),
                const Spacer(),
                TextButton(
                  onPressed: () => setState(() {
                    if (_selected.length == _items.length) {
                      _selected.clear();
                    } else {
                      _selected.addAll(_items.map((i) => i.url));
                    }
                  }),
                  child: Text(
                    _selected.length == _items.length
                        ? 'deselect all'
                        : 'select all',
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Card(
              clipBehavior: Clip.antiAlias,
              child: ListView.separated(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: _items.length,
                separatorBuilder: (_, __) => const Divider(height: 1),
                itemBuilder: (context, i) {
                  final item = _items[i];
                  return ListTile(
                    dense: true,
                    leading: Checkbox(
                      value: _selected.contains(item.url),
                      onChanged: (v) => setState(() {
                        if (v == true) {
                          _selected.add(item.url);
                        } else {
                          _selected.remove(item.url);
                        }
                      }),
                    ),
                    title: Text(
                      item.hasTitle ? item.title : '(unknown title)',
                      style: const TextStyle(fontSize: 14),
                    ),
                    subtitle: Text(
                      item.hasTitle && item.channel.isNotEmpty
                          ? '${item.channel}  ·  ${item.kind}'
                          : item.kind,
                      style: const TextStyle(fontSize: 12),
                    ),
                  );
                },
              ),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: _items.isEmpty ? null : () => _startDownload(),
                    icon: const Icon(Icons.download_done),
                    label: const Text('Download all'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: FilledButton.icon(
                    onPressed: _selectedUrls.isEmpty || _items.isEmpty
                        ? null
                        : () => _startDownload(onlySelection: true),
                    icon: const Icon(Icons.download),
                    label: Text(
                      _selected.isNotEmpty
                          ? 'Download ${_selected.length}'
                          : 'Download all',
                    ),
                  ),
                ),
              ],
            ),
          ] else
            Center(
              child: Padding(
                padding: const EdgeInsets.only(top: 48),
                child: Text(
                  'Paste a URL to find its videos',
                  style: TextStyle(color: theme.colorScheme.outline),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
