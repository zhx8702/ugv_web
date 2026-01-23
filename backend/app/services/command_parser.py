# -*- coding: utf-8 -*-
"""
Command Parser Service
命令行解析器 - 兼容原ugv_rpi命令格式
基于原ugv_rpi/app.py的cmdline_ctrl重构
"""
import json
import logging

logger = logging.getLogger(__name__)


class CommandParser:
    """
    命令行解析器
    支持原ugv_rpi格式的命令字符串
    """

    def __init__(self, motor_controller=None, cv_service=None,
                 audio_service=None, video_stream=None):
        """
        初始化命令解析器

        Args:
            motor_controller: 电机控制器
            cv_service: CV视觉服务
            audio_service: 音频服务
            video_stream: 视频流服务
        """
        self.motor = motor_controller
        self.cv = cv_service
        self.audio = audio_service
        self.video = video_stream

        logger.info('CommandParser initialized')

    def set_motor_controller(self, controller):
        """设置电机控制器"""
        self.motor = controller

    def set_cv_service(self, cv_service):
        """设置CV服务"""
        self.cv = cv_service

    def set_audio_service(self, audio_service):
        """设置音频服务"""
        self.audio = audio_service

    def set_video_stream(self, video_stream):
        """设置视频流服务"""
        self.video = video_stream

    def parse(self, command: str) -> dict:
        """
        解析并执行命令字符串

        Args:
            command: 命令字符串

        Returns:
            执行结果字典

        支持的命令格式:
            base -c {"T":1,"L":0.5,"R":0.5}   # 发送JSON命令到硬件
            audio -s "Hello world"             # TTS语音
            audio -v 0.5                       # 设置音量
            audio -p filename.mp3              # 播放音频文件
            cv -r [0,100,100] [10,255,255]    # 设置颜色范围
            cv -s blue                         # 选择预设颜色
            cv -m 10303                        # 设置CV模式
            video -q 80                        # 设置视频质量
            send -a -b                         # ESP-NOW广播
        """
        if not command or not command.strip():
            return {'error': 'Empty command'}

        try:
            args = command.strip().split()
            cmd = args[0].lower()

            handlers = {
                'base': self._handle_base,
                'audio': self._handle_audio,
                'cv': self._handle_cv,
                'video': self._handle_video,
                'send': self._handle_send,
                'track': self._handle_track,
                'line': self._handle_line,
            }

            if cmd in handlers:
                return handlers[cmd](args[1:])
            else:
                return {'error': f'Unknown command: {cmd}'}

        except Exception as e:
            logger.error(f'Command parse error: {e}')
            return {'error': str(e)}

    def _handle_base(self, args: list) -> dict:
        """
        处理base命令
        格式: base -c {"T":1,"L":0.5,"R":0.5}
        """
        if not args:
            return {'error': 'Missing arguments for base command'}

        if args[0] in ['-c', '--cmd']:
            if len(args) < 2:
                return {'error': 'Missing JSON data'}

            try:
                # 合并剩余参数为JSON字符串
                json_str = ' '.join(args[1:])
                json_data = json.loads(json_str)

                if self.motor:
                    result = self.motor.send_json_command(json_data)
                    return {'success': True, 'result': result}
                else:
                    return {'error': 'Motor controller not available'}

            except json.JSONDecodeError as e:
                return {'error': f'Invalid JSON: {e}'}

        return {'error': f'Unknown base option: {args[0]}'}

    def _handle_audio(self, args: list) -> dict:
        """
        处理audio命令
        格式:
            audio -s "Hello"    # TTS
            audio -v 0.5        # 音量
            audio -p file.mp3   # 播放文件
        """
        if not args:
            return {'error': 'Missing arguments for audio command'}

        if not self.audio:
            return {'error': 'Audio service not available'}

        if args[0] in ['-s', '--say']:
            if len(args) < 2:
                return {'error': 'Missing text'}
            text = ' '.join(args[1:])
            success = self.audio.speak(text)
            return {'success': success, 'action': 'speak', 'text': text}

        elif args[0] in ['-v', '--volume']:
            if len(args) < 2:
                return {'error': 'Missing volume value'}
            try:
                volume = float(args[1])
                success = self.audio.set_volume(volume)
                return {'success': success, 'action': 'volume', 'value': volume}
            except ValueError:
                return {'error': 'Invalid volume value'}

        elif args[0] in ['-p', '--play', '--play_file']:
            if len(args) < 2:
                return {'error': 'Missing file path'}
            filepath = args[1]
            success = self.audio.play_file(filepath)
            return {'success': success, 'action': 'play', 'file': filepath}

        elif args[0] in ['--stop']:
            success = self.audio.stop()
            return {'success': success, 'action': 'stop'}

        return {'error': f'Unknown audio option: {args[0]}'}

    def _handle_cv(self, args: list) -> dict:
        """
        处理cv命令
        格式:
            cv -r [0,100,100] [10,255,255]  # 颜色范围
            cv -s blue                       # 选择颜色
            cv -m 10303                      # 设置模式
        """
        if not args:
            return {'error': 'Missing arguments for cv command'}

        if not self.cv:
            return {'error': 'CV service not available'}

        if args[0] in ['-r', '--range']:
            if len(args) < 3:
                return {'error': 'Missing color range values'}
            try:
                lower = json.loads(args[1])
                upper = json.loads(args[2])
                self.cv.set_color_range(lower, upper)
                return {'success': True, 'action': 'color_range',
                        'lower': lower, 'upper': upper}
            except (json.JSONDecodeError, ValueError) as e:
                return {'error': f'Invalid color values: {e}'}

        elif args[0] in ['-s', '--select']:
            if len(args) < 2:
                return {'error': 'Missing color name'}
            color_name = args[1].lower()
            color_map = {
                'red': ([0, 200, 170], [10, 255, 255]),
                'green': ([50, 130, 130], [78, 255, 255]),
                'blue': ([90, 160, 150], [105, 255, 255]),
            }
            if color_name in color_map:
                lower, upper = color_map[color_name]
                self.cv.set_color_range(lower, upper)
                return {'success': True, 'action': 'select_color',
                        'color': color_name}
            else:
                return {'error': f'Unknown color: {color_name}'}

        elif args[0] in ['-m', '--mode']:
            if len(args) < 2:
                return {'error': 'Missing mode value'}
            try:
                mode = int(args[1])
                self.cv.set_mode(mode)
                return {'success': True, 'action': 'set_mode', 'mode': mode}
            except ValueError:
                return {'error': 'Invalid mode value'}

        elif args[0] in ['-l', '--lock']:
            self.cv.set_motion_lock(True)
            return {'success': True, 'action': 'motion_lock', 'locked': True}

        elif args[0] in ['-u', '--unlock']:
            self.cv.set_motion_lock(False)
            return {'success': True, 'action': 'motion_lock', 'locked': False}

        return {'error': f'Unknown cv option: {args[0]}'}

    def _handle_video(self, args: list) -> dict:
        """
        处理video命令
        格式:
            video -q 80     # 设置质量
            video -z 2      # 设置缩放
        """
        if not args:
            return {'error': 'Missing arguments for video command'}

        if not self.video:
            return {'error': 'Video stream not available'}

        if args[0] in ['-q', '--quality']:
            if len(args) < 2:
                return {'error': 'Missing quality value'}
            try:
                quality = int(args[1])
                self.video.set_quality(quality)
                return {'success': True, 'action': 'quality', 'value': quality}
            except ValueError:
                return {'error': 'Invalid quality value'}

        elif args[0] in ['-z', '--zoom']:
            if len(args) < 2:
                return {'error': 'Missing zoom value'}
            try:
                zoom = int(args[1])
                self.video.set_zoom(zoom)
                return {'success': True, 'action': 'zoom', 'value': zoom}
            except ValueError:
                return {'error': 'Invalid zoom value'}

        return {'error': f'Unknown video option: {args[0]}'}

    def _handle_send(self, args: list) -> dict:
        """
        处理send命令（ESP-NOW）
        格式:
            send -a -b          # 添加广播地址
            send -rm -b         # 移除广播地址
        """
        if not args:
            return {'error': 'Missing arguments for send command'}

        if not self.motor:
            return {'error': 'Motor controller not available'}

        if args[0] in ['-a', '--add']:
            if len(args) >= 2 and args[1] in ['-b', '--broadcast']:
                self.motor.send_json_command({"T": 303, "mac": "FF:FF:FF:FF:FF:FF"})
                return {'success': True, 'action': 'add_broadcast'}
            elif len(args) >= 2:
                mac = args[1]
                self.motor.send_json_command({"T": 303, "mac": mac})
                return {'success': True, 'action': 'add_peer', 'mac': mac}

        elif args[0] in ['-rm', '--remove']:
            if len(args) >= 2 and args[1] in ['-b', '--broadcast']:
                self.motor.send_json_command({"T": 304, "mac": "FF:FF:FF:FF:FF:FF"})
                return {'success': True, 'action': 'remove_broadcast'}
            elif len(args) >= 2:
                mac = args[1]
                self.motor.send_json_command({"T": 304, "mac": mac})
                return {'success': True, 'action': 'remove_peer', 'mac': mac}

        return {'error': f'Unknown send option: {args[0]}'}

    def _handle_track(self, args: list) -> dict:
        """
        处理track命令
        格式:
            track -c 0.023     # 颜色追踪步长
            track -f 0.045     # 人脸追踪步长
            track -s 60        # 速度系数
            track -a 0.4       # 加速度系数
        """
        if not args or len(args) < 2:
            return {'error': 'Missing arguments for track command'}

        if not self.cv:
            return {'error': 'CV service not available'}

        try:
            value = float(args[1])

            if args[0] in ['-c', '--color_iterate']:
                self.cv.track_color_iterate = value
                return {'success': True, 'action': 'track_color_iterate', 'value': value}

            elif args[0] in ['-f', '--faces_iterate']:
                self.cv.track_faces_iterate = value
                return {'success': True, 'action': 'track_faces_iterate', 'value': value}

            elif args[0] in ['-s', '--speed']:
                self.cv.track_spd_rate = value
                return {'success': True, 'action': 'track_spd_rate', 'value': value}

            elif args[0] in ['-a', '--acc']:
                self.cv.track_acc_rate = value
                return {'success': True, 'action': 'track_acc_rate', 'value': value}

        except ValueError:
            return {'error': 'Invalid value'}

        return {'error': f'Unknown track option: {args[0]}'}

    def _handle_line(self, args: list) -> dict:
        """
        处理line命令（巡线参数）
        格式:
            line -r [25,150,70] [42,255,255]  # 颜色范围
            line -s 0.6 0.9 1.5 0.005 0.5 0.3 0.1  # 参数设置
        """
        if not args:
            return {'error': 'Missing arguments for line command'}

        if not self.cv:
            return {'error': 'CV service not available'}

        if args[0] in ['-r', '--range']:
            if len(args) < 3:
                return {'error': 'Missing color range values'}
            try:
                lower = json.loads(args[1])
                upper = json.loads(args[2])
                self.cv.set_line_color(lower, upper)
                return {'success': True, 'action': 'line_color',
                        'lower': lower, 'upper': upper}
            except (json.JSONDecodeError, ValueError) as e:
                return {'error': f'Invalid color values: {e}'}

        elif args[0] in ['-s', '--set']:
            if len(args) < 8:
                return {'error': 'Need 7 parameters'}
            try:
                self.cv.sampling_line_1 = float(args[1])
                self.cv.sampling_line_2 = float(args[2])
                self.cv.slope_impact = float(args[3])
                self.cv.base_impact = float(args[4])
                self.cv.speed_impact = float(args[5])
                self.cv.line_track_speed = float(args[6])
                self.cv.slope_on_speed = float(args[7])
                return {'success': True, 'action': 'line_params'}
            except ValueError:
                return {'error': 'Invalid parameter values'}

        return {'error': f'Unknown line option: {args[0]}'}


# 全局单例实例
_command_parser_instance = None


def get_command_parser():
    """获取CommandParser单例实例"""
    global _command_parser_instance
    if _command_parser_instance is None:
        _command_parser_instance = CommandParser()
    return _command_parser_instance
