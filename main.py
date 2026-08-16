import random
import time

from astrbot.api import logger, AstrBotConfig
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star


class SmartGroupReply(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)

        self.admin_ids = {
            str(x) for x in config.get("admin_ids", [])
        }

        self.group_ids = {
            str(x) for x in config.get("group_ids", [])
        }

        self.admin_probability = float(
            config.get("admin_probability", 0.95)
        )

        self.member_probability = float(
            config.get("member_probability", 0.10)
        )

        self.cooldown_seconds = float(
            config.get("cooldown_seconds", 5.0)
        )

        self.enabled = bool(
            config.get("enabled", True)
        )

        self.last_wake_time: dict[str, float] = {}

        logger.info(
            "[SmartGroupReply] 管理员概率=%.2f 普通成员概率=%.2f 冷却=%.1fs",
            self.admin_probability,
            self.member_probability,
            self.cooldown_seconds,
        )

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    @filter.platform_adapter_type(
        filter.PlatformAdapterType.AIOCQHTTP
    )
    async def group_reply_gate(
        self,
        event: AstrMessageEvent,
    ):
        if not self.enabled:
            return

        group_id = event.get_group_id()
        sender_id = event.get_sender_id()
        self_id = event.get_self_id()

        if not group_id:
            return

        group_id = str(group_id)
        sender_id = str(sender_id)

        if self.group_ids and group_id not in self.group_ids:
            return

        if self_id is not None and sender_id == str(self_id):
            return

        # 已经 @ 机器人时，不干涉原有机制
        if event.is_at_or_wake_command:
            return

        now = time.monotonic()
        last_time = self.last_wake_time.get(group_id, 0.0)

        if now - last_time < self.cooldown_seconds:
            return

        if sender_id in self.admin_ids:
            probability = self.admin_probability
            role = "admin"
        else:
            probability = self.member_probability
            role = "member"

        if random.random() >= probability:
            return

        event.is_wake = True
        event.is_at_or_wake_command = True

        self.last_wake_time[group_id] = now

        logger.info(
            "[SmartGroupReply] 主动唤醒 "
            "group=%s sender=%s role=%s probability=%.2f",
            group_id,
            sender_id,
            role,
            probability,
        )
