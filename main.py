from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.message_components import At
from astrbot.api.provider import Provider
from astrbot.api.star import Context, Star


class RouterPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.entries = self.config.get("entry_storage", []) or []

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

        status = "未配置启用的路由，沿用 AstrBot 原有的模型选择"
        for entry in self.entries:
            if not isinstance(entry, dict) or not entry.get("enabled", True):
                continue
            if str(entry.get("user_id") or "").strip() != target_id:
                continue

            provider_id = str(entry.get("provider_id") or "").strip()
            if not provider_id:
                status = "路由提供商为空，沿用 AstrBot 原有的模型选择"
            else:
                provider = self.context.get_provider_by_id(provider_id)
                if isinstance(provider, Provider):
                    status = f"模型：{provider_id}"
                else:
                    status = (
                        f"路由提供商：{provider_id}\n"
                        "提供商不存在或不是对话模型，沿用 AstrBot 原有的模型选择。"
                    )
            break

        yield event.plain_result(f"用户：{target_id}\n{status}")

    @filter.on_waiting_llm_request()
    async def on_waiting_llm(self, event: AstrMessageEvent) -> None:
        """Apply the first enabled routing entry matching the sender.

        Args:
            event: Message event whose provider is about to be selected.
        """
        sender_id = str(event.get_sender_id()).strip()
        if not sender_id:
            return

        for entry in self.entries:
            if not isinstance(entry, dict) or not entry.get("enabled", True):
                continue
            if str(entry.get("user_id") or "").strip() != sender_id:
                continue

            provider_id = str(entry.get("provider_id") or "").strip()
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
                "[router] Routed user '%s' to provider '%s'.", sender_id, provider_id
            )
            return
