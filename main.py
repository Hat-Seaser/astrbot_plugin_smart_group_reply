from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star


class SmartGroupReply(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def test_group_message(self, event: AstrMessageEvent):
        logger.info(
            "[SmartGroupReply] 收到群消息: sender=%s group=%s text=%s",
            event.get_sender_id(),
            event.get_group_id(),
            event.message_str,
        )