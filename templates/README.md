# 游戏截图模板使用说明

本目录用于存放奇迹暖暖（Miracle Nikki）游戏界面元素的模板图片，
供 `TemplateMatcher` 模块进行 OpenCV 模板匹配使用。

## 如何截取模板图片

### 方法一：使用 ADB 截图后裁剪

```bash
# 1. 连接模拟器
adb connect 127.0.0.1:5555

# 2. 截取当前屏幕
adb -s 127.0.0.1:5555 shell screencap -p /sdcard/screen.png
adb -s 127.0.0.1:5555 pull /sdcard/screen.png ./screen.png

# 3. 使用图片编辑器（如 Windows 画图、GIMP）裁剪需要识别的元素
```

### 方法二：使用 Python 截图并裁剪

```python
from PIL import Image

# 打开截图
img = Image.open("screen.png")

# 裁剪区域 (left, upper, right, lower)
template = img.crop((100, 200, 300, 280))

# 保存模板
template.save("templates/login_button.png")
```

## 推荐模板列表

请截取以下界面元素并以对应名称保存：

| 文件名 | 描述 |
|--------|------|
| `login_button.png` | 登录按钮 |
| `username_field.png` | 用户名输入框 |
| `password_field.png` | 密码输入框 |
| `main_screen.png` | 游戏主界面标志 |
| `daily_task_icon.png` | 每日任务入口图标 |
| `mailbox_icon.png` | 邮件图标 |
| `sign_in_button.png` | 签到按钮 |
| `confirm_button.png` | 确认/确定按钮 |
| `close_button.png` | 关闭弹窗按钮 |
| `loading_indicator.png` | 加载中图标（用于等待判断）|

## 注意事项

1. 模板图片应尽量小（只包含目标元素，减少背景干扰）
2. 确保模板图片来自同一分辨率的截图
3. 默认匹配阈值为 0.8，如遇误匹配可适当调高
4. 模板文件建议使用 PNG 格式以获得最佳匹配质量

## 使用示例

```python
from agentx.vision.template_matcher import TemplateMatcher

matcher = TemplateMatcher(threshold=0.8)

# 查找登录按钮并获取坐标
pos = matcher.find("templates/login_button.png", "screen.png")
if pos:
    x, y = pos
    print(f"登录按钮位于: ({x}, {y})")
```
