import random
import time

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star


class SmartGroupReply(Star):
    """
    智能群聊优先回复。

    功能：
    1. 指定管理员高概率主动参与群聊。
    2. 普通群友低概率主动参与群聊。
    3. 不自己调用 LLM。
    4. 不自己发送消息。
    5. @机器人时不干涉原有逻辑。
    """

    def __init__(self, context: Context):
        super().__init__(context)

        # =========================
        # 基础配置
        # =========================

        # 你的 QQ 大号
        self.admin_ids = {
            "XXX",
        }

        # 只在这些群启用主动回复概率
        self.group_ids = {
            "XXX",
            "XXX", 
        }

        # 管理员主动回复概率
        self.admin_probability = 0.85

        # 普通群友主动回复概率
        self.member_probability = 0.1

        # 两次主动唤醒之间的最短间隔（秒）
        # 防止群里连续刷屏。
        self.cooldown_seconds = 8.0

        # 保存每个群最近一次主动唤醒时间
        self.last_wake_time: dict[str, float] = {}

        logger.info(
            "[SmartGroupReply] 已加载："
            "管理员概率=%.2f，普通成员概率=%.2f，冷却=%ss",
            self.admin_probability,
            self.member_probability,
            self.cooldown_seconds,
        )

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    @filter.platform_adapter_type(filter.PlatformAdapterType.AIOCQHTTP)
    async def group_reply_gate(self, event: AstrMessageEvent):
        """
        群聊消息入口。

        本插件只改变唤醒状态，不发送消息。
        """

        group_id = event.get_group_id()
        sender_id = event.get_sender_id()
        self_id = event.get_self_id()

        if not group_id:
            return

        group_id = str(group_id)
        sender_id = str(sender_id)
        self_id = str(self_id) if self_id is not None else ""

        # 只处理指定群
        if group_id not in self.group_ids:
            return

        # 忽略 Bot 自己发送的消息
        if sender_id and sender_id == self_id:
            return

        # 已经被 @ / 唤醒的消息完全不干涉
        if event.is_at_or_wake_command:
            return

        # 冷却控制
        now = time.monotonic()
        last_time = self.last_wake_time.get(group_id, 0.0)

        if now - last_time < self.cooldown_seconds:
            return

        # 判断发送者身份
        if sender_id in self.admin_ids:
            probability = self.admin_probability
            role = "admin"
        else:
            probability = self.member_probability
            role = "member"

        # 随机判断
        if random.random() >= probability:
            return

        # 标记本消息为唤醒消息
        event.is_wake = True
        event.should_call_llm(True)

        self.last_wake_time[group_id] = now

        logger.info(
            "[SmartGroupReply] 主动唤醒："
            "group=%s sender=%s role=%s probability=%.2f",
            group_id,
            sender_id,
            role,
            probability,
        )
