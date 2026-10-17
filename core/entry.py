from __future__ import annotations

import re
from typing import Any

from astrbot.api import logger

from .config import ConfigNode


class RouteEntry(ConfigNode):
    """模型路由条目模型。"""

    user_id: str
    enabled: bool
    pattern: str
    provider_id: str

    def __init__(self, data: dict[str, Any]):
        data.setdefault("enabled", True)
        data.setdefault("user_id", "")
        data.setdefault("provider_id", "")
        data.setdefault("__template_key", "default")

        super().__init__(data)
        self._compiled_pattern: re.Pattern | None = None
        self._compile_pattern()

    def _compile_pattern(self) -> None:
        p = str(self.pattern or "").strip()
        if not p:
            self._compiled_pattern = None
            return
        try:
            self._compiled_pattern = re.compile(p)
        except re.error as e:
            logger.warning(
                "[router] 条目正则语法错误 '%s' (user_id: %s): %s",
                p,
                self.user_id,
                e,
            )
            self._compiled_pattern = None

    def update_pattern(self, pattern: str) -> None:
        self.pattern = pattern
        self._compile_pattern()

    def matches(self, sender_id: str, message: str) -> bool:
        """检查用户 ID 与消息内容是否匹配此路由条目。"""
        if not self.enabled:
            return False
        if str(self.user_id).strip() != str(sender_id).strip():
            return False

        if self._compiled_pattern is None:
            return False
        return bool(self._compiled_pattern.search(message))

    def to_dict(self) -> dict[str, Any]:
        return dict(self._data)
