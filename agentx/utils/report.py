# -*- coding: utf-8 -*-
"""
测试报告生成模块
记录操作步骤、截图附件，并生成 HTML 格式测试报告
"""

import os
import shutil
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from agentx.utils.logger import get_logger

logger = get_logger(__name__)

# HTML 报告模板
_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AgentX 测试报告 - {task_name}</title>
<style>
  body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
  .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); padding: 30px; }}
  h1 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
  .summary {{ display: flex; gap: 20px; margin: 20px 0; flex-wrap: wrap; }}
  .stat-card {{ background: #f9f9f9; border-radius: 6px; padding: 15px 25px; border-left: 4px solid #4CAF50; }}
  .stat-card.fail {{ border-color: #f44336; }}
  .stat-card h3 {{ margin: 0 0 5px 0; color: #666; font-size: 14px; }}
  .stat-card .value {{ font-size: 28px; font-weight: bold; color: #333; }}
  .steps {{ margin-top: 30px; }}
  .step {{ background: #fafafa; border: 1px solid #e0e0e0; border-radius: 6px; margin-bottom: 15px; padding: 15px; }}
  .step-header {{ display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }}
  .step-num {{ background: #4CAF50; color: white; border-radius: 50%; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 13px; flex-shrink: 0; }}
  .action-badge {{ background: #2196F3; color: white; padding: 2px 10px; border-radius: 12px; font-size: 13px; }}
  .action-badge.done {{ background: #4CAF50; }}
  .action-badge.back, .action-badge.wait {{ background: #9E9E9E; }}
  .confidence {{ margin-left: auto; color: #888; font-size: 13px; }}
  .reason {{ color: #555; font-size: 14px; margin: 5px 0; }}
  .screenshot {{ margin-top: 10px; }}
  .screenshot img {{ max-width: 300px; border: 1px solid #ddd; border-radius: 4px; cursor: pointer; transition: transform 0.2s; }}
  .screenshot img:hover {{ transform: scale(1.05); }}
  .result-banner {{ padding: 12px 20px; border-radius: 6px; font-size: 16px; font-weight: bold; margin-bottom: 20px; }}
  .result-banner.success {{ background: #E8F5E9; color: #2E7D32; border: 1px solid #A5D6A7; }}
  .result-banner.fail {{ background: #FFEBEE; color: #C62828; border: 1px solid #EF9A9A; }}
</style>
</head>
<body>
<div class="container">
  <h1>🤖 AgentX 测试报告</h1>
  <div class="result-banner {result_class}">
    {result_icon} {result_text}
  </div>
  <div class="summary">
    <div class="stat-card">
      <h3>任务指令</h3>
      <div class="value" style="font-size:18px;">{task_name}</div>
    </div>
    <div class="stat-card">
      <h3>执行步骤</h3>
      <div class="value">{total_steps}</div>
    </div>
    <div class="stat-card">
      <h3>开始时间</h3>
      <div class="value" style="font-size:16px;">{start_time}</div>
    </div>
    <div class="stat-card">
      <h3>耗时</h3>
      <div class="value" style="font-size:16px;">{duration}</div>
    </div>
  </div>
  <div class="steps">
    <h2>执行步骤详情</h2>
    {steps_html}
  </div>
</div>
</body>
</html>
"""

_STEP_TEMPLATE = """
<div class="step">
  <div class="step-header">
    <div class="step-num">{step_num}</div>
    <span class="action-badge {action_class}">{action}</span>
    <span class="confidence">置信度: {confidence:.0%}</span>
  </div>
  <div class="reason">📝 {reason}</div>
  {coord_html}
  {screenshot_html}
</div>
"""


class ReportGenerator:
    """
    HTML 测试报告生成器

    记录每次自动化任务的操作步骤、截图，并生成可视化 HTML 报告。
    """

    def __init__(self, output_dir: str = "reports/") -> None:
        """
        初始化报告生成器

        Args:
            output_dir: 报告输出目录
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        self._task_name: str = ""
        self._start_time: Optional[float] = None
        self._steps: List[Dict[str, Any]] = []
        self._success: bool = False

    def start_task(self, task_name: str) -> None:
        """
        开始记录一个新任务

        Args:
            task_name: 任务描述（自然语言指令）
        """
        self._task_name = task_name
        self._start_time = time.time()
        self._steps = []
        self._success = False
        logger.debug(f"开始记录任务报告：{task_name}")

    def add_step(
        self,
        step: int,
        action: Dict[str, Any],
        screenshot_path: Optional[str] = None,
    ) -> None:
        """
        添加一个操作步骤记录

        Args:
            step: 步骤编号
            action: AI 返回的操作指令字典
            screenshot_path: 该步骤对应的截图路径（可选）
        """
        step_data = {
            "step": step,
            "action": action,
            "screenshot_path": screenshot_path,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        }
        self._steps.append(step_data)

    def finish_task(self, success: bool) -> Optional[str]:
        """
        完成任务记录并生成 HTML 报告

        Args:
            success: 任务是否成功完成

        Returns:
            生成的报告文件路径，失败时返回 None
        """
        self._success = success
        try:
            return self._generate_html()
        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            return None

    def _generate_html(self) -> str:
        """
        生成 HTML 报告文件

        Returns:
            报告文件路径
        """
        # 报告文件命名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        task_slug = self._task_name[:20].replace(" ", "_").replace("/", "-")
        report_filename = f"report_{timestamp}_{task_slug}.html"
        report_path = os.path.join(self.output_dir, report_filename)

        # 截图目录（放在报告同目录）
        screenshots_dir = os.path.join(self.output_dir, f"screenshots_{timestamp}")
        os.makedirs(screenshots_dir, exist_ok=True)

        # 生成步骤 HTML
        steps_html_parts = []
        for s in self._steps:
            action_data = s["action"]
            action_name = action_data.get("action", "unknown")
            confidence = action_data.get("confidence", 0.0)
            reason = action_data.get("reason", "")

            # 坐标显示
            coord_html = ""
            if "x" in action_data and "y" in action_data:
                coord_html = f'<div style="color:#888;font-size:13px;">坐标: ({action_data["x"]}, {action_data["y"]})</div>'
                if "x2" in action_data:
                    coord_html += f'<div style="color:#888;font-size:13px;">终点: ({action_data.get("x2")}, {action_data.get("y2")})</div>'

            # 截图处理
            screenshot_html = ""
            orig_path = s.get("screenshot_path")
            if orig_path and os.path.exists(orig_path):
                dest_name = f"step_{s['step']:03d}.png"
                dest_path = os.path.join(screenshots_dir, dest_name)
                try:
                    shutil.copy2(orig_path, dest_path)
                    rel_path = os.path.join(
                        f"screenshots_{timestamp}", dest_name
                    ).replace("\\", "/")
                    screenshot_html = (
                        f'<div class="screenshot">'
                        f'<img src="{rel_path}" alt="步骤{s["step"]}截图" '
                        f'title="点击查看截图" onclick="window.open(this.src)">'
                        f'</div>'
                    )
                except Exception:
                    pass

            step_html = _STEP_TEMPLATE.format(
                step_num=s["step"],
                action=action_name.upper(),
                action_class=action_name.lower(),
                confidence=float(confidence),
                reason=reason or "-",
                coord_html=coord_html,
                screenshot_html=screenshot_html,
            )
            steps_html_parts.append(step_html)

        # 计算耗时
        elapsed = ""
        if self._start_time:
            seconds = int(time.time() - self._start_time)
            elapsed = f"{seconds // 60}分{seconds % 60}秒"

        # 渲染 HTML
        html = _HTML_TEMPLATE.format(
            task_name=self._task_name,
            result_class="success" if self._success else "fail",
            result_icon="✅" if self._success else "❌",
            result_text="任务执行成功" if self._success else "任务执行失败",
            total_steps=len(self._steps),
            start_time=datetime.fromtimestamp(self._start_time or time.time()).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            duration=elapsed,
            steps_html="\n".join(steps_html_parts) if steps_html_parts else "<p>无步骤记录</p>",
        )

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html)

        logger.info(f"测试报告已生成: {report_path}")
        return report_path
