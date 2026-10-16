from __future__ import annotations

import re
from typing import Any

from astrbot.api import logger

from .config import ConfigNode

DEFAULT_PATTERN = r"^干活："


class RouteEntry(ConfigNode):
    """模型路由条目模型。"""

    user_id: str
    enabled: bool
    pattern: str
    provider_id: str

    def __init__(self, data: dict[str, Any]):
        # 兼容旧配置中的 prefix 或缺省 pattern
        if "pattern" not in data:
            if "prefix" in data:
                data["pattern"] = str(data["prefix"])
            else:
                data["pattern"] = DEFAULT_PATTERN
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

        pattern_str = str(self.pattern or "").strip()
        if not pattern_str:
            return True

        if self._compiled_pattern is None:
            # 重新尝试编译，若依然不合法则匹配失败
            try:
                self._compiled_pattern = re.compile(pattern_str)
            except re.error:
                return False

        return bool(self._compiled_pattern.search(message))

    def to_dict(self) -> dict[str, Any]:
        return dict(self._data)
