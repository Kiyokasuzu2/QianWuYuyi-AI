import aiohttp
import json
from astrbot.api.all import *

@register("astrbot_plugin_yuyi", "Kiyokasuzu", "浅雾羽依 AI 的 AstrBot 插件", "1.0.0")
class YuyiPlugin(StarlettePluginBundle):
    async def initialize(self):
        self.yuyi_api_url = "http://localhost:5000/api/chat"
        
    @command("羽依")
    async def chat_with_yuyi(self, event: AstrBotEvent, message: str):
        '''与浅雾羽依对话'''
        try:
            user_id = event.get_sender_id()
            user_name = event.get_sender_name()
            group_id = event.get_group_id()
            
            async with aiohttp.ClientSession() as session:
                payload = {
                    "user_id": user_id,
                    "user_name": user_name,
                    "group_id": group_id,
                    "message": message,
                    "timestamp": event.get_timestamp()
                }
                async with session.post(self.yuyi_api_url, json=payload, timeout=30) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        reply = result.get("reply", "羽依好像走神了...")
                    else:
                        reply = f"抱歉，连接羽依时出错了 (状态码: {resp.status})"
        except asyncio.TimeoutError:
            reply = "羽依思考时间太长了，请稍后再试试。"
        except Exception as e:
            reply = f"发生了一个错误: {str(e)}"
        
        yield event.plain_result(reply)
