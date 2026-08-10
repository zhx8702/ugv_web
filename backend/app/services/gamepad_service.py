"""Server-side Linux joystick support for locally connected gamepads."""
import logging
import os
import struct
import threading
import time

from app.services.base_controller import get_base_controller

logger = logging.getLogger(__name__)

JS_EVENT_BUTTON = 0x01
JS_EVENT_AXIS = 0x02
JS_EVENT_INIT = 0x80
JS_EVENT = struct.Struct('IhBB')


class GamepadService:
    """Read a Linux /dev/input/js* device and control the rover safely."""

    def __init__(self, config):
        self.device = config.get('GAMEPAD_DEVICE', '/dev/input/js0')
        self.deadzone = float(config.get('GAMEPAD_DEADZONE', 0.12))
        self.max_speed = float(config.get('GAMEPAD_MAX_SPEED', 1.3))
        self.gimbal_speed = float(config.get('GAMEPAD_GIMBAL_SPEED', 45.0))
        self.controller = get_base_controller()
        self.armed = False
        self.speed_mode = 'mid'
        self.speed = 0.66
        self.axes = {0: 0.0, 1: 0.0, 3: 0.0, 4: 0.0}
        self.pan = 0.0
        self.tilt = 0.0
        self._connected = threading.Event()
        self._thread = None
        self._gimbal_thread = None

    def start(self):
        if self._thread is None:
            self._thread = threading.Thread(target=self._run, daemon=True, name='gamepad-input')
            self._thread.start()
            self._gimbal_thread = threading.Thread(target=self._run_gimbal, daemon=True, name='gamepad-gimbal')
            self._gimbal_thread.start()

    def _run(self):
        while True:
            try:
                with open(self.device, 'rb', buffering=0) as joystick:
                    logger.info('Gamepad connected: %s', self.device)
                    self._connected.set()
                    self._read_events(joystick)
            except FileNotFoundError:
                logger.info('Gamepad waiting for %s', self.device)
            except OSError as error:
                logger.warning('Gamepad input error: %s', error)
            finally:
                self._connected.clear()
                self._disarm()
            time.sleep(1)

    def _read_events(self, joystick):
        while True:
            event = joystick.read(JS_EVENT.size)
            if len(event) != JS_EVENT.size:
                raise OSError('gamepad device disconnected')
            _, value, event_type, number = JS_EVENT.unpack(event)
            event_type &= ~JS_EVENT_INIT

            if event_type == JS_EVENT_AXIS and number in self.axes:
                self.axes[number] = self._normalize_axis(value)
                if number in (0, 1):
                    self._drive()
            elif event_type == JS_EVENT_BUTTON and value:
                if number == 7:  # Xbox Start: toggle drive enable.
                    self.armed = not self.armed
                    logger.info('Gamepad drive %s', 'enabled' if self.armed else 'disabled')
                    if not self.armed:
                        self._stop()
                elif number == 1:  # Xbox B: immediate stop and disarm.
                    self._disarm()
                elif number == 0:  # Xbox A: slow speed.
                    self._set_speed_mode('slow', 0.2)
                elif number == 2:  # Xbox X: medium speed.
                    self._set_speed_mode('mid', 0.66)
                elif number == 3:  # Xbox Y: fast speed.
                    self._set_speed_mode('fast', self.max_speed)

    def _normalize_axis(self, value):
        normalized = value / 32767.0
        return 0.0 if abs(normalized) < self.deadzone else normalized

    def _drive(self):
        if not self.armed:
            return
        throttle = -self.axes[1]
        steering = self.axes[0]
        left = throttle + steering
        right = throttle - steering
        scale = max(1.0, abs(left), abs(right))
        self.controller.base_speed_ctrl(
            round(left / scale * self.speed, 3),
            round(right / scale * self.speed, 3),
        )

    def _run_gimbal(self):
        interval = 0.05
        while True:
            if self._connected.is_set() and self.armed:
                pan_input = self.axes[3]
                tilt_input = self.axes[4]
                if pan_input or tilt_input:
                    self.pan = max(-90.0, min(90.0, self.pan + pan_input * self.gimbal_speed * interval))
                    self.tilt = max(-60.0, min(60.0, self.tilt - tilt_input * self.gimbal_speed * interval))
                    self.controller.gimbal_ctrl(round(self.pan, 1), round(self.tilt, 1))
            time.sleep(interval)

    def _set_speed_mode(self, mode, speed):
        self.speed_mode = mode
        self.speed = speed
        logger.info('Gamepad speed mode: %s (%.2f)', mode, speed)

    def _stop(self):
        self.controller.base_speed_ctrl(0, 0)

    def _disarm(self):
        if self.armed:
            logger.info('Gamepad drive disabled')
        self.armed = False
        self._stop()


_service = None


def start_gamepad_service(config):
    global _service
    if _service is None:
        _service = GamepadService(config)
        _service.start()
    return _service
