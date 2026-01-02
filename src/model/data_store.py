# src/model/data_store.py
# -*- coding: utf-8 -*-
import json
import os
import re
from datetime import datetime
from src.core.utils import MEMOS_PATH
from src.model.memo_model import Memo

class DataStore:
    def __init__(self):
        self.file_path = MEMOS_PATH
        self.memos = self._load_data()

    def _load_data(self):
        if not os.path.exists(self.file_path): return []
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                memos = [Memo.from_dict(item) for item in data]
                return sorted(memos, key=lambda x: x.created_at, reverse=True)
        except:
            return []

    def get_memos(self):
        return self.memos

    def get_memo_by_id(self, memo_id):
        for memo in self.memos:
            if memo.id == memo_id:
                return memo
        return None

    def add_memo(self, raw_text):
        tags = re.findall(r"#(\S+)", raw_text)
        clean_content = re.sub(r"#\S+", "", raw_text).strip()
        if not clean_content: clean_content = "无标题备忘"

        lines = clean_content.split('\n', 1)
        title = lines[0][:20]

        new_memo = Memo(
            id=int(datetime.now().timestamp() * 1000),
            title=title,
            content=clean_content,
            tags=tags
        )
        self.memos.insert(0, new_memo)
        self._save_data()
        return new_memo

    def update_memo(self, memo_id, title, content, tags):
        for memo in self.memos:
            if memo.id == memo_id:
                memo.title = title
                memo.content = content
                memo.tags = tags
                self._save_data()
                return True
        return False

    def delete_memo(self, memo_id):
        initial_len = len(self.memos)
        self.memos = [m for m in self.memos if m.id != memo_id]
        if len(self.memos) < initial_len:
            self._save_data()
            return True
        return False

    def _save_data(self):
        try:
            data = [memo.to_dict() for memo in self.memos]
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except:
            pass
