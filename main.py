from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.message_components import At, Plain
from astrbot.api.provider import Provider
from astrbot.api.star import Context, Star

from .core import DEFAULT_PATTERN, PluginConfig, RouteManager


class RouterPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.plugin_config = PluginConfig(config)
        self.manager = RouteManager(self.plugin_config)

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("添加路由")
    async def add_router(self, event: AstrMessageEvent):
        """Add or replace a user's route using the provider command's LLM index.

        Args:
            event: Command event containing a user mention and a provider index.
        """
        target_id = ""
        for component in event.get_messages():
            if isinstance(component, At):
                mentioned_id = str(component.qq).strip()
                if mentioned_id not in {"", "all", str(event.get_self_id())}:
                    target_id = mentioned_id
                    break

        text = " ".join(
            component.text
            for component in event.get_messages()
            if isinstance(component, Plain)
        )
        try:
            index = int(text.split()[-1])
        except (ValueError, IndexError):
            yield event.plain_result(
                "命令格式：添加路由 @某人 序号（使用 provider 列出的 LLM 序号）"
            )
            return
        if not target_id:
            yield event.plain_result(
                "命令格式：添加路由 @某人 序号，请 @ 要添加路由的用户。"
            )
            return

        providers = list(self.context.get_all_providers())
        if index < 1 or index > len(providers):
            yield event.plain_result(
                "模型序号无效，请先使用 provider 查看当前 LLM 模型列表。"
            )
            return
        provider_id = providers[index - 1].meta().id

        try:
            self.manager.set_user_route(
                user_id=target_id,
                provider_id=provider_id,
                pattern=DEFAULT_PATTERN,
                enabled=True,
            )
        except Exception:
            logger.exception(
                "[router] Failed to save the route for user '%s'.", target_id
            )
            yield event.plain_result("路由保存失败，请检查日志后重试。")
            return

        yield event.plain_result(
            f"已添加路由\n用户：{target_id}\n模型：{provider_id}\n触发正则：{DEFAULT_PATTERN}"
        )

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("删除路由")
    async def delete_router(self, event: AstrMessageEvent):
        """Delete all routing entries for the mentioned user and save the config.

        Args:
            event: Command event containing the user mention to remove.
        """
        target_id = ""
        for component in event.get_messages():
            if isinstance(component, At):
                mentioned_id = str(component.qq).strip()
                if mentioned_id not in {"", "all", str(event.get_self_id())}:
                    target_id = mentioned_id
                    break
        if not target_id:
            yield event.plain_result("命令格式：删除路由 @某人")
            return

        try:
            deleted = self.manager.delete_user_routes(target_id)
        except Exception:
            logger.exception(
                "[router] Failed to delete routes for user '%s'.", target_id
            )
            yield event.plain_result("路由删除失败，请检查日志后重试。")
            return

        if not deleted:
            yield event.plain_result(f"用户 {target_id} 没有配置路由。")
            return

        yield event.plain_result(
            f"已删除用户 {target_id} 的全部路由，后续对话沿用 AstrBot 原有的模型选择。"
        )

    @filter.command("查看路由")
    async def show_router(self, event: AstrMessageEvent):
        """查看路由 留空/@某人"""
        target_id = str(event.get_sender_id()).strip()
        for component in event.get_messages():
            if isinstance(component, At):
                mentioned_id = str(component.qq).strip()
                if mentioned_id not in {"", "all", str(event.get_self_id())}:
                    target_id = mentioned_id
                    break

        user_entries = self.manager.get_entries_by_user(target_id)
        matched_entries = []
        for entry in user_entries:
            if not entry.enabled:
                continue

            provider_id = str(entry.provider_id or "").strip()
            pattern = str(entry.pattern or "").strip()
            pattern_display = f"触发正则：{pattern}" if pattern else "无正则限制（全匹配）"

            if not provider_id:
                matched_entries.append(f"模型：未设置 ({pattern_display})")
            else:
                provider = self.context.get_provider_by_id(provider_id)
                if isinstance(provider, Provider):
                    matched_entries.append(
                        f"模型：{provider_id} ({pattern_display})"
                    )
                else:
                    matched_entries.append(
                        f"模型：{provider_id}（提供商不存在或无效）({pattern_display})"
                    )

        if not matched_entries:
            status = "未配置启用的路由，沿用 AstrBot 原有的模型选择"
        else:
            status = "\n".join(matched_entries)

        yield event.plain_result(f"用户：{target_id}\n{status}")

    @filter.on_waiting_llm_request()
    async def on_waiting_llm(self, event: AstrMessageEvent) -> None:
        """Apply the first enabled routing entry matching the sender and pattern.

        Args:
            event: Message event whose provider is about to be selected.
        """
        sender_id = str(event.get_sender_id()).strip()
        if not sender_id:
            return

        msg_str = (event.get_message_str() or "").strip()

        provider_id = self.manager.match_provider(sender_id, msg_str)
        if not provider_id:
            return

        provider = self.context.get_provider_by_id(provider_id)
        if not isinstance(provider, Provider):
            logger.warning(
                "[router] Provider '%s' for user '%s' is missing or is not "
                "a chat provider; keeping the original provider selection.",
                provider_id,
                sender_id,
            )
            return

        # Select a provider for this event without changing session preferences.
        event.set_extra("selected_provider", provider_id)
        logger.debug(
            "[router] Routed user '%s' to provider '%s'.",
            sender_id,
            provider_id,
        )
