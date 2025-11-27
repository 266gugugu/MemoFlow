# MemoFlow - 沉浸式桌面备忘录

MemoFlow 是一款基于 PyQt6 开发的现代化桌面备忘录应用，专注于提供无干扰的记录体验。它结合了悬浮窗、Markdown 支持和标签管理，是您管理碎片化信息的得力助手。

## ✨ 核心特性

*   **🎈 智能悬浮窗**
    *   **自动吸附**：默认吸附屏幕顶部，不占用桌面空间。
    *   **自动收起**：鼠标离开后自动收起为一条细线，靠近即展开。
    *   **动态高度**：根据内容自动调整窗口大小，支持 Markdown 渲染。
    *   **多屏支持**：智能识别屏幕边缘，防丢回位。

*   **📝 沉浸式编辑**
    *   **内嵌编辑**：双击列表直接在主界面编辑，无弹窗打扰。
    *   **Markdown**：支持标题、列表、粗体等 Markdown 语法。
    *   **标签管理**：独立的标签选择器，轻松分类，防止标签污染正文。

*   **⚡ 高效交互**
    *   **快捷搜索**：顶部搜索框实时过滤备忘录。
    *   **快捷添加**：底部输入框支持 `#标签` 快速录入。
    *   **后台运行**：关闭窗口自动最小化到托盘，右键托盘可完全退出。

*   **⚙️ 个性化设置**
    *   **开机自启**：支持 Windows 开机自动运行。
    *   **行为定制**：可调节悬浮窗自动淡出的时间，或设置保持置顶。
    *   **暗色主题**：精心调配的现代暗色 UI，护眼且美观。

## 🚀 快速开始

### 环境要求
*   Python 3.10+
*   Windows 10/11

### 安装依赖
```bash
pip install -r requirements.txt
```

### 运行应用
```bash
python main.py
```

## 📦 打包为可执行文件

MemoFlow 提供了便捷的打包工具，可以将应用打包为独立的 Windows 可执行文件（.exe），无需安装 Python 环境即可运行。

### 方法一：使用打包脚本（推荐）

1. **安装打包工具**
   ```bash
   pip install pyinstaller
   ```

2. **运行打包脚本**
   ```bash
   python build.py
   ```

   脚本会自动：
   - 检查 Python 版本（需要 3.10+）
   - 检查主文件是否存在
   - 检查并提示安装 PyInstaller（如未安装）
   - 清理之前的构建文件（可选）
   - 打包应用为单个可执行文件
   - 显示文件大小和位置信息

3. **调试模式**（如遇问题）
   ```bash
   python build.py --debug
   # 或
   python build.py -d
   ```
   调试模式会显示详细的打包过程和错误信息，帮助排查问题。

4. **跳过清理**（保留之前的构建文件）
   ```bash
   python build.py --no-clean
   ```

3. **获取可执行文件**
   - 打包完成后，可执行文件位于 `dist/MemoFlow.exe`
   - 建议将 `MemoFlow.exe` 放在单独的文件夹中，因为它会在同目录下创建配置文件

### 方法二：使用 PyInstaller 直接打包

1. **安装 PyInstaller**
   ```bash
   pip install pyinstaller
   ```

2. **使用 .spec 文件打包（推荐）**
   ```bash
   pyinstaller MemoFlow.spec
   ```

3. **或使用命令行参数打包**
   ```bash
   pyinstaller --name=MemoFlow --onefile --windowed --add-data="settings.json;." main.py
   ```

### 打包说明

- **输出位置**：打包后的可执行文件位于 `dist/` 目录
- **文件大小**：首次打包可能较大（约 50-100MB），因为包含了完整的 Python 运行时和 PyQt6 库
- **首次运行**：打包后的 .exe 文件首次运行可能需要几秒钟来解压临时文件
- **配置文件**：应用会在可执行文件同目录下自动创建 `settings.json` 和 `memos.json`
- **图标**：如需添加应用图标，将图标文件命名为 `icon.ico` 并放在项目根目录，然后修改 `build.py` 或 `MemoFlow.spec` 中的图标配置

### 打包选项说明

**build.py 参数：**
- `--debug` 或 `-d`：启用调试模式，显示详细的打包日志
- `--no-clean`：跳过清理步骤，保留之前的构建文件

**PyInstaller 选项：**
- `--onefile`：打包为单个可执行文件，便于分发
- `--windowed`：不显示控制台窗口（GUI 应用推荐）
- `--add-data`：包含数据文件（配置文件、数据文件等）
- `--hidden-import`：显式包含可能被遗漏的模块

### 故障排除

如果打包过程中遇到问题：

1. **检查 Python 版本**
   - 确保使用 Python 3.10 或更高版本
   - 运行 `python --version` 检查

2. **使用调试模式**
   ```bash
   python build.py --debug
   ```
   这会显示详细的错误信息，帮助定位问题

3. **检查依赖**
   - 确保已安装所有依赖：`pip install -r requirements.txt`
   - 确保 PyInstaller 已正确安装：`pip install pyinstaller`

4. **常见错误**
   - **ModuleNotFoundError**：在 `build.py` 中添加 `--hidden-import=模块名`
   - **文件找不到**：检查 `settings.json` 和 `memos.json` 是否存在
   - **打包失败**：尝试使用 `--debug` 模式查看详细错误

## 📝 开发说明
