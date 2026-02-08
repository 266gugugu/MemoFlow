# src/core/theme.py
# -*- coding: utf-8 -*-

class AppTheme:
    """集中管理应用的颜色和样式"""
    """集中管理应用的颜色和样式"""
    COLORS = {
        # 背景色 - 更深邃的蓝灰色调
        "bg_primary": "#1E1E2E",      # 主窗口背景
        "bg_secondary": "#252535",    # 侧边栏/输入区背景
        "bg_hover": "#2A2A3C",        # 悬停背景
        "bg_selected": "#32324A",     # 选中背景
        
        # 边框
        "border": "#353545",          # 柔和边框
        
        # 文本
        "text_primary": "#E4E4F0",    # 主文本 (近白)
        "text_secondary": "#A1A1B5",  # 次要文本 (灰紫)
        "text_tertiary": "#6E6E80",   # 微弱文本
        
        # 强调色 (Teal -> Emerald 渐变感)
        "accent": "#10B981",          # 鲜亮绿
        "accent_hover": "#059669",
        "accent_dim": "rgba(16, 185, 129, 0.15)",
        
        # 功能色
        "danger": "#EF4444",
        "warning": "#F59E0B",
        "tag_bg": "#2A2A3C",          # 标签背景
        "tag_text": "#10B981",        # 标签文字
        
        # 阴影 (用于 QSS)
        "shadow": "rgba(0, 0, 0, 0.25)"
    }

    @staticmethod
    def get_stylesheet(widget_name):
        c = AppTheme.COLORS
        styles = {
            # 搜索框
            "SearchInput": f"""
                QLineEdit {{
                    background-color: {c['bg_secondary']};
                    border: 1px solid {c['border']};
                    border-radius: 8px;
                    padding: 6px 12px;
                    font-size: 13px;
                    color: {c['text_primary']};
                    selection-background-color: {c['accent']};
                }}
                QLineEdit:focus {{
                    border: 1px solid {c['accent']};
                    background-color: {c['bg_secondary']};
                }}
            """,
            
            # 输入框
            "MemoInput": f"""
                QLineEdit {{
                    background-color: {c['bg_secondary']};
                    border: 1px solid {c['border']};
                    border-radius: 8px;
                    padding: 8px 12px;
                    font-size: 13px;
                    color: {c['text_primary']};
                }}
                QLineEdit:focus {{
                    border: 1px solid {c['accent']};
                }}
            """,
            
            # 按钮
            "PrimaryButton": f"""
                QPushButton {{
                    background-color: {c['accent']};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-weight: 600;
                    padding: 4px 12px;
                }}
                QPushButton:hover {{
                    background-color: {c['accent_hover']};
                }}
                QPushButton:pressed {{
                    background-color: {c['accent']};
                    margin-top: 1px;
                }}
            """,
            
            # 标签按钮
            "TagButton": f"""
                QPushButton {{
                    background-color: {c['bg_secondary']};
                    color: {c['text_secondary']};
                    border: 1px solid {c['border']};
                    border-radius: 10px;
                    padding: 2px 10px;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background-color: {c['bg_hover']};
                    color: {c['text_primary']};
                    border-color: {c['text_secondary']};
                }}
            """,
            
            # 列表视图
            "ListView": f"""
                QListView {{
                    background-color: {c['bg_primary']};
                    border: none;
                    outline: none;
                }}
                QListView::item {{ 
                    border: none; 
                }}
            """,
            
            # 悬浮窗
            "FloatingWindow": f"""
                background-color: {c['bg_primary']};
                border: 1px solid {c['border']};
                border-radius: 12px;
            """,
            "TitleLabel": f"""
                color: {c['text_primary']};
                font-size: 14px;
                font-weight: bold;
                font-family: "Segoe UI", "Microsoft YaHei";
            """
        }
        return styles.get(widget_name, "")
