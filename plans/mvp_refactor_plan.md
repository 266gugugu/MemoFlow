# 重构计划：MVP 架构 (Model-View-Presenter)

## 1. 目标
将现有的 PyQt6 代码重构为 MVP 架构，以分离关注点，提高代码的可维护性和可测试性。
View 层将变得“被动”，只负责展示和转发用户输入；Model 层负责数据存储；Presenter 层作为中间人处理逻辑。

## 2. 目录结构设计
```
src/
├── __init__.py
├── main.py              # 入口，负责装配 MVP
├── core/                # 核心业务无关代码
│   ├── __init__.py
│   ├── theme.py         # 主题 (AppTheme)
│   ├── utils.py         # 工具 (AutoStart, Settings 等 - 可拆分)
│   └── signals.py       # (可选) 全局信号
├── model/               # Model 层
│   ├── __init__.py
│   ├── data_store.py    # DataStore (数据存取)
│   ├── memo_model.py    # Memo 数据类
│   └── settings_model.py # Settings (配置数据)
├── view/                # View 层 (UI)
│   ├── __init__.py
│   ├── main_window.py   # MainWindow (主界面)
│   ├── editor_view.py   # Editor (编辑界面)
│   ├── floating_view.py # FloatingWindow (悬浮窗)
│   ├── settings_view.py # SettingsDialog (设置界面)
│   └── widgets/         # 可复用的小组件
│       ├── __init__.py
│       ├── memo_item.py
│       └── tag_button.py
└── presenter/           # Presenter 层 (逻辑)
    ├── __init__.py
    ├── main_presenter.py    # 协调主界面逻辑
    ├── editor_presenter.py  # 协调编辑逻辑
    ├── floating_presenter.py # 协调悬浮窗逻辑
    └── settings_presenter.py # 协调设置逻辑
```

## 3. 详细步骤

### 3.1 准备阶段
- [ ] 备份现有代码（Git commit 或手动备份）。
- [ ] 创建新的目录结构。

### 3.2 Model 层重构
- **`src/model/settings_model.py`**: 封装 `Settings` 类，提供配置读写。
- **`src/model/data_store.py`**: 封装 `DataStore` 类，负责 JSON 读写，CRUD 操作。
- **`src/model/memo_model.py`**: 定义 `Memo` 数据结构（dataclass 或 字典包装），保持数据纯净。

### 3.3 Core & Utils 迁移
- 移动 `theme.py` 到 `src/core/theme.py`。
- 拆分 `utils.py`：
    - `AutoStart` 逻辑保留在 `src/core/autostart.py` 或类似位置。
    - 通用工具函数放入 `src/core/utils.py`。

### 3.4 View 层重构 (Passive View)
- **`src/view/widgets/`**: 迁移 `widgets.py` 中的 `MemoListItemWidget`, `TagButton`。
- **`src/view/main_window.py`**:
    - 继承 `QMainWindow`。
    - **移除**所有业务逻辑（如 `add_memo`, `delete_memo` 的具体实现）。
    - 暴露信号（Signals），例如 `add_memo_requested(text)`, `memo_clicked(memo_id)`。
    - 提供更新 UI 的公共方法，例如 `update_memo_list(memos)`, `clear_input()`。
- **`src/view/editor_view.py`**:
    - 继承 `QDialog` 或 `QWidget`。
    - 暴露 `save_requested(title, content, tags)` 信号。
    - 提供 `set_memo_data(title, content, tags)` 方法。
- **`src/view/floating_view.py`**:
    - 负责悬浮窗的动画、渲染。
    - 逻辑由 Presenter 控制（如请求下一条/上一条）。

### 3.5 Presenter 层实现
- **`src/presenter/main_presenter.py`**:
    - 持有 `MainWindow`, `DataStore`, `SettingsModel`。
    - 连接 View 的信号到 Presenter 的处理函数。
    - 实现业务逻辑：调用 Model -> 更新 View。
    - 处理悬浮窗与主窗口的联动。
- **`src/presenter/editor_presenter.py`** (可选，简单逻辑可合并入 MainPresenter 或独立):
    - 处理编辑、保存、删除逻辑。

### 3.6 入口文件更新
- 更新 `main.py`：
    - 初始化 `QApplication`。
    - 初始化 Models (`Settings`, `DataStore`)。
    - 初始化 Views (`MainWindow`, `FloatingWindow`)。
    - 初始化 Presenters 并绑定 Model 和 View。
    - 显示主窗口。

## 4. 关键变更点
- **解耦**: View 不再直接调用 `DataStore`。
- **信号流**: View (User Action) -> Signal -> Presenter -> Model (Update) -> Presenter (Get Result) -> View (Update UI)。
- **依赖注入**: Presenter 在构造时接收 View 和 Model 实例。

## 5. 待确认
- 是否需要严格定义 Interface (Protocol)? Python 中可以利用鸭子类型，为了开发速度可先不定义严格的 ABC，但在方法命名上保持一致。 -> **决定：暂不强制 ABC，保持 Pythonic，但注重命名规范。**
