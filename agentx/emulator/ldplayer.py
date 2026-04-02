# -*- coding: utf-8 -*-
"""
雷电模拟器专用控制模块
负责启动、停止、连接雷电模拟器，并管理 ADB 连接
"""

import subprocess
import time
import os
from typing import Optional, Tuple

from agentx.utils.logger import get_logger
from agentx.emulator.adb_controller import ADBController

logger = get_logger(__name__)


class LDPlayerController:
    """
    雷电模拟器控制器

    封装雷电模拟器（LDPlayer）的启动、停止、ADB 连接等操作。
    默认使用雷电模拟器9的 ADB 端口 5555。
    """

    # 雷电模拟器默认 ADB 端口
    DEFAULT_ADB_PORT: int = 5555

    def __init__(
        self,
        adb_host: str = "127.0.0.1",
        adb_port: int = DEFAULT_ADB_PORT,
        adb_path: str = "adb",
        emulator_exe: str = "C:/LDPlayer/LDPlayer9/dnplayer.exe",
        wait_boot: int = 30,
    ) -> None:
        """
        初始化雷电模拟器控制器

        Args:
            adb_host: ADB 主机地址
            adb_port: ADB 端口（雷电默认 5555）
            adb_path: adb 可执行文件路径
            emulator_exe: 雷电模拟器可执行文件路径
            wait_boot: 等待模拟器启动的时间（秒）
        """
        self.adb_host = adb_host
        self.adb_port = adb_port
        self.adb_path = adb_path
        self.emulator_exe = emulator_exe
        self.wait_boot = wait_boot
        self.device = f"{adb_host}:{adb_port}"
        self._adb: Optional[ADBController] = None

    def start(self) -> bool:
        """
        启动雷电模拟器

        Returns:
            是否成功启动
        """
        try:
            if self.is_running():
                logger.info("雷电模拟器已经在运行中")
                return True

            if not os.path.exists(self.emulator_exe):
                logger.error(f"模拟器可执行文件不存在: {self.emulator_exe}")
                return False

            logger.info(f"启动雷电模拟器: {self.emulator_exe}")
            subprocess.Popen(
                [self.emulator_exe],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            # 等待模拟器启动完成
            logger.info(f"等待模拟器启动（{self.wait_boot} 秒）...")
            time.sleep(self.wait_boot)

            # 尝试连接
            return self.connect()
        except Exception as e:
            logger.error(f"启动雷电模拟器失败: {e}")
            return False

    def stop(self) -> bool:
        """
        关闭雷电模拟器

        Returns:
            是否成功关闭
        """
        try:
            logger.info("正在关闭雷电模拟器...")
            # 先断开 ADB 连接
            self._run_adb_cmd(["disconnect", self.device])
            # 结束模拟器进程
            subprocess.run(
                ["taskkill", "/F", "/IM", "dnplayer.exe"],
                capture_output=True,
                check=False,
            )
            logger.info("雷电模拟器已关闭")
            return True
        except Exception as e:
            logger.error(f"关闭雷电模拟器失败: {e}")
            return False

    def connect(self) -> bool:
        """
        通过 ADB 连接雷电模拟器

        Returns:
            是否连接成功
        """
        try:
            logger.info(f"正在连接 ADB: {self.device}")
            result = self._run_adb_cmd(["connect", self.device])

            if result and ("connected" in result.lower() or "already" in result.lower()):
                logger.info(f"ADB 连接成功: {self.device}")
                self._adb = ADBController(
                    device=self.device,
                    adb_path=self.adb_path,
                )
                return True
            else:
                logger.error(f"ADB 连接失败，输出: {result}")
                return False
        except Exception as e:
            logger.error(f"ADB 连接异常: {e}")
            return False

    def is_running(self) -> bool:
        """
        检查雷电模拟器是否正在运行

        Returns:
            True 表示模拟器正在运行
        """
        try:
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq dnplayer.exe"],
                capture_output=True,
                text=True,
                check=False,
            )
            return "dnplayer.exe" in result.stdout
        except Exception as e:
            logger.warning(f"检查模拟器状态失败: {e}")
            return False

    def get_screen_resolution(self) -> Tuple[int, int]:
        """
        获取模拟器屏幕分辨率

        Returns:
            (宽, 高) 元组
        """
        try:
            result = self._run_adb_shell("wm size")
            if result:
                # 解析输出，如 "Physical size: 1280x720"
                for line in result.splitlines():
                    if "Physical size" in line or "Override size" in line:
                        size_str = line.split(":")[-1].strip()
                        width, height = size_str.split("x")
                        logger.info(f"屏幕分辨率: {width}x{height}")
                        return int(width), int(height)
            logger.warning("无法获取屏幕分辨率，使用默认值 1280x720")
            return 1280, 720
        except Exception as e:
            logger.error(f"获取屏幕分辨率失败: {e}")
            return 1280, 720

    def get_adb_controller(self) -> Optional[ADBController]:
        """
        获取 ADB 控制器实例

        Returns:
            ADBController 实例，未连接时返回 None
        """
        if self._adb is None:
            logger.warning("ADB 未连接，请先调用 connect()")
        return self._adb

    def _run_adb_cmd(self, args: list) -> str:
        """
        运行 adb 命令（不带设备参数）

        Args:
            args: adb 命令参数列表

        Returns:
            命令输出字符串
        """
        try:
            cmd = [self.adb_path] + args
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            logger.error("ADB 命令超时")
            return ""
        except Exception as e:
            logger.error(f"运行 ADB 命令失败: {e}")
            return ""

    def _run_adb_shell(self, command: str) -> str:
        """
        运行 adb shell 命令

        Args:
            command: shell 命令字符串

        Returns:
            命令输出字符串
        """
        try:
            cmd = [self.adb_path, "-s", self.device, "shell"] + command.split()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            logger.error("ADB shell 命令超时")
            return ""
        except Exception as e:
            logger.error(f"运行 ADB shell 命令失败: {e}")
            return ""
