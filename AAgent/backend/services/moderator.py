"""
Moderator Service - 主持人服务
"""

import asyncio
import os
import logging
import random
import json
from typing import Dict, List
from db.database import open_db
from services.expert import build_system_prompt
from services.ai_service import generate_expert_response, generate_consensus
from services.sse_service import (
    broadcast_message, broadcast_consensus,
    broadcast_complete, broadcast_error, broadcast_status
)

logger = logging.getLogger(__name__)

MODERATOR = {
    "id": 0,
    "name": "主持人",
    "role": "圆桌主持人",
    "avatar_color": "#6366F1"
}

EXPERT_STATES = {
    "idle": "待机",
    "thinking": "准备发言",
    "speaking": "发言中"
}


class Moderator:
    def __init__(self, discussion_id: int):
        self.discussion_id = discussion_id
        self.is_running = False
        self.max_rounds = int(os.getenv("MAX_ROUNDS", "3"))
        self.current_round = 0
        self.participants = []
        self.all_messages: List[Dict] = []

    async def start_discussion(self):
        if self.is_running:
            raise Exception("讨论已在进行中")
        self.is_running = True
        try:
            logger.info(f"[主持人] 启动讨论 #{self.discussion_id}")
            discussion = await self.load_discussion()
            self.participants = await self.load_participants()

            if len(self.participants) < 3:
                raise Exception("参与专家数量不足（至少需要3位）")

            await self.update_discussion_status("running")
            await self._moderator_speak(
                f"欢迎各位专家参加本次圆桌讨论！今天我们围绕「{discussion['title']}」这一话题展开探讨。"
                f"请各位从自身专业视角出发，畅所欲言。先请各位做简短的开场表态。"
            )
            await self.conduct_discussion(discussion)
            await self._moderator_speak(
                "感谢各位专家的精彩发言！接下来我将对本次讨论进行总结，提炼各方的共识与分歧。"
            )
            await self.generate_and_save_consensus(discussion)
            await self.complete_discussion()
            logger.info(f"[主持人] 讨论 #{self.discussion_id} 成功完成")
        except Exception as e:
            logger.error(f"[主持人] 讨论 #{self.discussion_id} 失败: {e}")
            await self.fail_discussion(str(e))
            raise
        finally:
            self.is_running = False

    async def conduct_discussion(self, discussion: Dict):
        for round_num in range(1, self.max_rounds + 1):
            self.current_round = round_num

            if round_num > 1:
                await self._moderator_speak(
                    f"进入第 {round_num} 轮深入探讨。请各位针对刚才的观点进行回应、补充或反驳。"
                )

            ordered = await self._decide_speaking_order(discussion, round_num)

            for participant in ordered:
                await self._broadcast_expert_state(participant["id"], "thinking")
                await asyncio.sleep(1)

                logger.info(f"[主持人] 第{round_num}轮 - {participant['name']} 发言中...")

                previous_messages = await self.load_previous_messages()
                system_prompt = build_system_prompt(
                    participant,
                    {"title": discussion["title"], "description": discussion.get("description", "")},
                    previous_messages,
                    round_num
                )

                if len(previous_messages) == 0:
                    user_msg = (
                        f'请就「{discussion["title"]}」发表你的专业开场观点，'
                        f'用1-2句话简洁表达核心立场。'
                    )
                else:
                    last = previous_messages[-1]
                    user_msg = (
                        f'刚才 {last["participant"]["name"]} 说："{last["content"][:80]}..."\n'
                        f'请你用1-2句话，选择【补充/反驳/追问】其中一种方式回应，并说明理由。'
                    )

                await self._broadcast_expert_state(participant["id"], "speaking")

                try:
                    response_text = await generate_expert_response(
                        system_prompt, user_msg, temperature=0.85, max_tokens=200
                    )
                except Exception as ai_err:
                    logger.error(f"AI生成失败: {ai_err}")
                    response_text = f"{participant['name']} 暂时无法发言，稍后继续。"

                msg_id = await self.save_message(participant["id"], response_text, round_num)
                self.all_messages.append({
                    "id": msg_id,
                    "participant": participant,
                    "content": response_text,
                    "round": round_num
                })

                await broadcast_message(self.discussion_id, {
                    "participant": {
                        "id": participant["id"],
                        "name": participant["name"],
                        "role": participant["role"],
                        "avatar_color": participant["avatar_color"]
                    },
                    "content": response_text,
                    "round": round_num,
                    "is_moderator": False,
                    "timestamp": None
                })

                await self._broadcast_expert_state(participant["id"], "idle")

                if len(self.all_messages) % 2 == 0:
                    await self._broadcast_realtime_consensus(discussion["title"])

                await asyncio.sleep(2)

    async def _moderator_speak(self, text: str):
        await broadcast_message(self.discussion_id, {
            "participant": MODERATOR,
            "content": text,
            "round": self.current_round,
            "is_moderator": True,
            "timestamp": None
        })
        await asyncio.sleep(1.5)

    async def _decide_speaking_order(self, discussion: Dict, round_num: int) -> List[Dict]:
        if len(self.all_messages) < 2:
            shuffled = self.participants.copy()
            random.shuffle(shuffled)
            return shuffled
        try:
            names = [p["name"] for p in self.participants]
            recent = self.all_messages[-4:]
            context = "\n".join(
                f'{m["participant"]["name"]}({m["participant"]["role"]}): {m["content"]}'
                for m in recent
            )
            system_prompt = (
                "你是圆桌讨论主持人。根据讨论内容，决定本轮各专家发言顺序。\n"
                "原则：有争议的先说，想补充的跟上，最后综合。\n"
                f"专家列表：{', '.join(names)}\n"
                "只输出按顺序排列的名字，英文逗号分隔，不要其他内容。"
            )
            order_str = await generate_expert_response(
                system_prompt,
                f"最近发言：\n{context}\n\n请决定本轮发言顺序：",
                temperature=0.3, max_tokens=50
            )
            ordered_names = [n.strip() for n in order_str.replace("，", ",").split(",")]
            ordered = []
            used = set()
            for name in ordered_names:
                for p in self.participants:
                    if p["name"] == name and p["id"] not in used:
                        ordered.append(p)
                        used.add(p["id"])
                        break
            for p in self.participants:
                if p["id"] not in used:
                    ordered.append(p)
            return ordered
        except Exception as e:
            logger.warning(f"自主顺序决策失败，使用随机: {e}")
            shuffled = self.participants.copy()
            random.shuffle(shuffled)
            return shuffled

    async def _broadcast_realtime_consensus(self, title: str):
        try:
            system_prompt = (
                "你是讨论分析助手。根据当前发言实时提炼共识与分歧。\n"
                "只输出纯JSON，不要markdown代码块，格式：\n"
                '{"agreements": ["共识1", "共识2"], "divergences": ["分歧1"]}'
            )
            user_msg = (
                f"话题：{title}\n最近发言：\n" +
                "\n".join(
                    f'{m["participant"]["name"]}: {m["content"]}'
                    for m in self.all_messages[-6:]
                )
            )
            raw = await generate_expert_response(system_prompt, user_msg, temperature=0.3, max_tokens=300)
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start == -1 or end <= start:
                return
            result = json.loads(raw[start:end])
            await broadcast_status(self.discussion_id, {
                "type": "realtime_consensus",
                "agreements": result.get("agreements", []),
                "divergences": result.get("divergences", [])
            })
        except Exception as e:
            logger.debug(f"实时共识更新跳过: {e}")

    async def _broadcast_expert_state(self, participant_id: int, state: str):
        await broadcast_status(self.discussion_id, {
            "type": "expert_state",
            "participantId": participant_id,
            "state": state,
            "stateText": EXPERT_STATES.get(state, state)
        })

    async def generate_and_save_consensus(self, discussion: Dict):
        logger.info(f"[主持人] 生成讨论共识...")
        async with open_db() as db:
            cursor = await db.execute("""
                SELECT m.*, p.name as participant_name, p.role as participant_role
                FROM messages m
                JOIN participants p ON m.participant_id = p.id
                WHERE m.discussion_id = ?
                ORDER BY m.round_number, m.created_at
            """, (self.discussion_id,))
            all_messages = await cursor.fetchall()
            if not all_messages:
                return

            msgs_for_consensus = [
                {
                    "participant_name": m["participant_name"],
                    "participant_role": m["participant_role"],
                    "content": m["content"]
                }
                for m in all_messages
            ]
            try:
                consensus = await generate_consensus(discussion["title"], msgs_for_consensus)
            except Exception as e:
                logger.error(f"AI共识生成失败: {e}")
                consensus = self.generate_fallback_consensus(list(all_messages), discussion["title"])

            await db.execute(
                "INSERT INTO consensus (discussion_id, summary, key_points) VALUES (?, ?, ?)",
                (
                    self.discussion_id,
                    consensus["summary"],
                    json.dumps(consensus.get("keyPoints", []), ensure_ascii=False)
                )
            )
            await db.commit()

        await broadcast_consensus(self.discussion_id, {
            "summary": consensus["summary"],
            "keyPoints": consensus.get("keyPoints", []),
            "timestamp": None
        })
        logger.info("[主持人] 共识生成完成")

    def generate_fallback_consensus(self, messages: List, title: str) -> Dict:
        names = list(set(m["participant_name"] for m in messages))
        return {
            "summary": (
                f'本次关于「{title}」的讨论中，{"、".join(names)}等{len(names)}位专家'
                f'进行了{len(messages)}次深入交流，从多个专业视角形成了丰富的观点碰撞。'
            ),
            "keyPoints": [
                "专家们进行了多轮深入探讨",
                "从多个专业角度分析了核心问题",
                "提出了具有建设性的解决思路"
            ]
        }

    async def load_discussion(self) -> Dict:
        async with open_db() as db:
            cursor = await db.execute(
                "SELECT * FROM discussions WHERE id = ?", (self.discussion_id,)
            )
            row = await cursor.fetchone()
        if not row:
            raise Exception(f"讨论 #{self.discussion_id} 不存在")
        return dict(row)

    async def load_participants(self) -> List[Dict]:
        async with open_db() as db:
            cursor = await db.execute(
                "SELECT * FROM participants WHERE discussion_id = ? ORDER BY order_index",
                (self.discussion_id,)
            )
            rows = await cursor.fetchall()
        return [dict(p) for p in rows]

    async def load_previous_messages(self) -> List[Dict]:
        async with open_db() as db:
            cursor = await db.execute("""
                SELECT m.*, p.name as participant_name, p.role as participant_role, p.avatar_color
                FROM messages m
                JOIN participants p ON m.participant_id = p.id
                WHERE m.discussion_id = ?
                ORDER BY m.round_number, m.created_at
            """, (self.discussion_id,))
            rows = await cursor.fetchall()
        return [
            {
                "participant": {
                    "name": m["participant_name"],
                    "role": m["participant_role"],
                    "avatar_color": m["avatar_color"]
                },
                "content": m["content"]
            }
            for m in rows
        ]

    async def save_message(self, participant_id: int, content: str, round_number: int) -> int:
        async with open_db() as db:
            cursor = await db.execute(
                "INSERT INTO messages (discussion_id, participant_id, content, round_number) "
                "VALUES (?, ?, ?, ?)",
                (self.discussion_id, participant_id, content, round_number)
            )
            await db.commit()
            return cursor.lastrowid

    async def update_discussion_status(self, status: str):
        async with open_db() as db:
            await db.execute(
                "UPDATE discussions SET status = ? WHERE id = ?",
                (status, self.discussion_id)
            )
            await db.commit()

    async def complete_discussion(self):
        await self.update_discussion_status("completed")
        async with open_db() as db:
            cursor = await db.execute(
                "SELECT COUNT(*) as count FROM messages WHERE discussion_id = ?",
                (self.discussion_id,)
            )
            count = (await cursor.fetchone())[0]
        await broadcast_complete(self.discussion_id, {
            "discussionId": self.discussion_id,
            "status": "completed",
            "totalRounds": self.max_rounds,
            "totalMessages": count,
            "timestamp": None
        })

    async def fail_discussion(self, reason: str):
        await self.update_discussion_status("failed")
        await broadcast_error(self.discussion_id, {"message": reason, "timestamp": None})


async def run_discussion(discussion_id: int):
    moderator = Moderator(discussion_id)
    await moderator.start_discussion()
