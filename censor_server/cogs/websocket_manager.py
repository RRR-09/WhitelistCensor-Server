import asyncio
import json
from enum import Enum
from typing import Any, Set

import websockets
from discord.ext import commands  # type: ignore
from utils import BotClass


class WSFunction(str, Enum):
    WHITELIST_REQUEST = "WHITELIST_REQUEST"


class WSResponse(str, Enum):
    COMPLETE = "COMPLETE"


class WSManager:
    def __init__(self, valid_ids: Set[str]):
        self.connections: Set[Any] = set()
        self.valid_ids = valid_ids

    async def ws_handler(self, websocket):
        raw_data = await websocket.recv()
        try:
            data = json.loads(raw_data)
        except Exception:
            await websocket.close(code=1003, reason="Invalid JSON")
            return

        client_id = data.get("id")
        if client_id not in self.valid_ids:
            await websocket.close(code=1003, reason="Invalid Auth")
            return

        func = data.get("function")
        if func not in WSFunction.__members__:
            await websocket.close(code=1003, reason="Invalid Function")
            return

        print(data)

        response = {"id": client_id, "message": WSResponse.COMPLETE}

        await websocket.send(json.dumps(response))

        await websocket.close(reason="Complete")

    def message_all(self, message):
        print(f"[WS] Sent: {message}")
        websockets.broadcast(self.connections, message)

    def message_all_silent(self, message):
        websockets.broadcast(self.connections, message)


class WebsocketManagerCog(commands.Cog):
    def __init__(self, bot: BotClass):
        self.bot = bot
        authorized_clients: Set[str] = self.bot.CFG.get("ws_authorized_clients", set())
        self.ws_manager = WSManager(authorized_clients)
        asyncio.create_task(self.ws_init())

    async def ws_init(self):
        async with websockets.serve(self.ws_manager.ws_handler, "127.0.0.1", 8087):
            await asyncio.Future()  # run forever
