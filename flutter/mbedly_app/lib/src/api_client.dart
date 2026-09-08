import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import 'models.dart';

/// Thrown when the mbedly-api is unreachable or returns an error.
class ApiException implements Exception {
  final String message;
  ApiException(this.message);
  @override
  String toString() => 'ApiException: $message';
}

/// Thin HTTP client for the local `mbedly-api`.
///
/// Point it at the machine running the Python backend; the default is the
/// local loopback port the `mbedly-api` server listens on.
class ApiClient {
  final String baseUrl;
  final http.Client _http;

  ApiClient({String? baseUrl, http.Client? httpClient})
      : baseUrl = baseUrl ?? 'http://127.0.0.1:8765',
        _http = httpClient ?? http.Client();

  Uri _uri(String path) => Uri.parse('$baseUrl$path');

  Future<Map<String, dynamic>> _get(String path) async {
    try {
      final res = await _http.get(_uri(path)).timeout(const Duration(seconds: 20));
      return _decode(res);
    } on ApiException {
      rethrow;
    } catch (e) {
      throw ApiException('cannot reach mbedly-api at $baseUrl ($e)');
    }
  }

  Future<Map<String, dynamic>> _post(
    String path,
    Map<String, dynamic> body,
  ) async {
    try {
      final res = await _http
          .post(
            _uri(path),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(body),
          )
          .timeout(const Duration(seconds: 120));
      return _decode(res);
    } on ApiException {
      rethrow;
    } catch (e) {
      throw ApiException('cannot reach mbedly-api at $baseUrl ($e)');
    }
  }

  Map<String, dynamic> _decode(http.Response res) {
    final body = jsonDecode(res.body) as Map<String, dynamic>? ?? {};
    if (res.statusCode >= 400) {
      throw ApiException((body['error'] as String?) ?? 'HTTP ${res.statusCode}');
    }
    return body;
  }

  Future<void> checkHealth() async {
    await _get('/health');
  }

  Future<List<String>> qualities() async {
    final data = await _get('/qualities');
    final q = data['qualities'];
    if (q is List) return q.map((e) => e.toString()).toList();
    return const [];
  }

  /// Scrape a URL and resolve titles/channels for every item.
  Future<List<MediaItem>> scrape(String url) async {
    final data = await _post('/scrape', {'url': url});
    final items = (data['items'] as List? ?? const [])
        .map((e) => MediaItem.fromJson(e as Map<String, dynamic>))
        .toList();
    return items;
  }

  /// Start background downloads for the given URLs, in order.
  Future<List<String>> download(List<String> urls, {String quality = '1080p'}) async {
    final data = await _post('/download', {
      'urls': urls,
      'quality': quality,
    });
    final ids = data['job_ids'] as List? ?? const [];
    return ids.map((e) => e.toString()).toList();
  }

  Future<List<Job>> jobs() async {
    final data = await _get('/jobs');
    final list = data['jobs'] as List? ?? const <dynamic>[];
    return list
        .map((e) => Job.fromJson(e as Map<String, dynamic>))
        .toList(growable: true);
  }

  Future<List<HistoryEntry>> history() async {
    final data = await _get('/history');
    final list = data['entries'] as List? ?? const <dynamic>[];
    return list
        .map((e) => HistoryEntry.fromJson(e as Map<String, dynamic>))
        .toList(growable: true);
  }
}
