from app.services.media_manager import MediaManager


def test_thumb_path_uses_hidden_cache(tmp_path):
    mgr = MediaManager()
    mgr.videos_path = str(tmp_path)
    thumb = mgr._thumb_path(str(tmp_path / 'run-01.mp4'))
    assert thumb.endswith('/.thumbs/run-01.jpg')
