from __future__ import annotations

from typing import Any

from astrbot.api import logger

from .config import PluginConfig
from .entry import DEFAULT_PATTERN, RouteEntry


class RouteManager:
    """路由条目管理器，负责条目的增删改查、持久化与请求匹配。"""

    def __init__(self, config: PluginConfig):
        self.cfg = config
        self.entries: list[RouteEntry] = []
        self.load_entries()

    def load_entries(self) -> None:
        """从配置加载并实例化所有条目。"""
        self.entries = [
            RouteEntry(item)
            for item in self.cfg.entry_storage
            if isinstance(item, dict)
        ]

    def _sync_storage(self) -> None:
        """同步回写底层配置列表并保存。"""
        self.cfg.entry_storage = [entry._data for entry in self.entries]
        self.cfg.save_config()

    def get_entries_by_user(self, user_id: str) -> list[RouteEntry]:
        """获取指定用户的所有路由条目。"""
        target = str(user_id).strip()
        return [
            entry
            for entry in self.entries
            if str(entry.user_id).strip() == target
        ]

    def set_user_route(
        self,
        user_id: str,
        provider_id: str,
        pattern: str = DEFAULT_PATTERN,
        enabled: bool = True,
    ) -> RouteEntry:
        """添加或替换用户的路由配置。"""
        target = str(user_id).strip()
        # 移除该用户的已有条目
        self.entries = [
            e for e in self.entries if str(e.user_id).strip() != target
        ]

        raw_data: dict[str, Any] = {
            "__template_key": "default",
            "user_id": target,
            "enabled": enabled,
            "pattern": pattern,
            "provider_id": provider_id,
        }
        new_entry = RouteEntry(raw_data)
        self.entries.append(new_entry)
        self._sync_storage()
        return new_entry

    def delete_user_routes(self, user_id: str) -> bool:
        """删除指定用户的全部路由条目。若存在删除项则返回 True。"""
        target = str(user_id).strip()
        initial_len = len(self.entries)
        self.entries = [
            e for e in self.entries if str(e.user_id).strip() != target
        ]
        if len(self.entries) != initial_len:
            self._sync_storage()
            return True
        return False

    def match_provider(self, sender_id: str, message: str) -> str | None:
        """按顺序匹配第一条命中的条目，返回对应 provider_id。"""
        target = str(sender_id).strip()
        if not target:
            return None

        for entry in self.entries:
            if entry.matches(target, message):
                provider_id = str(entry.provider_id or "").strip()
                if provider_id:
                    return provider_id
        return None
