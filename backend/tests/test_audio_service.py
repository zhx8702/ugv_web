# -*- coding: utf-8 -*-
from pathlib import Path

from app.services.audio_service import AudioService


def test_resolve_does_not_double_sounds_prefix(tmp_path):
    sounds = tmp_path / 'sounds'
    connected = sounds / 'connected'
    connected.mkdir(parents=True)
    sample = connected / 'connected.mp3'
    sample.write_bytes(b'fake')

    svc = AudioService({'mock_mode': True, 'audio_path': str(sounds)})

    resolved = svc._resolve_audio_path('connected/connected.mp3')
    assert resolved == sample

    doubled = svc._resolve_audio_path('sounds/connected/connected.mp3')
    assert doubled == sample
    assert 'sounds/sounds' not in str(doubled)


def test_speak_in_mock_mode_succeeds():
    svc = AudioService({'mock_mode': True, 'audio_path': './sounds'})
    assert svc.speak('hello rover') is True
    assert svc.get_status()['tts_available'] is True


def test_contains_cjk():
    assert AudioService._contains_cjk('你好')
    assert not AudioService._contains_cjk('hello')
