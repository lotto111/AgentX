# -*- coding: utf-8 -*-
"""
截图分析模块
使用 GPT-4V 分析游戏截图，返回下一步操作指令
"""

import base64
import json
import re
import time
from typing import Any, Dict, List, Optional

from agentx.utils.logger import get_logger

logger = get_logger(__name__)

# AI 系统提示词，专门针对奇迹暖暖游戏界面优化（模块私有）
_SYSTEM_PROMPT = """你是一个专业的奇迹暖暖（Miracle Nikki）游戏自动化助手。
你的任务是分析游戏截图，理解当前界面状态，并根据用户的指令决定下一步操作。

## 输出格式（严格遵守）
请只返回一个 JSON 对象，格式如下：
{
    "action": "动作类型",
    "x": 横坐标（整数，仅 tap/swipe 需要）,
    "y": 纵坐标（整数，仅 tap/swipe 需要）,
    "x2": 滑动终点横坐标（整数，仅 swipe 需要）,
    "y2": 滑动终点纵坐标（整数，仅 swipe 需要）,
    "text": "输入文本（仅 input 需要）",
    "reason": "执行这个操作的原因",
    "confidence": 置信度（0.0 到 1.0 的浮点数）
}

## 支持的动作类型
- tap: 点击指定坐标
- swipe: 从 (x, y) 滑动到 (x2, y2)
- input: 在当前焦点输入文本
- wait: 等待界面加载（无需坐标）
- back: 按返回键（无需坐标）
- home: 按 Home 键（无需坐标）
- done: 任务已完成（无需坐标）

## 奇迹暖暖游戏界面知识
- 游戏默认分辨率：1280x720 或 1920x1080
- 主界面有：商店、邮件、任务、时装搭配、竞技等入口
- 加载界面通常有进度条或旋转图标
- 对话框通常有"确定"、"取消"、"关闭"按钮
- 如果看到弹窗，通常需要先关闭弹窗再继续

## 注意事项
- 坐标必须在屏幕范围内（不超过截图尺寸）
- 置信度低于 0.6 时应选择 wait 动作
- 如果当前状态已满足任务要求，返回 done
- 只返回 JSON，不要有任何其他文字
"""


class ScreenAnalyzer:
    """
    截图分析器

    使用 GPT-4V（或 Claude 的视觉能力）分析游戏截图，
    根据当前界面和用户指令决定下一步操作。
    """

    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-4o",
        api_key: str = "",
        confidence_threshold: float = 0.8,
    ) -> None:
        """
        初始化截图分析器

        Args:
            provider: AI 提供商（openai 或 anthropic）
            model: 使用的模型名称
            api_key: API 密钥
            confidence_threshold: 操作置信度阈值
        """
        self.provider = provider.lower()
        self.model = model
        self.api_key = api_key
        self.confidence_threshold = confidence_threshold
        self._client = None
        self._init_client()

    def _init_client(self) -> None:
        """初始化 AI 客户端"""
        try:
            if self.provider == "openai":
                import openai
                self._client = openai.OpenAI(api_key=self.api_key)
                logger.info(f"OpenAI 客户端初始化成功，模型: {self.model}")
            elif self.provider == "anthropic":
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.api_key)
                logger.info(f"Anthropic 客户端初始化成功，模型: {self.model}")
            else:
                logger.error(f"不支持的 AI 提供商: {self.provider}")
        except ImportError as e:
            logger.error(f"导入 AI 库失败: {e}，请运行 pip install -r requirements.txt")
        except Exception as e:
            logger.error(f"初始化 AI 客户端失败: {e}")

    def analyze(
        self,
        screenshot_path: str,
        instruction: str,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        分析截图并返回操作指令

        Args:
            screenshot_path: 截图文件路径
            instruction: 用户自然语言指令
            history: 历史操作记录列表

        Returns:
            操作指令字典，格式：
            {
                "action": "tap/swipe/input/wait/done/back",
                "x": int,
                "y": int,
                "x2": int（可选）,
                "y2": int（可选）,
                "text": str（可选）,
                "reason": str,
                "confidence": float
            }
        """
        if self._client is None:
            logger.error("AI 客户端未初始化")
            return self._fallback_action("AI 客户端未初始化")

        try:
            # 将截图编码为 base64
            image_b64 = self._encode_image(screenshot_path)
            if not image_b64:
                return self._fallback_action("截图编码失败")

            # 构建历史操作摘要
            history_text = ""
            if history:
                recent = history[-5:]  # 只取最近5步
                history_text = "\n历史操作（最近5步）：\n"
                for i, h in enumerate(recent, 1):
                    history_text += (
                        f"  第{i}步: {h.get('action')} - {h.get('reason', '')}\n"
                    )

            user_message = (
                f"当前任务：{instruction}\n"
                f"{history_text}\n"
                "请分析截图，决定下一步操作，只返回 JSON。"
            )

            # 调用 AI 分析
            if self.provider == "openai":
                response_text = self._call_openai(image_b64, user_message)
            elif self.provider == "anthropic":
                response_text = self._call_anthropic(image_b64, user_message)
            else:
                return self._fallback_action("不支持的 AI 提供商")

            # 解析 JSON 响应
            action_data = self._parse_response(response_text)
            logger.info(
                f"AI 分析结果: {action_data.get('action')} - {action_data.get('reason', '')}"
            )
            return action_data

        except Exception as e:
            logger.error(f"截图分析失败: {e}")
            return self._fallback_action(f"分析异常: {e}")

    def _call_openai(self, image_b64: str, user_message: str) -> str:
        """
        调用 OpenAI GPT-4V 分析截图

        Args:
            image_b64: base64 编码的图片
            user_message: 用户消息

        Returns:
            AI 响应文本
        """
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_b64}",
                                "detail": "high",
                            },
                        },
                        {"type": "text", "text": user_message},
                    ],
                },
            ],
            max_tokens=500,
            temperature=0.1,
        )
        return response.choices[0].message.content

    def _call_anthropic(self, image_b64: str, user_message: str) -> str:
        """
        调用 Anthropic Claude 分析截图

        Args:
            image_b64: base64 编码的图片
            user_message: 用户消息

        Returns:
            AI 响应文本
        """
        response = self._client.messages.create(
            model=self.model,
            max_tokens=500,
            system=_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_b64,
                            },
                        },
                        {"type": "text", "text": user_message},
                    ],
                }
            ],
        )
        return response.content[0].text

    def _encode_image(self, image_path: str) -> str:
        """
        将图片文件编码为 base64 字符串

        Args:
            image_path: 图片文件路径

        Returns:
            base64 编码字符串，失败时返回空字符串
        """
        try:
            with open(image_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except FileNotFoundError:
            logger.error(f"截图文件不存在: {image_path}")
            return ""
        except Exception as e:
            logger.error(f"图片编码失败: {e}")
            return ""

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        解析 AI 返回的 JSON 响应

        Args:
            response_text: AI 响应文本

        Returns:
            解析后的操作指令字典
        """
        try:
            # 尝试直接解析
            cleaned = response_text.strip()

            # 提取 JSON 块（处理可能的 markdown 代码块）
            json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
            if json_match:
                cleaned = json_match.group(1)
            else:
                # 查找第一个 { 到最后一个 }
                start = cleaned.find("{")
                end = cleaned.rfind("}") + 1
                if start != -1 and end > start:
                    cleaned = cleaned[start:end]

            data = json.loads(cleaned)

            # 验证必要字段
            if "action" not in data:
                logger.warning("AI 响应缺少 action 字段，使用 wait")
                data["action"] = "wait"

            # 确保数值字段类型正确
            for field in ("x", "y", "x2", "y2"):
                if field in data and data[field] is not None:
                    data[field] = int(data[field])

            if "confidence" in data:
                data["confidence"] = float(data["confidence"])
            else:
                data["confidence"] = 0.8

            if "reason" not in data:
                data["reason"] = ""

            return data

        except json.JSONDecodeError as e:
            logger.error(f"解析 AI 响应 JSON 失败: {e}\n原始响应: {response_text[:200]}")
            return self._fallback_action("JSON 解析失败")
        except Exception as e:
            logger.error(f"解析响应异常: {e}")
            return self._fallback_action(f"响应解析异常: {e}")

    def _fallback_action(self, reason: str = "") -> Dict[str, Any]:
        """
        返回降级操作（等待）

        Args:
            reason: 降级原因

        Returns:
            wait 操作字典
        """
        return {
            "action": "wait",
            "reason": reason or "分析失败，等待重试",
            "confidence": 0.0,
        }
