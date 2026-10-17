from aiocqhttp import CQHttp

from astrbot.api.event import AstrMessageEvent
from astrbot.core.message.components import At, Plain, Reply


async def get_nickname(client: CQHttp, group_id: int | str, user_id: int | str) -> str:
    """获取指定群友的群昵称或 Q 名，群接口失败/空结果自动降级到陌生人资料"""
    user_id = int(user_id)

    info = {}

    # 在群里就先试群资料，任何异常或空结果都跳过
    if str(group_id).isdigit():
        try:
            info = (
                await client.get_group_member_info(
                    group_id=int(group_id), user_id=user_id
                )
                or {}
            )
        except Exception:
            pass

    # 群资料没拿到就降级到陌生人资料
    if not info:
        try:
            info = await client.get_stranger_info(user_id=user_id) or {}
        except Exception:
            pass

    # 依次取群名片、QQ 昵称、通用 nick，兜底数字 UID
    return info.get("card") or info.get("nickname") or info.get("nick") or str(user_id)


def get_reply_text(event: AstrMessageEvent) -> str:
    """
    获取引用消息的文本
    """
    text = ""
    chain = event.get_messages()
    reply_seg = next((seg for seg in chain if isinstance(seg, Reply)), None)
    if reply_seg and reply_seg.chain:
        for seg in reply_seg.chain:
            if isinstance(seg, Plain):
                text = seg.text
    return text


def get_ats(
    event: AstrMessageEvent,
    noself: bool = False,
    block_ids: list[str] | None = None,
    skip_first_seg: bool = True,
):
    """
    获取被at者们的id列表(@增强版)
    Args:
        event: 消息事件对象
        noself: 是否排除自己
        block_ids: 要排除的id列表
        skip_first_seg: 是否跳过第一个消息段（默认为True）
    """
    segs = event.get_messages()
    segs = segs[1:] if skip_first_seg else segs
    ats = {str(seg.qq) for seg in segs if isinstance(seg, At)}
    ats.update(
        arg[1:]
        for arg in event.message_str.split()
        if arg.startswith("@") and arg[1:].isdigit()
    )
    if noself:
        ats.discard(event.get_self_id())
    if block_ids:
        ats.difference_update(block_ids)
    return list(ats)

def get_index(event: AstrMessageEvent) -> int | None:
    text = " ".join(
        component.text
        for component in event.get_messages()
        if isinstance(component, Plain)
    )
    try:
        index = int(text.split()[-1])
        return index
    except (ValueError, IndexError):
        return None
