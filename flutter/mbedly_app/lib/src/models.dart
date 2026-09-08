/// Data models for the Mbedly API - mirror of `mbedly.engine.MediaItem` and
/// the `/jobs` / `/history` payloads.

class MediaItem {
  final String url;
  final String kind;
  final String title;
  final String channel;

  const MediaItem({
    required this.url,
    required this.kind,
    this.title = '',
    this.channel = '',
  });

  bool get hasTitle => title.isNotEmpty;

  factory MediaItem.fromJson(Map<String, dynamic> json) => MediaItem(
        url: (json['url'] as String?) ?? '',
        kind: (json['kind'] as String?) ?? '',
        title: (json['title'] as String?) ?? '',
        channel: (json['channel'] as String?) ?? '',
      );

  Map<String, dynamic> toJson() => {
        'url': url,
        'kind': kind,
        'title': title,
        'channel': channel,
      };
}

enum JobStatus {
  queued,
  working,
  done,
  error;

  static JobStatus fromString(String? s) {
    switch (s) {
      case 'queued':
        return JobStatus.queued;
      case 'working':
        return JobStatus.working;
      case 'done':
        return JobStatus.done;
      case 'error':
        return JobStatus.error;
      default:
        return JobStatus.queued;
    }
  }
}

class Job {
  final String id;
  final String url;
  final String kind;
  final String quality;
  final JobStatus status;
  final int downloaded;
  final int total;
  final double speed;
  final String filename;
  final String error;

  const Job({
    required this.id,
    required this.url,
    required this.kind,
    required this.quality,
    required this.status,
    required this.downloaded,
    required this.total,
    required this.speed,
    required this.filename,
    required this.error,
  });

  double get fraction =>
      total <= 0 ? 0.0 : (downloaded / total).clamp(0.0, 1.0).toDouble();

  factory Job.fromJson(Map<String, dynamic> json) => Job(
        id: (json['id'] as String?) ?? '',
        url: (json['url'] as String?) ?? '',
        kind: (json['kind'] as String?) ?? '',
        quality: (json['quality'] as String?) ?? '',
        status: JobStatus.fromString(json['status'] as String?),
        downloaded: (json['downloaded'] as num?)?.toInt() ?? 0,
        total: (json['total'] as num?)?.toInt() ?? 0,
        speed: (json['speed'] as num?)?.toDouble() ?? 0.0,
        filename: (json['filename'] as String?) ?? '',
        error: (json['error'] as String?) ?? '',
      );
}

class HistoryEntry {
  final String url;
  final String title;
  final String quality;
  final String destination;
  final String at;

  const HistoryEntry({
    required this.url,
    required this.title,
    required this.quality,
    required this.destination,
    required this.at,
  });

  factory HistoryEntry.fromJson(Map<String, dynamic> json) => HistoryEntry(
        url: (json['url'] as String?) ?? '',
        title: (json['title'] as String?) ?? '',
        quality: (json['quality'] as String?) ?? '',
        destination: (json['destination'] as String?) ?? '',
        at: (json['at'] as String?) ?? '',
      );
}
