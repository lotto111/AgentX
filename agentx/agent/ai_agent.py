# -*- coding: utf-8 -*-
"""
核心 AI Agent 模块
负责协调截图分析、操作执行、错误恢复的完整自动化循环
"""

import time
import os
from typing import Any, Dict, List, Optional

from agentx.emulator.ldplayer import LDPlayerController
from agentx.emulator.adb_controller import ADBController
from agentx.vision.screen_analyzer import ScreenAnalyzer
from agentx.agent.action_executor import ActionExecutor
from agentx.utils.logger import get_logger
from agentx.utils.report import ReportGenerator

logger = get_logger(__name__)


class AIAgent:
    """
    核心 AI Agent

    实现"截图 → AI 分析 → 执行操作 → 验证 → 循环"的自动化主循环。
    支持 OpenAI 和 Anthropic 两种 AI 提供商，具备最大步骤限制和自动错误恢复机制。
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        初始化 AI Agent

        Args:
            config: 完整配置字典（来自 config.yaml）
        """
        self.config = config

        # 模拟器配置
        emu_cfg = config.get("emulator", {})
        self.emulator = LDPlayerController(
            adb_host=emu_cfg.get("adb_host", "127.0.0.1"),
            adb_port=emu_cfg.get("adb_port", 5555),
            adb_path=emu_cfg.get("adb_path", "adb"),
            emulator_exe=emu_cfg.get("emulator_exe", ""),
            wait_boot=emu_cfg.get("wait_boot", 30),
        )

        # AI 配置
        ai_cfg = config.get("ai", {})
        self.max_steps: int = ai_cfg.get("max_steps", 30)
        self.confidence_threshold: float = ai_cfg.get("confidence_threshold", 0.8)

        # 初始化视觉分析器
        self.analyzer = ScreenAnalyzer(
            provider=ai_cfg.get("provider", "openai"),
            model=ai_cfg.get("model", "gpt-4o"),
            api_key=ai_cfg.get("api_key", ""),
            confidence_threshold=self.confidence_threshold,
        )

        # 操作执行器（延迟初始化，等待 ADB 连接后再创建）
        self._executor: Optional[ActionExecutor] = None

        # 报告生成器
        report_cfg = config.get("report", {})
        self.report_enabled: bool = report_cfg.get("enabled", True)
        self.report = ReportGenerator(
            output_dir=report_cfg.get("output_dir", "reports/")
        ) if self.report_enabled else None

        # 截图临时文件路径
        self.screenshot_dir = "/tmp/agentx_screenshots"
        os.makedirs(self.screenshot_dir, exist_ok=True)

        # 连接 ADB
        self._connect_adb()

    def _connect_adb(self) -> bool:
        """
        连接 ADB 并初始化操作执行器

        Returns:
            是否连接成功
        """
        try:
            connected = self.emulator.connect()
            if connected:
                adb = self.emulator.get_adb_controller()
                if adb:
                    self._executor = ActionExecutor(adb=adb)
                    logger.info("ADB 连接成功，操作执行器已初始化")
                    return True
            logger.warning("ADB 连接失败，部分功能可能不可用")
            return False
        except Exception as e:
            logger.error(f"ADB 连接异常: {e}")
            return False

    def run(self, instruction: str) -> bool:
        """
        执行自然语言指令的主循环

        流程：截图 → AI 分析 → 执行操作 → 检查是否完成 → 循环

        Args:
            instruction: 用户自然语言指令

        Returns:
            True 表示任务成功完成，False 表示失败或超时
        """
        logger.info(f"开始执行指令：{instruction}")
        history: List[Dict[str, Any]] = []
        consecutive_errors = 0
        max_consecutive_errors = 3

        # 开始报告记录
        if self.report:
            self.report.start_task(instruction)

        for step in range(1, self.max_steps + 1):
            logger.info(f"--- 步骤 {step}/{self.max_steps} ---")

            # 1. 截图
            screenshot_path = self._take_screenshot(step)
            if not screenshot_path:
                logger.error("截图失败，尝试恢复...")
                consecutive_errors += 1
                if consecutive_errors >= max_consecutive_errors:
                    logger.error("连续截图失败，任务中止")
                    break
                time.sleep(2)
                continue

            # 2. AI 分析当前界面
            action_data = self.analyzer.analyze(
                screenshot_path=screenshot_path,
                instruction=instruction,
                history=history,
            )
            logger.info(
                f"AI 决策: {action_data.get('action')} "
                f"(置信度: {action_data.get('confidence', 0):.2f}) "
                f"- {action_data.get('reason', '')}"
            )

            # 记录到报告
            if self.report:
                self.report.add_step(
                    step=step,
                    action=action_data,
                    screenshot_path=screenshot_path,
                )

            # 3. 检查置信度
            confidence = action_data.get("confidence", 0.0)
            if confidence < self.confidence_threshold and action_data.get("action") not in ("wait", "done"):
                logger.warning(
                    f"置信度 {confidence:.2f} 低于阈值 {self.confidence_threshold}，等待重试"
                )
                time.sleep(2)
                continue

            # 4. 检查是否完成
            if action_data.get("action") == "done":
                logger.info(f"✅ 任务完成：{instruction}")
                if self.report:
                    self.report.finish_task(success=True)
                return True

            # 5. 执行操作
            if self._executor:
                success = self._executor.execute(action_data)
                if success:
                    consecutive_errors = 0
                else:
                    consecutive_errors += 1
                    logger.warning(f"操作执行失败（连续 {consecutive_errors} 次）")

                    # 错误恢复：尝试按返回键
                    if consecutive_errors >= 2:
                        logger.info("尝试错误恢复：按返回键")
                        self._executor.execute({"action": "back", "reason": "错误恢复"})
                        time.sleep(1)

                    if consecutive_errors >= max_consecutive_errors:
                        logger.error("连续操作失败，任务中止")
                        break
            else:
                logger.warning("操作执行器未初始化，跳过执行")
                time.sleep(1)

            # 记录历史
            history.append(action_data)

            # 步骤间等待
            time.sleep(1)

        # 超出最大步骤数
        logger.warning(f"达到最大步骤数 {self.max_steps}，任务未完成")
        if self.report:
            self.report.finish_task(success=False)
        return False

    def _take_screenshot(self, step: int) -> Optional[str]:
        """
        截取当前设备屏幕

        Args:
            step: 当前步骤号（用于命名文件）

        Returns:
            截图文件路径，失败时返回 None
        """
        try:
            adb = self.emulator.get_adb_controller()
            if not adb:
                # 尝试重新连接
                logger.info("ADB 未连接，尝试重连...")
                if self._connect_adb():
                    adb = self.emulator.get_adb_controller()
                if not adb:
                    return None

            screenshot_path = os.path.join(
                self.screenshot_dir, f"step_{step:03d}.png"
            )
            result = adb.screenshot(save_path=screenshot_path)
            return result
        except Exception as e:
            logger.error(f"截图异常: {e}")
            return None
