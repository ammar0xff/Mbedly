import 'dart:async';

import 'package:flutter/material.dart';

import '../src/api_client.dart';
import '../src/format.dart';
import '../src/models.dart';

/// Live download jobs: polls `/jobs`, shows each with a progress bar,
/// speed and status - the dashboard's downloads panel as a page.
class DownloadsScreen extends StatefulWidget {
  final ApiClient api;
  final VoidCallback onDismissed;

  const DownloadsScreen({super.key, required this.api, required this.onDismissed});

  @override
  State<DownloadsScreen> createState() => _DownloadsScreenState();
}

class _DownloadsScreenState extends State<DownloadsScreen> {
  List<Job> _jobs = const [];
  bool _loading = true;
  String? _error;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _refresh();
    _timer = Timer.periodic(const Duration(seconds: 1), (_) => _refresh());
  }

  Future<void> _refresh() async {
    try {
      final jobs = await widget.api.jobs();
      if (!mounted) return;
      final allTerminal = jobs.isNotEmpty &&
          jobs.every((j) => j.status == JobStatus.done || j.status == JobStatus.error);
      setState(() {
        _jobs = jobs;
        _loading = false;
        _error = null;
      });
      if (allTerminal) _timer?.cancel();
    } on ApiException catch (e) {
      if (mounted) {
        setState(() {
          _loading = false;
          _error = e.message;
        });
      }
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Downloads'),
        leading: IconButton(
          onPressed: widget.onDismissed,
          icon: const Icon(Icons.arrow_back),
        ),
      ),
      body: _error != null && _jobs.isEmpty
          ? Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Text(_error!,
                    style: TextStyle(color: theme.colorScheme.error)),
              ),
            )
          : _loading && _jobs.isEmpty
              ? const Center(child: CircularProgressIndicator())
              : _jobs.isEmpty
                  ? const Center(child: Text('no downloads yet'))
                  : ListView.separated(
                      padding: const EdgeInsets.all(12),
                      itemCount: _jobs.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 8),
                      itemBuilder: (context, i) => _JobTile(job: _jobs[i]),
                    ),
    );
  }
}

class _JobTile extends StatelessWidget {
  final Job job;
  const _JobTile({required this.job});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final (Color color, String statusText) = switch (job.status) {
      JobStatus.done => (Colors.green, 'done'),
      JobStatus.error => (theme.colorScheme.error, 'error'),
      JobStatus.working => (theme.colorScheme.primary, 'downloading'),
      JobStatus.queued => (theme.colorScheme.outline, 'queued'),
    };

    final speed = job.speed > 0 ? '${formatBytes(job.speed)}/s' : '';
    final progress = job.fraction;
    final pct = (progress * 100).toStringAsFixed(0);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    job.filename.isNotEmpty
                        ? job.filename.split('/').last
                        : job.url,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontWeight: FontWeight.w600),
                  ),
                ),
                const SizedBox(width: 8),
                Text(
                  statusText,
                  style: TextStyle(color: color, fontSize: 12),
                ),
              ],
            ),
            if (job.status == JobStatus.working) ...[
              const SizedBox(height: 8),
              ClipRRect(
                borderRadius: BorderRadius.circular(4),
                child: LinearProgressIndicator(
                  value: progress,
                  minHeight: 8,
                ),
              ),
              const SizedBox(height: 6),
              Text(
                '$pct%   ${formatBytes(job.downloaded)}'
                '${job.total > 0 ? ' / ${formatBytes(job.total)}' : ''}'
                '${speed.isNotEmpty ? '   ·   $speed' : ''}',
                style: const TextStyle(fontSize: 12),
              ),
            ] else if (job.status == JobStatus.done) ...[
              const SizedBox(height: 6),
              Text(
                job.filename,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(fontSize: 12, color: Colors.green),
              ),
            ] else if (job.status == JobStatus.error) ...[
              const SizedBox(height: 6),
              Text(
                job.error,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(fontSize: 12, color: theme.colorScheme.error),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
