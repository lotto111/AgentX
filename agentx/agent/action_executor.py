# -*- coding: utf-8 -*-
"""
操作执行器模块
根据 AI 返回的 JSON 指令执行对应的 ADB 操作
"""

import time
from typing import Any, Dict

from agentx.emulator.adb_controller import ADBController
from agentx.utils.logger import get_logger

logger = get_logger(__name__)

# 各动作执行后的等待时间（秒）
ACTION_WAIT_TIMES: Dict[str, float] = {
    "tap": 1.0,
    "swipe": 1.5,
    "input": 0.8,
    "wait": 2.0,
    "back": 1.0,
    "home": 1.0,
    "done": 0.0,
}


class ActionExecutor:
    """
    操作执行器

    根据 AI 分析返回的 JSON 操作指令，调用 ADB 执行对应的手机操作。
    支持 tap/swipe/input/wait/done/back/home 等所有动作类型。
    """

    def __init__(self, adb: ADBController) -> None:
        """
        初始化操作执行器

        Args:
            adb: ADB 控制器实例
        """
        self.adb = adb

    def execute(self, action_data: Dict[str, Any]) -> bool:
        """
        根据 AI 返回的 JSON 执行对应操作

        Args:
            action_data: AI 返回的操作指令字典，包含 action 等字段

        Returns:
            True 表示执行成功
        """
        action = action_data.get("action", "wait").lower()
        reason = action_data.get("reason", "")

        logger.info(f"执行操作: {action} | 原因: {reason}")

        try:
            if action == "tap":
                return self._do_tap(action_data)
            elif action == "swipe":
                return self._do_swipe(action_data)
            elif action == "input":
                return self._do_input(action_data)
            elif action == "wait":
                return self._do_wait(action_data)
            elif action == "back":
                return self._do_back()
            elif action == "home":
                return self._do_home()
            elif action == "done":
                logger.info("任务标记为完成")
                return True
            else:
                logger.warning(f"未知动作类型: {action}，执行等待")
                time.sleep(ACTION_WAIT_TIMES.get("wait", 2.0))
                return True
        except Exception as e:
            logger.error(f"执行操作 {action} 时发生异常: {e}")
            return False

    def _do_tap(self, action_data: Dict[str, Any]) -> bool:
        """
        执行点击操作

        Args:
            action_data: 包含 x, y 坐标的操作字典

        Returns:
            是否成功
        """
        x = action_data.get("x")
        y = action_data.get("y")

        if x is None or y is None:
            logger.error("tap 操作缺少坐标 x 或 y")
            return False

        logger.debug(f"点击坐标: ({x}, {y})")
        result = self.adb.tap(int(x), int(y))
        time.sleep(ACTION_WAIT_TIMES["tap"])
        return result

    def _do_swipe(self, action_data: Dict[str, Any]) -> bool:
        """
        执行滑动操作

        Args:
            action_data: 包含起点终点坐标和持续时间的操作字典

        Returns:
            是否成功
        """
        x1 = action_data.get("x")
        y1 = action_data.get("y")
        x2 = action_data.get("x2")
        y2 = action_data.get("y2")
        duration = action_data.get("duration", 500)

        if any(v is None for v in (x1, y1, x2, y2)):
            logger.error("swipe 操作缺少坐标字段")
            return False

        logger.debug(f"滑动: ({x1}, {y1}) -> ({x2}, {y2}), 持续 {duration}ms")
        result = self.adb.swipe(int(x1), int(y1), int(x2), int(y2), int(duration))
        time.sleep(ACTION_WAIT_TIMES["swipe"])
        return result

    def _do_input(self, action_data: Dict[str, Any]) -> bool:
        """
        执行文本输入操作

        Args:
            action_data: 包含 text 字段的操作字典

        Returns:
            是否成功
        """
        text = action_data.get("text", "")
        if not text:
            logger.warning("input 操作没有提供文本内容")
            return True

        logger.debug(f"输入文本: {text}")
        result = self.adb.input_text(str(text))
        time.sleep(ACTION_WAIT_TIMES["input"])
        return result

    def _do_wait(self, action_data: Dict[str, Any]) -> bool:
        """
        执行等待操作

        Args:
            action_data: 可包含 duration 字段（秒）

        Returns:
            始终返回 True
        """
        duration = action_data.get("duration", ACTION_WAIT_TIMES["wait"])
        logger.debug(f"等待 {duration} 秒")
        time.sleep(float(duration))
        return True

    def _do_back(self) -> bool:
        """
        执行返回键操作

        Returns:
            是否成功
        """
        logger.debug("按下返回键")
        result = self.adb.back()
        time.sleep(ACTION_WAIT_TIMES["back"])
        return result

    def _do_home(self) -> bool:
        """
        执行 Home 键操作

        Returns:
            是否成功
        """
        logger.debug("按下 Home 键")
        result = self.adb.home()
        time.sleep(ACTION_WAIT_TIMES["home"])
        return result
