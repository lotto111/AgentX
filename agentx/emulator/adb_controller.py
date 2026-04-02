# -*- coding: utf-8 -*-
"""
通用 ADB 操作封装
提供点击、滑动、输入文本、截图等常用 ADB 操作
"""

import subprocess
import time
import os
from typing import List, Optional

from agentx.utils.logger import get_logger

logger = get_logger(__name__)


class ADBController:
    """
    通用 ADB 操作控制器

    封装常用的 Android Debug Bridge 操作，包括触摸事件、截图、应用管理等。
    """

    def __init__(
        self,
        device: str = "127.0.0.1:5555",
        adb_path: str = "adb",
    ) -> None:
        """
        初始化 ADB 控制器

        Args:
            device: 设备地址（如 127.0.0.1:5555）
            adb_path: adb 可执行文件路径
        """
        self.device = device
        self.adb_path = adb_path

    def tap(self, x: int, y: int) -> bool:
        """
        点击指定坐标

        Args:
            x: 横坐标
            y: 纵坐标

        Returns:
            是否执行成功
        """
        try:
            logger.debug(f"点击坐标: ({x}, {y})")
            self._shell(f"input tap {x} {y}")
            time.sleep(0.5)
            return True
        except Exception as e:
            logger.error(f"点击失败 ({x}, {y}): {e}")
            return False

    def swipe(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        duration: int = 500,
    ) -> bool:
        """
        滑动操作

        Args:
            x1: 起始横坐标
            y1: 起始纵坐标
            x2: 结束横坐标
            y2: 结束纵坐标
            duration: 滑动持续时间（毫秒）

        Returns:
            是否执行成功
        """
        try:
            logger.debug(f"滑动: ({x1}, {y1}) -> ({x2}, {y2}), 持续 {duration}ms")
            self._shell(f"input swipe {x1} {y1} {x2} {y2} {duration}")
            time.sleep(0.8)
            return True
        except Exception as e:
            logger.error(f"滑动失败: {e}")
            return False

    def input_text(self, text: str) -> bool:
        """
        在当前焦点输入文本

        Args:
            text: 要输入的文本（仅支持 ASCII，中文需用其他方式）

        Returns:
            是否执行成功
        """
        try:
            logger.debug(f"输入文本: {text}")
            # 对特殊字符进行转义
            escaped = text.replace(" ", "%s").replace("&", "\\&")
            self._shell(f"input text '{escaped}'")
            time.sleep(0.3)
            return True
        except Exception as e:
            logger.error(f"输入文本失败: {e}")
            return False

    def press_key(self, keycode: int) -> bool:
        """
        按下指定按键

        Args:
            keycode: Android 按键代码（如 3=HOME, 4=BACK, 82=MENU）

        Returns:
            是否执行成功
        """
        try:
            logger.debug(f"按键: keycode={keycode}")
            self._shell(f"input keyevent {keycode}")
            time.sleep(0.3)
            return True
        except Exception as e:
            logger.error(f"按键失败 (keycode={keycode}): {e}")
            return False

    def screenshot(self, save_path: str = "/tmp/agentx_screen.png") -> Optional[str]:
        """
        截取设备屏幕并保存到本地

        Args:
            save_path: 本地保存路径

        Returns:
            成功时返回保存路径，失败时返回 None
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)

            remote_path = "/sdcard/agentx_screen.png"
            logger.debug(f"截图中...")

            # 在设备上截图
            self._shell(f"screencap -p {remote_path}")
            time.sleep(0.3)

            # 将截图拉取到本地
            result = subprocess.run(
                [self.adb_path, "-s", self.device, "pull", remote_path, save_path],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )

            if result.returncode == 0 and os.path.exists(save_path):
                logger.debug(f"截图保存至: {save_path}")
                return save_path
            else:
                logger.error(f"截图拉取失败: {result.stderr}")
                return None
        except Exception as e:
            logger.error(f"截图失败: {e}")
            return None

    def get_running_apps(self) -> List[str]:
        """
        获取当前运行中的应用包名列表

        Returns:
            包名列表
        """
        try:
            output = self._shell("ps -A")
            apps = []
            for line in output.splitlines():
                parts = line.split()
                if len(parts) >= 9:
                    package = parts[-1]
                    # 过滤系统进程，只保留包名格式的进程
                    if "." in package and not package.startswith("/"):
                        apps.append(package)
            logger.debug(f"运行中的应用数量: {len(apps)}")
            return apps
        except Exception as e:
            logger.error(f"获取运行中应用失败: {e}")
            return []

    def launch_app(self, package: str, activity: str = "") -> bool:
        """
        启动应用

        Args:
            package: 应用包名
            activity: Activity 名称（可选）

        Returns:
            是否成功启动
        """
        try:
            if activity:
                logger.info(f"启动应用: {package}/{activity}")
                self._shell(
                    f"am start -n {package}/{activity}"
                )
            else:
                logger.info(f"启动应用: {package}")
                self._shell(
                    f"monkey -p {package} -c android.intent.category.LAUNCHER 1"
                )
            time.sleep(2)
            return True
        except Exception as e:
            logger.error(f"启动应用失败 ({package}): {e}")
            return False

    def stop_app(self, package: str) -> bool:
        """
        强制停止应用

        Args:
            package: 应用包名

        Returns:
            是否成功停止
        """
        try:
            logger.info(f"停止应用: {package}")
            self._shell(f"am force-stop {package}")
            time.sleep(1)
            return True
        except Exception as e:
            logger.error(f"停止应用失败 ({package}): {e}")
            return False

    def back(self) -> bool:
        """
        模拟按下返回键

        Returns:
            是否执行成功
        """
        try:
            logger.debug("按下返回键")
            self._shell("input keyevent 4")
            time.sleep(0.5)
            return True
        except Exception as e:
            logger.error(f"返回键失败: {e}")
            return False

    def home(self) -> bool:
        """
        模拟按下 Home 键

        Returns:
            是否执行成功
        """
        try:
            logger.debug("按下 Home 键")
            self._shell("input keyevent 3")
            time.sleep(0.5)
            return True
        except Exception as e:
            logger.error(f"Home 键失败: {e}")
            return False

    def long_tap(self, x: int, y: int, duration: int = 1000) -> bool:
        """
        长按指定坐标

        Args:
            x: 横坐标
            y: 纵坐标
            duration: 长按持续时间（毫秒）

        Returns:
            是否执行成功
        """
        try:
            logger.debug(f"长按坐标: ({x}, {y}), 持续 {duration}ms")
            self._shell(f"input swipe {x} {y} {x} {y} {duration}")
            time.sleep(0.5)
            return True
        except Exception as e:
            logger.error(f"长按失败 ({x}, {y}): {e}")
            return False

    def clear_app_data(self, package: str) -> bool:
        """
        清除应用数据

        Args:
            package: 应用包名

        Returns:
            是否成功清除
        """
        try:
            logger.info(f"清除应用数据: {package}")
            self._shell(f"pm clear {package}")
            time.sleep(1)
            return True
        except Exception as e:
            logger.error(f"清除应用数据失败 ({package}): {e}")
            return False

    def _shell(self, command: str) -> str:
        """
        执行 adb shell 命令

        Args:
            command: shell 命令字符串

        Returns:
            命令输出
        """
        cmd = [self.adb_path, "-s", self.device, "shell"] + command.split()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if result.returncode != 0 and result.stderr:
            logger.warning(f"ADB shell 警告: {result.stderr.strip()}")
        return result.stdout.strip()
