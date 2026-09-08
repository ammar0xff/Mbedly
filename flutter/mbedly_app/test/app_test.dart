import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:mbedly_app/main.dart';
import 'package:mbedly_app/src/api_client.dart';
import 'package:mbedly_app/src/downloads_screen.dart';
import 'package:mbedly_app/src/history_screen.dart';
import 'package:mbedly_app/src/models.dart';

/// In-memory ApiClient; never touches the network.
class FakeApiClient extends ApiClient {
  final List<String> downloadCalls = [];
  final List<String> requestedQualities = [];

  @override
  Future<List<String>> qualities() async => [
        '144p', '360p', '480p', '720p', '1080p', '2k', '4k', 'mp3',
      ];

  @override
  Future<List<MediaItem>> scrape(String url) async {
    if (url.contains('404')) throw ApiException('boom');
    return [
      MediaItem(
        url: 'https://youtu.be/abc',
        kind: 'youtube',
        title: 'Lesson One',
        channel: 'My Channel',
      ),
      MediaItem(
        url: 'https://youtu.be/def',
        kind: 'youtube',
        title: 'Lesson Two',
        channel: 'My Channel',
      ),
    ];
  }

  @override
  Future<List<String>> download(List<String> urls,
      {String quality = '1080p'}) async {
    downloadCalls.addAll(urls);
    return urls.map((u) => 'j-$u').toList();
  }

  @override
  Future<List<Job>> jobs() async => [
        const Job(
          id: 'j1',
          url: 'https://youtu.be/abc',
          kind: 'youtube',
          quality: '720p',
          status: JobStatus.working,
          downloaded: 50,
          total: 100,
          speed: 1000,
          filename: 'lesson.mp4',
          error: '',
        ),
      ];

  @override
  Future<List<HistoryEntry>> history() async => const [
        HistoryEntry(
          url: 'https://youtu.be/abc',
          title: 'Lesson One',
          quality: '720p',
          destination: '/data/media/lesson.mp4',
          at: '2026-01-01T10:00:00',
        ),
      ];
}

Widget wrap(Widget child) => MaterialApp(home: child);

void main() {
  testWidgets('home shows empty state and analyzes a URL', (tester) async {
    final api = FakeApiClient();
    await tester.pumpWidget(
      wrap(Root(api: api)),
    );

    expect(find.text('mbedly'), findsOneWidget);
    expect(find.text('Paste a URL to find its videos'), findsOneWidget);

    await tester.enterText(find.byType(TextField), 'https://youtube.com/playlist?list=X');
    await tester.tap(find.text('Analyze URL'));
    await tester.pumpAndSettle();

    expect(find.text('Lesson One'), findsOneWidget);
    expect(find.text('Lesson Two'), findsOneWidget);
    expect(find.text('My Channel  ·  youtube'), findsNWidgets(2));
  });

  testWidgets('scrape error surfaces to the user', (tester) async {
    final api = FakeApiClient();
    await tester.pumpWidget(wrap(Root(api: api)));

    await tester.enterText(find.byType(TextField), 'https://youtube.com/404');
    await tester.tap(find.text('Analyze URL'));
    await tester.pumpAndSettle();

    expect(find.text('boom'), findsOneWidget);
  });

  testWidgets('downloading selected items navigates to downloads and calls API',
      (tester) async {
    final api = FakeApiClient();
    await tester.pumpWidget(wrap(Root(api: api)));

    await tester.enterText(find.byType(TextField), 'https://youtube.com/playlist?list=X');
    await tester.tap(find.text('Analyze URL'));
    await tester.pumpAndSettle();

    // select the first item via its checkbox
    await tester.tap(find.byType(Checkbox).first);
    await tester.pumpAndSettle();

    await tester.tap(find.text('Download 1'));
    await tester.pumpAndSettle();

    expect(api.downloadCalls, contains('https://youtu.be/abc'));
    // downloads page shown (bottom nav index 1)
    expect(find.text('Downloads'), findsWidgets);
  });

  testWidgets('history screen shows an entry', (tester) async {
    final api = FakeApiClient();
    await tester.pumpWidget(wrap(HistoryScreen(api: api)));
    await tester.pumpAndSettle();

    expect(find.text('Lesson One'), findsOneWidget);
    expect(find.textContaining('720p'), findsOneWidget);
  });

  testWidgets('downloads screen shows live progress', (tester) async {
    final api = FakeApiClient();
    await tester.pumpWidget(wrap(DownloadsScreen(api: api, onDismissed: () {})));
    await tester.pumpAndSettle();

    expect(find.text('lesson.mp4'), findsOneWidget);
    expect(find.textContaining('50%'), findsOneWidget);
  });
}
