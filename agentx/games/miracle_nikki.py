# -*- coding: utf-8 -*-
"""
奇迹暖暖（Miracle Nikki）专用游戏逻辑模块
封装游戏启动、登录、每日任务、邮件收取等常用操作
"""

import time
from typing import Optional, Tuple

from agentx.emulator.adb_controller import ADBController
from agentx.utils.logger import get_logger

logger = get_logger(__name__)

# ========================================================
# 游戏常量（基于 1280x720 分辨率）
# 如果使用 1920x1080 分辨率，请按比例缩放坐标
# ========================================================

# 游戏包名和入口 Activity
PACKAGE_NAME = "com.netease.nikki"
MAIN_ACTIVITY = "com.netease.nikki.MainActivity"

# 主界面常用按钮坐标（1280x720）
class Coords720p:
    """1280x720 分辨率下的界面坐标常量"""

    # 登录界面
    LOGIN_USERNAME = (640, 350)       # 用户名输入框
    LOGIN_PASSWORD = (640, 430)       # 密码输入框
    LOGIN_BUTTON = (640, 530)         # 登录按钮

    # 主界面导航
    MAIN_MENU_CLOSE = (1220, 50)      # 关闭弹窗按钮（右上角X）
    MAIN_DAILY_TASK = (80, 360)       # 每日任务入口
    MAIN_MAILBOX = (80, 440)          # 邮件入口
    MAIN_SHOP = (80, 280)             # 商店入口
    MAIN_COMPETE = (80, 520)          # 竞技场入口

    # 签到界面
    SIGN_IN_BUTTON = (640, 550)       # 签到按钮

    # 任务界面
    TASK_COLLECT_ALL = (1100, 650)    # 一键领取所有任务奖励
    TASK_FIRST_ITEM = (640, 200)      # 任务列表第一项

    # 邮件界面
    MAIL_COLLECT_ALL = (1100, 650)    # 一键领取所有邮件
    MAIL_FIRST_ITEM = (640, 200)      # 邮件列表第一封

    # 通用
    CONFIRM_BUTTON = (700, 430)       # 确认/确定按钮
    CANCEL_BUTTON = (580, 430)        # 取消按钮
    CLOSE_POPUP = (640, 580)          # 关闭通用弹窗


# 坐标缩放比例（1920x1080 相对于 1280x720）
SCALE_1080P = (1920 / 1280, 1080 / 720)


def scale_coord(
    coord: Tuple[int, int],
    width: int = 1280,
    height: int = 720,
) -> Tuple[int, int]:
    """
    根据实际分辨率缩放坐标

    Args:
        coord: 基于 1280x720 的坐标
        width: 实际屏幕宽度
        height: 实际屏幕高度

    Returns:
        缩放后的坐标
    """
    sx = width / 1280
    sy = height / 720
    return int(coord[0] * sx), int(coord[1] * sy)


class MiracleNikki:
    """
    奇迹暖暖游戏专用控制器

    封装奇迹暖暖（Miracle Nikki）游戏的常用操作，
    包括启动游戏、自动登录、每日任务、收取邮件等。
    """

    PACKAGE = PACKAGE_NAME
    ACTIVITY = MAIN_ACTIVITY

    def __init__(
        self,
        adb: ADBController,
        screen_width: int = 1280,
        screen_height: int = 720,
        wait_launch: int = 10,
    ) -> None:
        """
        初始化奇迹暖暖控制器

        Args:
            adb: ADB 控制器实例
            screen_width: 屏幕宽度（像素）
            screen_height: 屏幕高度（像素）
            wait_launch: 游戏启动等待时间（秒）
        """
        self.adb = adb
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.wait_launch = wait_launch

    def _coord(self, coord: Tuple[int, int]) -> Tuple[int, int]:
        """根据当前分辨率缩放坐标"""
        return scale_coord(coord, self.screen_width, self.screen_height)

    def launch(self) -> bool:
        """
        启动奇迹暖暖游戏

        Returns:
            是否成功启动
        """
        try:
            logger.info(f"启动奇迹暖暖: {self.PACKAGE}")
            result = self.adb.launch_app(self.PACKAGE, self.ACTIVITY)
            if result:
                logger.info(f"等待游戏加载（{self.wait_launch} 秒）...")
                time.sleep(self.wait_launch)
            return result
        except Exception as e:
            logger.error(f"启动游戏失败: {e}")
            return False

    def stop(self) -> bool:
        """
        退出奇迹暖暖游戏

        Returns:
            是否成功退出
        """
        try:
            logger.info("退出奇迹暖暖")
            return self.adb.stop_app(self.PACKAGE)
        except Exception as e:
            logger.error(f"退出游戏失败: {e}")
            return False

    def login(self, username: str, password: str) -> bool:
        """
        自动登录游戏

        Args:
            username: 游戏账号
            password: 游戏密码

        Returns:
            是否登录成功
        """
        try:
            logger.info(f"尝试登录账号: {username}")

            # 点击用户名输入框
            x, y = self._coord(Coords720p.LOGIN_USERNAME)
            self.adb.tap(x, y)
            time.sleep(0.5)
            self.adb.input_text(username)

            # 点击密码输入框
            x, y = self._coord(Coords720p.LOGIN_PASSWORD)
            self.adb.tap(x, y)
            time.sleep(0.5)
            self.adb.input_text(password)

            # 点击登录按钮
            x, y = self._coord(Coords720p.LOGIN_BUTTON)
            self.adb.tap(x, y)
            time.sleep(5)  # 等待登录结果

            logger.info("登录操作已执行，请检查游戏状态")
            return True
        except Exception as e:
            logger.error(f"登录失败: {e}")
            return False

    def daily_tasks(self) -> bool:
        """
        完成并收取每日任务奖励

        Returns:
            是否成功完成
        """
        try:
            logger.info("执行每日任务领取")

            # 点击每日任务入口
            x, y = self._coord(Coords720p.MAIN_DAILY_TASK)
            self.adb.tap(x, y)
            time.sleep(2)

            # 一键领取所有已完成的任务奖励
            x, y = self._coord(Coords720p.TASK_COLLECT_ALL)
            self.adb.tap(x, y)
            time.sleep(1)

            # 确认领取弹窗（如果有）
            x, y = self._coord(Coords720p.CONFIRM_BUTTON)
            self.adb.tap(x, y)
            time.sleep(1)

            # 关闭任务界面
            self.adb.back()
            logger.info("每日任务领取完成")
            return True
        except Exception as e:
            logger.error(f"完成每日任务失败: {e}")
            return False

    def collect_mail(self) -> bool:
        """
        收取所有邮件奖励

        Returns:
            是否成功收取
        """
        try:
            logger.info("收取邮件")

            # 点击邮件入口
            x, y = self._coord(Coords720p.MAIN_MAILBOX)
            self.adb.tap(x, y)
            time.sleep(2)

            # 一键领取所有邮件附件
            x, y = self._coord(Coords720p.MAIL_COLLECT_ALL)
            self.adb.tap(x, y)
            time.sleep(1)

            # 确认
            x, y = self._coord(Coords720p.CONFIRM_BUTTON)
            self.adb.tap(x, y)
            time.sleep(1)

            # 关闭邮件界面
            self.adb.back()
            logger.info("邮件收取完成")
            return True
        except Exception as e:
            logger.error(f"收取邮件失败: {e}")
            return False

    def sign_in(self) -> bool:
        """
        完成每日签到

        Returns:
            是否签到成功
        """
        try:
            logger.info("执行每日签到")
            # 点击签到按钮（通常在主界面或签到弹窗内）
            x, y = self._coord(Coords720p.SIGN_IN_BUTTON)
            self.adb.tap(x, y)
            time.sleep(1)

            # 确认领取
            x, y = self._coord(Coords720p.CONFIRM_BUTTON)
            self.adb.tap(x, y)
            time.sleep(1)

            logger.info("每日签到完成")
            return True
        except Exception as e:
            logger.error(f"每日签到失败: {e}")
            return False

    def close_popups(self, max_attempts: int = 3) -> None:
        """
        尝试关闭所有弹窗

        Args:
            max_attempts: 最大尝试次数
        """
        logger.info("尝试关闭弹窗")
        for i in range(max_attempts):
            # 先尝试点击右上角关闭按钮
            x, y = self._coord(Coords720p.MAIN_MENU_CLOSE)
            self.adb.tap(x, y)
            time.sleep(0.8)

            # 再尝试通用关闭位置
            x, y = self._coord(Coords720p.CLOSE_POPUP)
            self.adb.tap(x, y)
            time.sleep(0.8)

    def is_game_running(self) -> bool:
        """
        检查游戏是否正在运行

        Returns:
            True 表示游戏正在运行
        """
        try:
            running_apps = self.adb.get_running_apps()
            return any(self.PACKAGE in app for app in running_apps)
        except Exception as e:
            logger.error(f"检查游戏状态失败: {e}")
            return False
