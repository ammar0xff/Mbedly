"""Tests for the Mbedly engine - no network calls required."""

from mbedly import engine


class TestExtractLinks:
    def test_pulls_urls_out_of_raw_html(self):
        html = (
            '<a href="https://youtu.be/abcdefghijk">x</a> '
            '<iframe src=\'https://player.example/v.mp4\'></iframe>'
            "text with https://example.org/a[b] bare urls"
        )
        links = engine.extract_links(html)
        assert "https://youtu.be/abcdefghijk" in links
        assert "https://player.example/v.mp4" in links
        assert "https://example.org/a[b]" in links or "https://example.org/a" in links

    def test_deduplicates_and_sorts(self):
        html = 'https://a.example/1 "https://a.example/1" https://b.example/2'
        assert engine.extract_links(html) == ["https://a.example/1", "https://b.example/2"]

    def test_filters_noise_records(self):
        html = "https://youtu.be/x https://link.example/channel/one"
        links = engine.extract_links(html)
        assert "https://youtu.be/x" in links
        assert all("channel" not in u for u in links)

    def test_ignores_non_http(self):
        assert engine.extract_links("just words and ftp://x") == []


class TestClassify:
    def test_youtube_shapes(self):
        assert engine.classify("https://youtu.be/abcDEFghijk") == "youtube"
        assert engine.classify("https://www.youtube.com/watch?v=abcDEFghijk") == "youtube"
        assert engine.classify("https://www.youtube.com/embed/abcDEFghijk") == "youtube"
        assert engine.classify("https://www.youtube.com/shorts/abcDEFghijk") == "youtube"

    def test_facebook(self):
        assert engine.classify("https://www.facebook.com/watch/?v=12345") == "facebook"

    def test_livi_video(self):
        assert engine.classify("https://cdn.liiivideo.com/embed/abc") == "livi-video"

    def test_native_media(self):
        assert engine.classify("https://cdn.example/v.mp4") == "mp4"
        assert engine.classify("https://cdn.example/live.m3u8") == "m3u8"

    def test_unknown(self):
        assert engine.classify("https://example.com/page") == "other"


class TestYouTubeId:
    def test_watch(self):
        assert engine.youtube_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_short_url(self):
        assert engine.youtube_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_embed_and_shorts(self):
        assert engine.youtube_id("https://www.youtube.com/embed/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
        assert engine.youtube_id("https://www.youtube.com/shorts/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_no_id(self):
        assert engine.youtube_id("https://example.com/not-a-video") is None


class TestFormatFor:
    def test_height_selectors(self):
        assert "height<=144" in engine.format_for("144p")
        assert "height<=2160" in engine.format_for("4k")
        assert "height<=1440" in engine.format_for("2k")
        assert "bestaudio" in engine.format_for("mp3")

    def test_all_qualities_valid(self):
        for q in engine.QUALITIES:
            assert engine.format_for(q)


class TestMaharatech:
    def test_course_detection(self):
        assert engine.is_maharatech_course("https://maharatech.gov.eg/course/view.php?id=1")
        assert not engine.is_maharatech_course("https://maharatech.gov.eg/other")


class TestPlaylist:
    def test_detection(self):
        assert engine.is_youtube_playlist("https://www.youtube.com/playlist?list=PLabc123")
        assert not engine.is_youtube_playlist("https://www.youtube.com/watch?v=aaaaaaaaaaa")
        assert not engine.is_youtube_playlist("https://example.com/playlist?list=x")

    def test_expand(self, monkeypatch):
        class FakeEntry:
            def __init__(self, vid, title, channel=None):
                self.data = {
                    "id": vid,
                    "title": title,
                    "channel": channel or "",
                    "uploader": channel or "",
                }
            def get(self, key, default=None):
                return self.data.get(key, default)

        fake_entries = [
            FakeEntry("aaaaaaaaaaa", "lesson one", "mychannel"),
            FakeEntry("bbbbbbbbbbb", "lesson two", "mychannel"),
            FakeEntry("ccccccccccc", "", ""),
        ]
        fake_info = {
            "entries": fake_entries,
            "channel": "mychannel",
            "uploader": "mychannel",
        }

        class FakeYDL:
            def __init__(self, *a, **k):
                self.calls = (a, k)
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False
            def extract_info(self, url, download):
                assert download is False
                return fake_info

        monkeypatch.setattr(engine.yt_dlp, "YoutubeDL", FakeYDL)
        items = engine.expand_playlist("https://www.youtube.com/playlist?list=PLabc123")
        assert len(items) == 3
        assert items[0].title == "lesson one"
        assert items[0].channel == "mychannel"
        assert items[0].url == "https://www.youtube.com/watch?v=aaaaaaaaaaa"
        assert items[0].kind == "youtube"
        # entry without its own channel/uploader falls back to the playlist channel
        assert items[2].channel == "mychannel"

    def test_scrape_expands_playlist(self, monkeypatch):
        seen = []

        class FakeYDL:
            def __init__(self, *a, **k):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False
            def extract_info(self, url, download):
                seen.append(url)
                return {"entries": [
                    {"id": "aaaaaaaaaaa", "title": "ep 1", "channel": "c"},
                    {"id": "bbbbbbbbbbb", "title": "ep 2", "channel": "c"},
                ]}

        monkeypatch.setattr(engine.yt_dlp, "YoutubeDL", FakeYDL)
        items = engine.scrape("https://www.youtube.com/playlist?list=PLabc123")
        assert len(items) == 2
        assert all(i.kind == "youtube" for i in items)
        assert items[1].title == "ep 2"
        assert "PLabc123" in seen[0]

    def test_scrape_playlist_fallback_on_error(self, monkeypatch):
        class BoomYDL:
            def __init__(self, *a, **k):
                pass
            def __enter__(self):
                raise Exception("network down")
            def __exit__(self, *a):
                return False

        monkeypatch.setattr(engine.yt_dlp, "YoutubeDL", BoomYDL)
        # falls back to a single item (not a crash)
        items = engine.scrape("https://www.youtube.com/playlist?list=PLabc123")
        assert len(items) == 1
        assert items[0].kind == "youtube"