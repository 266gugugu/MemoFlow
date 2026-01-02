# src/model/memo_model.py
# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
from datetime import datetime
from typing import List

@dataclass
class Memo:
    id: int
    title: str
    content: str
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    time_str: str = field(default_factory=lambda: datetime.now().strftime("%H:%M"))

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "tags": self.tags,
            "created_at": self.created_at,
            "time_str": self.time_str
        }

    @staticmethod
    def from_dict(data: dict):
        return Memo(
            id=data.get("id", 0),
            title=data.get("title", ""),
            content=data.get("content", ""),
            tags=data.get("tags", []),
            created_at=data.get("created_at", ""),
            time_str=data.get("time_str", "")
        )
