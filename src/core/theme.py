# src/core/theme.py
# -*- coding: utf-8 -*-

class AppTheme:
    """集中管理应用的颜色和样式"""
    COLORS = {
        "bg_primary": "#2d2d30",
        "bg_secondary": "#3e3e42",
        "border": "#565869",
        "text_primary": "#ECECF1",
        "text_secondary": "#9CA3AF",
        "text_time": "#6B7280",
        "accent": "#10A37F",
        "tag_bg": "rgba(16, 163, 127, 0.12)",
        "shadow": "rgba(0, 0, 0, 120)"
    }

    @staticmethod
    def get_stylesheet(widget_name):
        c = AppTheme.COLORS
        styles = {
            "FloatingWindow": f"background-color: {c['bg_primary']}; border: 1px solid {c['border']}; border-radius: 12px;",
            "TitleLabel": f"color: {c['text_primary']}; font-size: 16px; font-weight: bold;",
            "ContentText": f"color: {c['text_primary']}; font-size: 13px; border: none; background: transparent;",
            "ListTitle": f"color: {c['text_primary']}; font-size: 14px; font-weight: 600;",
            "ListTime": f"color: {c['text_time']}; font-size: 12px;",
            "ListPreview": f"color: {c['text_secondary']}; font-size: 12px;",
            "Tag": f"color: {c['accent']}; font-size: 11px; background-color: {c['tag_bg']}; border-radius: 10px; padding: 2px 8px;"
        }
        return styles.get(widget_name, "")
