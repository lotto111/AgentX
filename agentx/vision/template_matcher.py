# -*- coding: utf-8 -*-
"""
OpenCV 模板匹配模块
在截图中查找预设的游戏界面元素模板
"""

import time
from typing import List, Optional, Tuple

import cv2
import numpy as np

from agentx.utils.logger import get_logger

logger = get_logger(__name__)


class TemplateMatcher:
    """
    OpenCV 模板匹配器

    通过图像模板在游戏截图中定位 UI 元素，
    作为 AI 视觉分析的补充或替代方案。
    """

    def __init__(self, threshold: float = 0.8) -> None:
        """
        初始化模板匹配器

        Args:
            threshold: 默认匹配置信度阈值（0.0 ~ 1.0）
        """
        self.threshold = threshold

    def find(
        self,
        template_path: str,
        screenshot_path: str,
        threshold: Optional[float] = None,
    ) -> Optional[Tuple[int, int]]:
        """
        在截图中查找模板，返回最佳匹配位置的中心坐标

        Args:
            template_path: 模板图片路径
            screenshot_path: 截图路径
            threshold: 匹配阈值（不传则使用默认阈值）

        Returns:
            匹配位置的中心 (x, y) 坐标，未找到时返回 None
        """
        try:
            thr = threshold if threshold is not None else self.threshold

            template = cv2.imread(template_path)
            screenshot = cv2.imread(screenshot_path)

            if template is None:
                logger.error(f"无法读取模板图片: {template_path}")
                return None
            if screenshot is None:
                logger.error(f"无法读取截图: {screenshot_path}")
                return None

            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)

            if max_val >= thr:
                h, w = template.shape[:2]
                cx = max_loc[0] + w // 2
                cy = max_loc[1] + h // 2
                logger.debug(
                    f"模板匹配成功: {template_path}, 位置=({cx}, {cy}), 置信度={max_val:.3f}"
                )
                return cx, cy
            else:
                logger.debug(
                    f"模板未找到: {template_path}, 最高置信度={max_val:.3f} < {thr}"
                )
                return None
        except Exception as e:
            logger.error(f"模板匹配失败: {e}")
            return None

    def find_all(
        self,
        template_path: str,
        screenshot_path: str,
        threshold: Optional[float] = None,
    ) -> List[Tuple[int, int]]:
        """
        在截图中查找所有匹配位置的中心坐标

        Args:
            template_path: 模板图片路径
            screenshot_path: 截图路径
            threshold: 匹配阈值

        Returns:
            所有匹配位置中心坐标列表
        """
        try:
            thr = threshold if threshold is not None else self.threshold

            template = cv2.imread(template_path)
            screenshot = cv2.imread(screenshot_path)

            if template is None or screenshot is None:
                return []

            h, w = template.shape[:2]
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= thr)

            # 收集匹配坐标并去重（使用 NMS 思路：排除距离太近的点）
            points = list(zip(locations[1], locations[0]))
            centers = []
            used = set()

            for px, py in sorted(points, key=lambda p: -result[p[1], p[0]]):
                if any(
                    abs(px - ux) < w // 2 and abs(py - uy) < h // 2
                    for ux, uy in used
                ):
                    continue
                cx = px + w // 2
                cy = py + h // 2
                centers.append((cx, cy))
                used.add((px, py))

            logger.debug(f"模板 {template_path} 找到 {len(centers)} 个匹配")
            return centers
        except Exception as e:
            logger.error(f"查找所有模板失败: {e}")
            return []

    def wait_for(
        self,
        template_path: str,
        screenshot_fn,
        timeout: int = 10,
        interval: float = 1.0,
        threshold: Optional[float] = None,
    ) -> Optional[Tuple[int, int]]:
        """
        等待指定模板出现在屏幕上

        Args:
            template_path: 模板图片路径
            screenshot_fn: 截图函数，调用后返回截图保存路径
            timeout: 超时时间（秒）
            interval: 检测间隔（秒）
            threshold: 匹配阈值

        Returns:
            找到后返回元素中心 (x, y) 坐标，超时返回 None
        """
        logger.info(f"等待模板出现: {template_path}（最多 {timeout} 秒）")
        start = time.time()

        while time.time() - start < timeout:
            # 获取最新截图
            screenshot_path = screenshot_fn()
            if screenshot_path:
                pos = self.find(template_path, screenshot_path, threshold)
                if pos:
                    logger.info(f"模板已出现: {template_path}, 位置={pos}")
                    return pos
            time.sleep(interval)

        logger.warning(f"等待超时，模板未出现: {template_path}")
        return None

    def is_visible(
        self,
        template_path: str,
        screenshot_path: str,
        threshold: Optional[float] = None,
    ) -> bool:
        """
        检查模板是否在截图中可见

        Args:
            template_path: 模板图片路径
            screenshot_path: 截图路径
            threshold: 匹配阈值

        Returns:
            True 表示模板可见
        """
        return self.find(template_path, screenshot_path, threshold) is not None
