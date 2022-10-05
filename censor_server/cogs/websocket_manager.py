import asyncio
import json
from asyncio import sleep as async_sleep
from enum import Enum
from time import time
from typing import Callable, Set

import websockets
from discord.ext import commands  # type: ignore
from utils import BotClass, do_log


class WSFunction(str, Enum):
    AUTH = "AUTH"
    WHITELIST_REQUEST = "WHITELIST_REQUEST"


class WSResponse(str, Enum):
    COMPLETE = "COMPLETE"
    AUTH_SUCCESS = "AUTH_SUCCESS"
    AUTH_FAIL = "AUTH_FAIL"
    WHITELIST_UPDATE = "WHITELIST_UPDATE"


class WSManager:
    def __init__(
        self, server_id: str, valid_ids: Set[str], request_whitelist_func: Callable
    ):
        self.server_id = server_id
        self.connections: Set[str] = set()
        self.valid_ids = valid_ids
        self.request_whitelist_func = request_whitelist_func

    async def process_message(self, websocket, raw_message):
        try:
            message = json.loads(raw_message)
        except Exception:
            await websocket.close(code=1003, reason="Invalid JSON")
            return

        client_id = message.get("id")
        if client_id not in self.valid_ids:
            await websocket.close(code=1003, reason="Invalid Auth")
            return

        func = message.get("function")
        if func not in WSFunction.__members__:
            await websocket.close(code=1003, reason="Invalid Function")
            return

        backup_timestamp = f"servermsg_{str(time()).replace('.','')}"
        timestamp = message.get("timestamp", backup_timestamp)
        response_message = WSResponse.COMPLETE

        if func == WSFunction.AUTH:
            do_log(f"[WS] Authed {client_id}")
            response_message = WSResponse.AUTH_SUCCESS
        elif func == WSFunction.WHITELIST_REQUEST:
            data = message.get("data")
            do_log(f"[WS] Whitelist Request: \n{data}\n")
            await self.request_whitelist_func(data)

        response = {
            "id": client_id,
            "timestamp": timestamp,
            "message": response_message,
        }
        await websocket.send(json.dumps(response))

    async def ws_handler(self, websocket):
        raw_data = await websocket.recv()
        await self.process_message(websocket, raw_data)
        self.connections.add(websocket)

        try:
            async for raw_message in websocket:
                do_log("[WS] Processing message")
                await self.process_message(websocket, raw_message)

                await async_sleep(0)
        except websockets.exceptions.ConnectionClosedError:
            self.connections.remove(websocket)

        do_log("[WS] Handler passed")

    async def broadcast_update(self, word: str, is_username: bool):
        timestamp = f"servermsg_{str(time()).replace('.','')}"
        message = {
            "id": self.server_id,
            "timestamp": timestamp,
            "message": WSResponse.WHITELIST_UPDATE,
            "data": {"word": word, "is_username": is_username},
        }
        websockets.broadcast(self.connections, json.dumps(message))  # type: ignore
        do_log(f"[WS] Broadcast {message['data']}")


class WebsocketManagerCog(commands.Cog):
    def __init__(self, bot: BotClass):
        self.bot = bot
        server_id: str = self.bot.CFG["ws_server_id"]
        self.server_ip: str = self.bot.CFG.get("ws_server_ip", "127.0.0.1")
        authorized_clients: Set[str] = self.bot.CFG.get("ws_authorized_clients", set())
        request_whitelist_func = self.bot.client.get_cog(
            "WhitelistCog"
        ).request_whitelist
        self.ws_manager = WSManager(
            server_id, authorized_clients, request_whitelist_func
        )
        self.ws_server_task = asyncio.create_task(self.ws_init())

    async def ws_init(self):
        while True:
            do_log("[WS] Starting server")
            try:
                async with websockets.serve(
                    self.ws_manager.ws_handler, self.server_ip, 8087
                ):
                    do_log("[WS] Server started")
                    await asyncio.Future()  # run forever
            except Exception:
                do_log("[WS] Stopping server")
