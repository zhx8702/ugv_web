"""
Settings Service
配置管理服务 - 管理机器人配置和用户偏好
"""
import os
import json
import logging
from threading import Lock

logger = logging.getLogger(__name__)

# 默认配置
DEFAULT_SETTINGS = {
    'base_config': {
        'robot_name': 'UGV Rover',
        'main_type': 2,  # 1=RaspRover, 2=UGV Rover, 3=UGV Beast
        'module_type': 0,  # 0=Camera PT, 1=RoArm-M2
        'sbc_version': '0.93'
    },
    'args_config': {
        'max_speed': 1.3,
        'slow_speed': 0.2,
        'mid_rate': 0.66
    },
    'video': {
        'default_quality': 20,
        'default_res_w': 640,
        'default_res_h': 480,
        'stream_type': 'mjpeg'  # 'mjpeg' or 'webrtc'
    },
    'user_preferences': {
        'speed_mode': 'mid',
        'head_light': 'off',
        'base_light': False,
        'zoom_level': 1,
        'detection_type': 'none',
        'keyboard_control': True,
        'vibration': False
    }
}


class SettingsService:
    """配置管理服务"""

    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # 配置文件路径
        self.config_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.config_file = os.path.join(self.config_dir, 'config', 'settings.json')

        # 确保配置目录存在
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

        # 加载或创建配置
        self.settings = self._load_settings()

        self._initialized = True
        logger.info(f"Settings service initialized, config file: {self.config_file}")

    def _load_settings(self) -> dict:
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # 合并默认配置（确保新增字段存在）
                    return self._merge_settings(DEFAULT_SETTINGS, loaded)
            except Exception as e:
                logger.error(f"Failed to load settings: {e}")
                return DEFAULT_SETTINGS.copy()
        else:
            # 创建默认配置文件
            self._save_settings(DEFAULT_SETTINGS)
            return DEFAULT_SETTINGS.copy()

    def _merge_settings(self, default: dict, loaded: dict) -> dict:
        """递归合并配置，保留已有值，添加缺失的默认值"""
        result = default.copy()
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_settings(result[key], value)
            else:
                result[key] = value
        return result

    def _save_settings(self, settings: dict = None) -> bool:
        """保存配置到文件"""
        try:
            data = settings if settings else self.settings
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info("Settings saved successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            return False

    def get_all(self) -> dict:
        """获取所有配置"""
        return self.settings.copy()

    def update_all(self, new_settings: dict) -> bool:
        """更新所有配置"""
        try:
            # 合并新配置
            if 'base_config' in new_settings:
                self.settings['base_config'].update(new_settings['base_config'])
            if 'args_config' in new_settings:
                self.settings['args_config'].update(new_settings['args_config'])
            if 'video' in new_settings:
                self.settings['video'].update(new_settings['video'])
            if 'user_preferences' in new_settings:
                self.settings['user_preferences'].update(new_settings['user_preferences'])

            return self._save_settings()
        except Exception as e:
            logger.error(f"Failed to update settings: {e}")
            return False

    def get_preferences(self) -> dict:
        """获取用户偏好"""
        return self.settings.get('user_preferences', DEFAULT_SETTINGS['user_preferences']).copy()

    def update_preferences(self, preferences: dict) -> bool:
        """更新用户偏好"""
        try:
            self.settings['user_preferences'].update(preferences)
            return self._save_settings()
        except Exception as e:
            logger.error(f"Failed to update preferences: {e}")
            return False

    def reset_to_defaults(self) -> bool:
        """重置为默认配置"""
        try:
            self.settings = DEFAULT_SETTINGS.copy()
            return self._save_settings()
        except Exception as e:
            logger.error(f"Failed to reset settings: {e}")
            return False

    def get_video_config(self) -> dict:
        """获取视频配置"""
        return self.settings.get('video', DEFAULT_SETTINGS['video']).copy()

    def get_speed_config(self) -> dict:
        """获取速度配置"""
        return self.settings.get('args_config', DEFAULT_SETTINGS['args_config']).copy()


# 单例获取函数
_settings_service = None


def get_settings_service() -> SettingsService:
    """获取设置服务单例"""
    global _settings_service
    if _settings_service is None:
        _settings_service = SettingsService()
    return _settings_service
