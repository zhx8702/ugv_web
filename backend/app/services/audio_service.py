# -*- coding: utf-8 -*-
"""
Audio Service
音频控制服务 - 支持音频播放和TTS语音合成
基于原ugv_rpi/audio_ctrl.py重构
"""
import os
import random
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
        """
        初始化音频服务

        Args:
            config: 配置字典，包含:
                - audio_path: 音频文件根目录
                - default_volume: 默认音量 (0.0-1.0)
                - tts_rate: TTS语速
                - min_time_between: 播放间隔
                - mock_mode: Mock模式
        """
        self.config = config or {}
        self.mock_mode = self.config.get('mock_mode', False)

        # 音频路径
        self.audio_path = Path(self.config.get('audio_path', './sounds'))
        self.audio_path.mkdir(parents=True, exist_ok=True)

        # 创建子目录
        (self.audio_path / 'robot_started').mkdir(exist_ok=True)
        (self.audio_path / 'connected').mkdir(exist_ok=True)
        (self.audio_path / 'others').mkdir(exist_ok=True)

        # 音频参数
        self.volume = self.config.get('default_volume', 0.5)
        self.tts_rate = self.config.get('tts_rate', 150)
        self.min_time_between = self.config.get('min_time_between', 0.5)

        # 状态
        self.playing = False
        self.play_event = threading.Event()
        self.play_event.clear()

        # 初始化音频引擎
        self.mixer_available = False
        self.tts_available = False

        self._init_mixer()
        self._init_tts()

        logger.info(f'AudioService initialized (mock_mode={self.mock_mode})')

    def _init_mixer(self):
        """初始化pygame mixer"""
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
        """初始化TTS引擎"""
        if self.mock_mode:
            logger.info('AudioService: TTS in mock mode')
            return

        try:
            import pyttsx3
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', self.tts_rate)
            self.tts_available = True
            logger.info('pyttsx3 TTS engine initialized')
        except Exception as e:
            self.tts_engine = None
            self.tts_available = False
            logger.warning(f'pyttsx3 TTS not available: {e}')

    def play_file(self, filepath: str) -> bool:
        """
        播放音频文件

        Args:
            filepath: 音频文件路径（相对于audio_path或绝对路径）

        Returns:
            是否成功开始播放
        """
        if self.mock_mode:
            logger.info(f'[MOCK] Playing audio: {filepath}')
            return True

        if not self.mixer_available:
            logger.warning('Mixer not available')
            return False

        if self.play_event.is_set():
            logger.warning('Audio already playing')
            return False

        # 处理路径
        if not os.path.isabs(filepath):
            filepath = self.audio_path / filepath

        if not os.path.exists(filepath):
            logger.error(f'Audio file not found: {filepath}')
            return False

        self.play_event.set()
        thread = threading.Thread(target=self._play_audio, args=(str(filepath),), daemon=True)
        thread.start()
        return True

    def _play_audio(self, filepath: str):
        """内部播放函数"""
        try:
            self.playing = True
            self.pygame.mixer.music.load(filepath)
            self.pygame.mixer.music.play()

            while self.pygame.mixer.music.get_busy():
                time.sleep(0.1)

            time.sleep(self.min_time_between)
        except Exception as e:
            logger.error(f'Error playing audio: {e}')
        finally:
            self.playing = False
            self.play_event.clear()

    def play_random(self, category: str, force: bool = False) -> bool:
        """
        播放指定类别的随机音频

        Args:
            category: 音频类别目录名 (robot_started, connected, others)
            force: 是否强制播放（忽略当前播放状态）

        Returns:
            是否成功开始播放
        """
        if self.mock_mode:
            logger.info(f'[MOCK] Playing random audio from: {category}')
            return True

        if not self.mixer_available:
            logger.warning('Mixer not available')
            return False

        if self.play_event.is_set() and not force:
            logger.warning('Audio already playing')
            return False

        category_path = self.audio_path / category
        if not category_path.exists():
            logger.error(f'Category not found: {category}')
            return False

        # 获取音频文件列表
        audio_files = [
            f for f in os.listdir(category_path)
            if f.endswith(('.mp3', '.wav', '.ogg'))
        ]

        if not audio_files:
            logger.warning(f'No audio files in category: {category}')
            return False

        # 随机选择
        audio_file = random.choice(audio_files)
        return self.play_file(str(category_path / audio_file))

    def speak(self, text: str) -> bool:
        """
        TTS语音合成

        Args:
            text: 要朗读的文本

        Returns:
            是否成功开始朗读
        """
        if self.mock_mode:
            logger.info(f'[MOCK] TTS speaking: {text}')
            return True

        if not self.tts_available:
            logger.warning('TTS not available')
            return False

        if self.play_event.is_set():
            logger.warning('Audio already playing')
            return False

        self.play_event.set()
        thread = threading.Thread(target=self._speak, args=(text,), daemon=True)
        thread.start()
        return True

    def _speak(self, text: str):
        """内部TTS函数"""
        try:
            self.playing = True
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            logger.error(f'Error in TTS: {e}')
        finally:
            self.playing = False
            self.play_event.clear()

    def stop(self) -> bool:
        """停止当前播放"""
        if self.mock_mode:
            logger.info('[MOCK] Stopping audio')
            return True

        try:
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
        """
        设置音量

        Args:
            volume: 音量值 (0.0-1.0)

        Returns:
            是否成功设置
        """
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
        """
        获取音频文件列表

        Args:
            category: 类别名，None表示获取所有

        Returns:
            音频文件列表
        """
        files = []

        if category:
            category_path = self.audio_path / category
            if category_path.exists():
                for f in os.listdir(category_path):
                    if f.endswith(('.mp3', '.wav', '.ogg')):
                        files.append({
                            'name': f,
                            'category': category,
                            'path': f'{category}/{f}'
                        })
        else:
            # 遍历所有子目录
            for cat in ['robot_started', 'connected', 'others']:
                cat_path = self.audio_path / cat
                if cat_path.exists():
                    for f in os.listdir(cat_path):
                        if f.endswith(('.mp3', '.wav', '.ogg')):
                            files.append({
                                'name': f,
                                'category': cat,
                                'path': f'{cat}/{f}'
                            })

        return files

    def get_status(self) -> dict:
        """获取音频服务状态"""
        return {
            'playing': self.playing,
            'volume': self.volume,
            'mixer_available': self.mixer_available,
            'tts_available': self.tts_available,
            'mock_mode': self.mock_mode,
            'audio_path': str(self.audio_path)
        }


# 全局单例实例
_audio_service_instance = None


def get_audio_service(config=None):
    """
    获取AudioService单例实例

    Args:
        config: 配置字典

    Returns:
        AudioService实例
    """
    global _audio_service_instance
    if _audio_service_instance is None:
        _audio_service_instance = AudioService(config)
    return _audio_service_instance


def init_audio_service(app_config):
    """
    从Flask配置初始化AudioService

    Args:
        app_config: Flask app.config对象
    """
    config = {
        'audio_path': app_config.get('AUDIO_PATH', './sounds'),
        'default_volume': app_config.get('AUDIO_DEFAULT_VOLUME', 0.5),
        'tts_rate': app_config.get('AUDIO_TTS_RATE', 150),
        'min_time_between': app_config.get('AUDIO_MIN_TIME_BETWEEN', 0.5),
        'mock_mode': app_config.get('MOCK_MODE', False)
    }
    return get_audio_service(config)
