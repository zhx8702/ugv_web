# -*- coding: utf-8 -*-
"""
Audio Service
音频控制服务 - 支持音频播放和TTS语音合成
基于原ugv_rpi/audio_ctrl.py重构
"""
import os
import queue
import re
import random
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class AudioService:
    """
    音频控制服务
    支持音频文件播放和TTS语音合成
    """

    def __init__(self, config=None):
        self.config = config or {}
        self.mock_mode = self.config.get('mock_mode', False)

        self.audio_path = Path(self.config.get('audio_path', './sounds'))
        self.audio_path.mkdir(parents=True, exist_ok=True)

        (self.audio_path / 'robot_started').mkdir(exist_ok=True)
        (self.audio_path / 'connected').mkdir(exist_ok=True)
        (self.audio_path / 'others').mkdir(exist_ok=True)

        self.volume = self.config.get('default_volume', 0.5)
        self.tts_rate = self.config.get('tts_rate', 150)
        self.min_time_between = self.config.get('min_time_between', 0.5)
        self.tts_engine_pref = str(self.config.get('tts_engine', 'auto')).lower()
        self.tts_voice = self.config.get('tts_voice', 'zh-CN-XiaoxiaoNeural')

        self.playing = False
        self.play_event = threading.Event()
        self.play_event.clear()
        self._stop_requested = threading.Event()
        self._tts_proc = None
        self._tts_lock = threading.Lock()
        self._job_queue = queue.Queue(maxsize=8)

        self.mixer_available = False
        self.tts_available = False
        self.tts_engine_name = None
        self.tts_engine = None
        self._espeak_bin = None
        self._edge_cmd = None
        self.pygame = None

        self._init_mixer()
        self._init_tts()
        if not self.mock_mode:
            threading.Thread(target=self._worker_loop, daemon=True, name='audio-worker').start()

        logger.info(f'AudioService initialized (mock_mode={self.mock_mode})')

    def _init_mixer(self):
        if self.mock_mode:
            logger.info('AudioService: mixer in mock mode')
            return

        try:
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.set_volume(self.volume)
            self.pygame = pygame
            self.mixer_available = True
            logger.info('pygame mixer initialized')
        except Exception as e:
            self.pygame = None
            self.mixer_available = False
            logger.warning(f'pygame mixer not available: {e}')

    def _init_tts(self):
        if self.mock_mode:
            self.tts_available = True
            self.tts_engine_name = 'mock'
            logger.info('AudioService: TTS in mock mode')
            return

        pref = self.tts_engine_pref
        tried = []
        if pref in ('auto', '', 'edge'):
            if self._init_edge():
                tried.append('edge')
        if pref in ('auto', '', 'espeak') or (pref == 'edge' and not tried):
            if self._init_espeak():
                tried.append('espeak')
        if not tried and pref in ('auto', '', 'pyttsx3'):
            if self._init_pyttsx3():
                tried.append('pyttsx3')

        if tried:
            self.tts_available = True
            self.tts_engine_name = '+'.join(tried)
            logger.info(f'TTS engines ready: {self.tts_engine_name}')
            return

        self.tts_available = False
        self.tts_engine_name = None
        logger.warning('TTS not available: install espeak/espeak-ng or edge-tts')

    def _init_espeak(self) -> bool:
        binary = shutil.which('espeak-ng') or shutil.which('espeak')
        if not binary:
            return False
        try:
            subprocess.run(
                [binary, '--version'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=3,
                check=False,
            )
        except Exception:
            return False
        self._espeak_bin = binary
        logger.info(f'espeak binary: {binary}')
        return True

    def _init_edge(self) -> bool:
        module_cmd = [sys.executable, '-m', 'edge_tts']
        try:
            result = subprocess.run(
                module_cmd + ['--help'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
                check=False,
            )
            if result.returncode == 0:
                self._edge_cmd = module_cmd
                logger.info('edge-tts module available')
                return True
        except Exception:
            pass
        binary = shutil.which('edge-tts')
        if binary:
            self._edge_cmd = [binary]
            logger.info(f'edge-tts binary: {binary}')
            return True
        return False

    def _init_pyttsx3(self) -> bool:
        try:
            import pyttsx3
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', self.tts_rate)
            logger.info('pyttsx3 TTS engine initialized')
            return True
        except Exception as e:
            self.tts_engine = None
            logger.warning(f'pyttsx3 TTS not available: {e}')
            return False

    @staticmethod
    def _contains_cjk(text: str) -> bool:
        return bool(re.search(r'[\u4e00-\u9fff]', text or ''))

    def _resolve_audio_path(self, filepath) -> Path:
        """Resolve a relative or absolute audio path without doubling audio_path."""
        p = Path(filepath)
        if p.is_absolute():
            return p

        direct = self.audio_path / p
        if direct.exists():
            return direct

        # play_random used to pass sounds/connected/x.mp3 while audio_path is .../sounds
        if len(p.parts) > 1 and p.parts[0] in (self.audio_path.name, 'sounds'):
            stripped = self.audio_path / Path(*p.parts[1:])
            return stripped

        return direct

    def _enqueue(self, kind: str, payload, interrupt: bool = False) -> bool:
        if self.mock_mode:
            logger.info(f'[MOCK] enqueue {kind}: {payload}')
            return True

        if interrupt:
            self.stop()

        try:
            self._job_queue.put_nowait((kind, payload))
            return True
        except queue.Full:
            logger.warning('Audio queue full')
            return False

    def _worker_loop(self):
        while True:
            job = self._job_queue.get()
            if job is None:
                self._job_queue.task_done()
                break
            kind, payload = job
            self._stop_requested.clear()
            self.playing = True
            self.play_event.set()
            try:
                if kind == 'file':
                    self._play_audio(payload)
                elif kind == 'tts':
                    self._speak(payload)
            except Exception as e:
                logger.error(f'Audio worker error: {e}')
            finally:
                self.playing = False
                self.play_event.clear()
                self._job_queue.task_done()

    def play_file(self, filepath: str, force: bool = False) -> bool:
        if self.mock_mode:
            logger.info(f'[MOCK] Playing audio: {filepath}')
            return True

        if not self.mixer_available:
            logger.warning('Mixer not available')
            return False

        resolved = self._resolve_audio_path(filepath)
        if not resolved.exists():
            logger.error(f'Audio file not found: {resolved}')
            return False

        return self._enqueue('file', str(resolved), interrupt=force)

    def _play_audio(self, filepath: str):
        try:
            self.pygame.mixer.music.load(filepath)
            self.pygame.mixer.music.set_volume(self.volume)
            self.pygame.mixer.music.play()

            while self.pygame.mixer.music.get_busy():
                if self._stop_requested.is_set():
                    self.pygame.mixer.music.stop()
                    break
                time.sleep(0.08)

            time.sleep(self.min_time_between)
        except Exception as e:
            logger.error(f'Error playing audio: {e}')

    def play_random(self, category: str, force: bool = False) -> bool:
        if self.mock_mode:
            logger.info(f'[MOCK] Playing random audio from: {category}')
            return True

        if not self.mixer_available:
            logger.warning('Mixer not available')
            return False

        category_path = self.audio_path / category
        if not category_path.exists():
            logger.error(f'Category not found: {category}')
            return False

        audio_files = [
            f for f in os.listdir(category_path)
            if f.endswith(('.mp3', '.wav', '.ogg'))
        ]

        if not audio_files:
            logger.warning(f'No audio files in category: {category}')
            return False

        audio_file = random.choice(audio_files)
        return self.play_file(f'{category}/{audio_file}', force=force)

    def speak(self, text: str, interrupt: bool = False) -> bool:
        text = (text or '').strip()
        if not text:
            return False

        if self.mock_mode:
            logger.info(f'[MOCK] TTS speaking: {text}')
            return True

        if not self.tts_available:
            logger.warning('TTS not available')
            return False

        return self._enqueue('tts', text, interrupt=interrupt)

    def _speak(self, text: str):
        media_path = None
        try:
            use_edge = self._edge_cmd and (self._contains_cjk(text) or self.tts_engine_pref == 'edge')
            if use_edge:
                media_path = self._edge_to_file(text)
            if not media_path and self._espeak_bin:
                media_path = self._espeak_to_wav(text)
            if media_path and not self._stop_requested.is_set():
                self._play_wav(media_path)
            elif self.tts_engine and not media_path:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            elif not media_path:
                logger.warning('No TTS backend produced audio')
        except Exception as e:
            logger.error(f'Error in TTS: {e}')
        finally:
            if media_path:
                try:
                    os.unlink(media_path)
                except OSError:
                    pass

    def _edge_to_file(self, text: str):
        suffix = '.mp3'
        fd, out_path = tempfile.mkstemp(prefix='ugv-tts-', suffix=suffix)
        os.close(fd)
        voice = self.tts_voice if self._contains_cjk(text) else 'en-US-JennyNeural'
        cmd = self._edge_cmd + [
            '--voice', voice,
            '--text', text,
            '--write-media', out_path,
        ]
        try:
            with self._tts_lock:
                self._tts_proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                )
                proc = self._tts_proc
            proc.wait(timeout=45)
            if proc.returncode != 0 or not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
                err = (proc.stderr.read() if proc.stderr else b'')[:300]
                logger.warning(f'edge-tts failed, will fall back: {err!r}')
                try:
                    os.unlink(out_path)
                except OSError:
                    pass
                return None
            return out_path
        except Exception as e:
            logger.warning(f'edge-tts error, will fall back: {e}')
            try:
                os.unlink(out_path)
            except OSError:
                pass
            return None
        finally:
            with self._tts_lock:
                self._tts_proc = None

    def _espeak_to_wav(self, text: str):
        fd, wav_path = tempfile.mkstemp(prefix='ugv-tts-', suffix='.wav')
        os.close(fd)
        voice = 'zh' if self._contains_cjk(text) else 'en'
        cmd = [
            self._espeak_bin,
            '-v', voice,
            '-s', str(max(80, min(300, int(self.tts_rate)))),
            '-a', str(max(10, min(200, int(self.volume * 200)))),
            '-w', wav_path,
            text,
        ]
        try:
            with self._tts_lock:
                self._tts_proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                )
                proc = self._tts_proc
            proc.wait(timeout=30)
            if proc.returncode != 0 or not os.path.exists(wav_path) or os.path.getsize(wav_path) == 0:
                err = (proc.stderr.read() if proc.stderr else b'')[:200]
                logger.error(f'espeak failed: {err!r}')
                os.unlink(wav_path)
                return None
            return wav_path
        except Exception as e:
            logger.error(f'espeak synthesize error: {e}')
            try:
                os.unlink(wav_path)
            except OSError:
                pass
            return None
        finally:
            with self._tts_lock:
                self._tts_proc = None

    def _play_wav(self, wav_path: str):
        if not self.mixer_available:
            subprocess.run(['aplay', '-q', wav_path], timeout=30, check=False)
            return

        self.pygame.mixer.music.load(wav_path)
        self.pygame.mixer.music.set_volume(self.volume)
        self.pygame.mixer.music.play()
        while self.pygame.mixer.music.get_busy():
            if self._stop_requested.is_set():
                self.pygame.mixer.music.stop()
                break
            time.sleep(0.08)
        time.sleep(self.min_time_between)

    def stop(self) -> bool:
        if self.mock_mode:
            logger.info('[MOCK] Stopping audio')
            return True

        try:
            self._stop_requested.set()
            while True:
                try:
                    self._job_queue.get_nowait()
                    self._job_queue.task_done()
                except queue.Empty:
                    break
            with self._tts_lock:
                proc = self._tts_proc
            if proc and proc.poll() is None:
                proc.terminate()
            if self.mixer_available:
                self.pygame.mixer.music.stop()
            self.playing = False
            self.play_event.clear()
            logger.info('Audio stopped')
            return True
        except Exception as e:
            logger.error(f'Error stopping audio: {e}')
            return False

    def set_volume(self, volume: float) -> bool:
        volume = max(0.0, min(1.0, volume))
        self.volume = volume

        if self.mock_mode:
            logger.info(f'[MOCK] Volume set to: {volume}')
            return True

        if not self.mixer_available:
            return False

        try:
            self.pygame.mixer.music.set_volume(volume)
            logger.info(f'Volume set to: {volume}')
            return True
        except Exception as e:
            logger.error(f'Error setting volume: {e}')
            return False

    def get_files(self, category: str = None) -> list:
        files = []
        cats = [category] if category else ['robot_started', 'connected', 'others']
        for cat in cats:
            category_path = self.audio_path / cat
            if not category_path.exists():
                continue
            for f in os.listdir(category_path):
                if f.endswith(('.mp3', '.wav', '.ogg')):
                    files.append({
                        'name': f,
                        'category': cat,
                        'path': f'{cat}/{f}'
                    })
        return files

    def get_status(self) -> dict:
        return {
            'playing': self.playing,
            'volume': self.volume,
            'mixer_available': self.mixer_available,
            'tts_available': self.tts_available,
            'tts_engine': self.tts_engine_name,
            'queue_size': 0 if self.mock_mode else self._job_queue.qsize(),
            'mock_mode': self.mock_mode,
            'audio_path': str(self.audio_path)
        }


_audio_service_instance = None


def get_audio_service(config=None):
    global _audio_service_instance
    if _audio_service_instance is None:
        _audio_service_instance = AudioService(config)
    return _audio_service_instance


def init_audio_service(app_config):
    global _audio_service_instance
    config = {
        'audio_path': app_config.get('AUDIO_PATH', './sounds'),
        'default_volume': app_config.get('AUDIO_DEFAULT_VOLUME', 0.5),
        'tts_rate': app_config.get('AUDIO_TTS_RATE', 150),
        'tts_engine': app_config.get('AUDIO_TTS_ENGINE', 'auto'),
        'tts_voice': app_config.get('AUDIO_TTS_VOICE', 'zh-CN-XiaoxiaoNeural'),
        'min_time_between': app_config.get('AUDIO_MIN_TIME_BETWEEN', 0.5),
        'mock_mode': app_config.get('MOCK_MODE', False)
    }
    _audio_service_instance = AudioService(config)
    return _audio_service_instance
