# -*- coding: utf-8 -*-
"""
日志工具模块
基于 loguru 实现，支持带颜色的控制台输出和文件持久化
"""

import sys
import os
from typing import Optional

from loguru import logger as _loguru_logger

# 全局标志：防止重复初始化
_initialized = False


def setup_logger(
    level: str = "INFO",
    log_file: Optional[str] = "logs/agentx.log",
) -> "loguru.Logger":
    """
    初始化并配置全局日志记录器

    Args:
        level: 日志级别（DEBUG / INFO / WARNING / ERROR）
        log_file: 日志文件路径（None 表示不写文件）

    Returns:
        配置好的 loguru logger 实例
    """
    global _initialized
    if _initialized:
        return _loguru_logger

    # 移除默认处理器
    _loguru_logger.remove()

    # 控制台输出（带颜色）
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    _loguru_logger.add(
        sys.stdout,
        level=level.upper(),
        format=console_format,
        colorize=True,
    )

    # 文件输出（无颜色）
    if log_file:
        # 确保日志目录存在
        log_dir = os.path.dirname(os.path.abspath(log_file))
        os.makedirs(log_dir, exist_ok=True)

        file_format = (
            "{time:YYYY-MM-DD HH:mm:ss} | "
            "{level: <8} | "
            "{name}:{line} | "
            "{message}"
        )
        _loguru_logger.add(
            log_file,
            level=level.upper(),
            format=file_format,
            rotation="10 MB",    # 超过 10MB 自动轮换
            retention="7 days",  # 保留最近 7 天的日志
            encoding="utf-8",
            colorize=False,
        )

    _initialized = True
    _loguru_logger.info(f"日志系统已初始化，级别={level}, 文件={log_file}")
    return _loguru_logger


def get_logger(name: str = "agentx") -> "loguru.Logger":
    """
    获取带模块名称绑定的日志记录器

    Args:
        name: 模块名称（通常传入 __name__）

    Returns:
        绑定了模块名的 loguru logger
    """
    # 确保已初始化
    if not _initialized:
        setup_logger()
    return _loguru_logger.bind(name=name)
