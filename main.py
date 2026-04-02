#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AgentX - AI 驱动的游戏自动化框架
支持通过自然语言指令控制雷电模拟器中的奇迹暖暖

使用方式:
    交互模式: python main.py
    单条指令: python main.py "帮我登录游戏"
    指令文件: python main.py --file tasks.txt
"""

import sys
import argparse
import yaml
from pathlib import Path

from agentx.utils.logger import setup_logger
from agentx.agent.ai_agent import AIAgent


def load_config(config_path: str = "config.yaml") -> dict:
    """
    加载配置文件

    Args:
        config_path: 配置文件路径

    Returns:
        配置字典
    """
    path = Path(config_path)
    if not path.exists():
        print(f"[错误] 配置文件不存在: {config_path}")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config


def run_instruction(agent: AIAgent, instruction: str) -> bool:
    """
    执行单条自然语言指令

    Args:
        agent: AI Agent 实例
        instruction: 自然语言指令

    Returns:
        是否执行成功
    """
    if not instruction.strip():
        return True

    print(f"\n✅ 正在执行：{instruction}")
    try:
        success = agent.run(instruction)
        if success:
            print(f"✅ 指令执行完成：{instruction}")
        else:
            print(f"❌ 指令执行失败：{instruction}")
        return success
    except KeyboardInterrupt:
        print("\n⚠️  用户中断操作")
        return False
    except Exception as e:
        print(f"❌ 执行出错：{e}")
        return False


def interactive_mode(agent: AIAgent) -> None:
    """
    交互模式：循环接收用户自然语言指令

    Args:
        agent: AI Agent 实例
    """
    print("\n" + "=" * 60)
    print("🤖 AgentX 已启动 - 雷电模拟器 + 奇迹暖暖")
    print("输入指令（输入 'exit' 或 'quit' 退出，输入 'help' 查看帮助）：")
    print("=" * 60)

    while True:
        try:
            instruction = input("\n> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n再见！")
            break

        if instruction.lower() in ("exit", "quit", "退出"):
            print("再见！")
            break

        if instruction.lower() in ("help", "帮助"):
            print("\n📋 可用指令示例：")
            print("  打开游戏并登录")
            print("  领取每日签到奖励")
            print("  收取所有邮件")
            print("  挑战今日时装评分")
            print("  完成每日任务")
            print("  exit / quit - 退出程序")
            continue

        if not instruction:
            continue

        run_instruction(agent, instruction)


def file_mode(agent: AIAgent, file_path: str) -> None:
    """
    指令文件模式：从文件读取并依次执行指令

    Args:
        agent: AI Agent 实例
        file_path: 指令文件路径
    """
    path = Path(file_path)
    if not path.exists():
        print(f"[错误] 指令文件不存在: {file_path}")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        instructions = [line.strip() for line in f.readlines()]

    # 过滤空行和注释行
    instructions = [
        line for line in instructions if line and not line.startswith("#")
    ]

    if not instructions:
        print("[警告] 指令文件为空，没有可执行的指令")
        return

    print(f"\n📋 从文件加载了 {len(instructions)} 条指令：{file_path}")
    print("=" * 60)

    success_count = 0
    fail_count = 0

    for i, instruction in enumerate(instructions, 1):
        print(f"\n[{i}/{len(instructions)}] {instruction}")
        success = run_instruction(agent, instruction)
        if success:
            success_count += 1
        else:
            fail_count += 1

    print("\n" + "=" * 60)
    print(f"📊 执行完成：成功 {success_count} 条，失败 {fail_count} 条")


def main() -> None:
    """主入口函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description="AgentX - AI 驱动的游戏自动化框架",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py                          # 交互模式
  python main.py "打开游戏并登录"          # 单条指令
  python main.py --file tasks.txt         # 指令文件模式
  python main.py --config my_config.yaml  # 指定配置文件
        """,
    )
    parser.add_argument(
        "instruction",
        nargs="?",
        help="自然语言指令（可选，不提供则进入交互模式）",
    )
    parser.add_argument(
        "--file",
        "-f",
        type=str,
        help="从文件读取指令列表（每行一条指令）",
    )
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default="config.yaml",
        help="配置文件路径（默认: config.yaml）",
    )

    args = parser.parse_args()

    # 加载配置
    config = load_config(args.config)

    # 初始化日志
    log_config = config.get("logging", {})
    logger = setup_logger(
        level=log_config.get("level", "INFO"),
        log_file=log_config.get("file", "logs/agentx.log"),
    )
    logger.info("AgentX 启动中...")

    # 检查 API Key
    ai_config = config.get("ai", {})
    api_key = ai_config.get("api_key", "")
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        print(
            "[错误] 请在 config.yaml 中填写有效的 API Key（ai.api_key）"
        )
        sys.exit(1)

    # 初始化 AI Agent
    try:
        agent = AIAgent(config=config)
    except Exception as e:
        print(f"[错误] 初始化 AI Agent 失败：{e}")
        logger.exception("初始化 AI Agent 失败")
        sys.exit(1)

    # 根据参数选择运行模式
    if args.file:
        # 指令文件模式
        file_mode(agent, args.file)
    elif args.instruction:
        # 单条指令模式
        success = run_instruction(agent, args.instruction)
        sys.exit(0 if success else 1)
    else:
        # 交互模式
        interactive_mode(agent)


if __name__ == "__main__":
    main()
