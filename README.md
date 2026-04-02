# AgentX 🤖

> AI 驱动的桌面游戏自动化框架 —— 通过自然语言指令控制雷电模拟器中的奇迹暖暖

---

## 📖 项目介绍

AgentX 是一个基于大语言模型（GPT-4o / Claude）和计算机视觉（GPT-4V / OpenCV）构建的游戏自动化框架。它允许用户通过简单的自然语言指令，自动控制运行在**雷电模拟器**中的**奇迹暖暖**游戏，无需编写固定步骤的脚本，AI 会动态识别当前界面并决定下一步操作。

---

## ✨ 功能特性

- 🗣️ **自然语言驱动**：直接输入中文指令，如"登录游戏并领取每日签到"
- 👁️ **视觉理解**：使用 GPT-4V 截图分析当前游戏界面
- 🧠 **动态决策**：AI 根据当前状态自动决定点击/滑动/输入等操作
- 📱 **ADB 控制**：通过 ADB 精准控制雷电模拟器
- 🔁 **自动恢复**：遇到错误自动尝试恢复
- 📊 **HTML 报告**：自动生成操作记录和测试报告
- 📝 **详细日志**：使用 loguru 记录所有操作步骤
- 🔧 **OpenCV 模板匹配**：可选的本地图像识别，降低 API 调用成本

---

## 🖥️ 环境要求

- Python 3.9+
- Windows 10/11（推荐，因为雷电模拟器主要运行在 Windows）
- 雷电模拟器（LDPlayer 9）已安装并运行
- OpenAI API Key（支持 GPT-4o / GPT-4V）或 Anthropic API Key
- ADB 工具（可独立安装或使用模拟器自带）

---

## 📦 安装步骤

### 1. 克隆仓库

```bash
git clone https://github.com/lotto111/AgentX.git
cd AgentX
```

### 2. 创建虚拟环境

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置 config.yaml

编辑 `config.yaml`，填写你的 API Key 和模拟器路径：

```yaml
ai:
  api_key: "sk-your-openai-api-key"
```

### 5. 启动雷电模拟器

确保雷电模拟器已启动，并在模拟器中安装了奇迹暖暖（包名：`com.netease.nikki`）。

---

## ⚙️ 配置说明（config.yaml）

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `emulator.adb_host` | 模拟器 ADB 地址 | `127.0.0.1` |
| `emulator.adb_port` | 雷电模拟器 ADB 端口 | `5555` |
| `emulator.emulator_exe` | 雷电模拟器可执行文件路径 | `C:/LDPlayer/LDPlayer9/dnplayer.exe` |
| `game.package` | 奇迹暖暖包名 | `com.netease.nikki` |
| `ai.provider` | AI 提供商 | `openai` |
| `ai.model` | 使用的模型 | `gpt-4o` |
| `ai.api_key` | API 密钥 | 需要填写 |
| `ai.max_steps` | 单次指令最大操作步数 | `30` |
| `ai.confidence_threshold` | 操作置信度阈值 | `0.8` |
| `logging.level` | 日志级别 | `INFO` |
| `report.enabled` | 是否生成 HTML 报告 | `true` |

---

## 🚀 使用示例

### 交互模式（推荐）

```bash
python main.py
```

```
🤖 AgentX 已启动 - 雷电模拟器 + 奇迹暖暖
输入指令（输入 'exit' 退出）：
> 打开游戏并登录
✅ 正在执行：打开游戏并登录
...
> 领取每日签到奖励
> 挑战今日时装评分
> exit
再见！
```

### 单条指令模式

```bash
python main.py "打开奇迹暖暖，完成每日任务"
```

### 指令文件模式

```bash
python main.py --file tasks.txt
```

`tasks.txt` 示例：
```
打开游戏并登录
领取每日签到奖励
收取所有邮件
挑战今日时装评分
```

---

## 📁 项目结构

```
AgentX/
├── README.md                        # 项目说明文档
├── requirements.txt                 # 依赖列表
├── config.yaml                      # 配置文件
├── main.py                          # 主入口
├── agentx/
│   ├── __init__.py
│   ├── emulator/
│   │   ├── __init__.py
│   │   ├── ldplayer.py              # 雷电模拟器 ADB 控制
│   │   └── adb_controller.py       # 通用 ADB 操作封装
│   ├── vision/
│   │   ├── __init__.py
│   │   ├── screen_analyzer.py      # 截图 + GPT-4V 分析
│   │   └── template_matcher.py     # OpenCV 模板匹配
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── ai_agent.py             # 核心 AI Agent
│   │   └── action_executor.py      # 操作执行器
│   ├── games/
│   │   ├── __init__.py
│   │   └── miracle_nikki.py        # 奇迹暖暖专用逻辑
│   └── utils/
│       ├── __init__.py
│       ├── logger.py               # 日志工具
│       └── report.py               # 测试报告生成
├── templates/                       # 游戏截图模板目录
│   └── README.md
├── logs/                            # 日志目录
└── reports/                         # 测试报告目录
```

---

## ❓ 常见问题

**Q: ADB 无法连接模拟器？**
A: 确认雷电模拟器已启动，并检查 `config.yaml` 中的 `adb_port` 是否为 `5555`（雷电9默认端口）。在命令行运行 `adb connect 127.0.0.1:5555` 手动测试连接。

**Q: AI 分析返回错误的操作？**
A: 增加 `ai.confidence_threshold` 阈值，或在 `templates/` 目录中添加游戏界面模板图片辅助识别。

**Q: 截图为黑屏？**
A: 雷电模拟器需要在前台运行，或者在模拟器设置中开启"允许后台截图"选项。

**Q: 支持其他模拟器吗？**
A: 理论上支持所有兼容 ADB 的 Android 模拟器，修改 `config.yaml` 中的 `adb_port` 即可（夜神：62001，MuMu：7555）。

**Q: 支持其他游戏吗？**
A: 可以参考 `agentx/games/miracle_nikki.py` 创建新的游戏模块，并修改 `config.yaml` 中的 `game.package`。

---

## 📄 License

MIT License
