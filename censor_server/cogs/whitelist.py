import json
from asyncio import sleep as async_sleep
from pathlib import Path
from typing import Dict, List, Set, TypedDict

from discord import Message as DiscordMessage
from discord.ext import commands  # type: ignore
from utils import BotClass


class WhitelistDatasets(TypedDict):
    """
    A total container for all whitelist data.
    - `blacklist` is for known bad words to raise a flag for.
    - `custom_old` is a large, semi-sorted set of all unique words during a year of operation.
    May contain bad/abusable words.
    - `custom` is used for new requests. Appended to during operation.
    - `dictionary` is the English dictionary with most bad/abuseable words removed, as well as duplicates from other
    datasets.
    - `nicknames` is a key-value pair of username -> desired username.
    - `nicknames_set` is a set of both keys and values in 'nicknames', for whitelist purposes
    - `random_prefixes`/`random_suffixes` is used for assigning temporary, safe usernames.
    - `sorted_datasets` is every file in the 'sorted_datasets' folder combined.
    - `trusted_usernames` is a set of all not-banned users who interacted with the project before this
    whitelist system was implemented.
    - `usernames` is used for allowing twitch usernames or mentions of ingame usernames. Appended to during operation.
    """

    blacklist: Set[str]
    custom: Set[str]
    custom_old: Set[str]
    dictionary: Set[str]
    nicknames: Dict[str, str]
    nicknames_set: Set[str]
    random_prefixes: Set[str]
    random_suffixes: Set[str]
    sorted_datasets: Set[str]
    trusted_usernames: Set[str]
    usernames: Set[str]
    version: int


class WhitelistCog(commands.Cog):
    def __init__(self, bot: BotClass):
        self.bot = bot
        self.user_whitelist_channel = self.bot.channels["username-request"]
        self.word_whitelist_channel = self.bot.channels["whitelist-request"]

        self.data_path = Path("..", "data")
        self.paths = {
            "blacklist": self.data_path / "blacklist.json",
            "custom_old": self.data_path / "custom_old.json",
            "custom": self.data_path / "custom.json",
            "dictionary": self.data_path / "dictionary.json",
            "nicknames": self.data_path / "nicknames.json",
            "random_prefixes": self.data_path / "random_prefixes.json",
            "random_suffixes": self.data_path / "random_suffixes.json",
            "trusted_usernames": self.data_path / "trusted_usernames.json",
            "usernames": self.data_path / "usernames.json",
            "sorted_datasets": self.data_path / "sorted_datasets",
        }

        self.react_emojis = {
            "approve": self.bot.CFG.get("whitelist_approve", "✅"),
            "reject": self.bot.CFG.get("whitelist_reject", "❌"),
            "spacer": self.bot.CFG.get("whitelist_spacer", "⬛"),
            "set_username": self.bot.CFG.get("whitelist_set_word", "🇺"),
            "set_word": self.bot.CFG.get("whitelist_set_username", "🇼"),
        }
        self.react_emoji_order = ["approve", "reject", "spacer"]

        self.init_files_if_missing()
        self.datasets = self.load_data()

    async def request_whitelist(self, data: Dict):
        requests = data.get("requests", [])
        message = data.get("message", "")
        username = data.get("username", "")
        is_username_req = data.get("is_username_req", False)
        channel_name = data.get("channel_name", "")

        user_url = (
            f"https://twitch.tv/popout/{channel_name}/viewercard/{username.lower()}"
        )
        command = "!userwhitelist" if is_username_req else "!whitelist"
        whitelist_text = [f"{command} {word}" for word in requests]
        message_title = (
            f"__Username Request__\n**{username}**"
            if is_username_req
            else f"__Whitelist Request from {username}__"
        )
        header_content = (
            f"** **\n** **\n{message_title}\n```{message}```\n<{user_url}>\n"
            f"<https://twitch.tv/{channel_name}>\n** **"
        )

        channel = (
            self.user_whitelist_channel
            if is_username_req
            else self.word_whitelist_channel
        )

        await channel.send(header_content)
        messages_to_react: List[DiscordMessage] = []
        for request in whitelist_text:
            messages_to_react.append(await channel.send(request))

        set_emoji_key = "set_username" if is_username_req else "set_word"
        react_emoji_order = self.react_emoji_order + [set_emoji_key]

        for message in messages_to_react:
            for react_emoji in react_emoji_order:
                await message.add_reaction(self.react_emojis[react_emoji])
                await async_sleep(0.1)

    def init_files_if_missing(self):
        self.data_path.mkdir(parents=True, exist_ok=True)
        # { file_path_key: default_value }
        default_data = {
            "blacklist": [],
            "custom_old": [],
            "custom": [],
            "dictionary": [],
            "nicknames": {},
            "random_prefixes": [],
            "random_suffixes": [],
            "trusted_usernames": [],
            "usernames": [],
        }
        for file_path_key, default_value in default_data.items():
            path = self.paths[file_path_key]
            if not path.exists():
                print(f"[Initalizing file '{path}']")
                with open(path, "w") as f:
                    json.dump(default_value, f)

    def load_data(self) -> WhitelistDatasets:
        base_dataset_paths: List[str] = [
            "blacklist",
            "custom_old",
            "custom",
            "dictionary",
            "random_prefixes",
            "random_suffixes",
            "trusted_usernames",
            "usernames",
        ]
        datasets: Dict[str, Set[str]] = {}

        # Load and set all files
        for dataset_type in base_dataset_paths:
            dataset_path = self.paths[dataset_type]
            try:
                with open(dataset_path, "r") as f:
                    data = json.load(f)
                    datasets[dataset_type] = set(data)
            except Exception:
                raise ValueError(f"{dataset_path} malformed or missing")

        # Assemble all files in `sorted_datasets` folder to a single dataset

        datasets["sorted_datasets"] = set()
        for dataset_file in self.paths["sorted_datasets"].glob("*.json"):
            try:
                with open(dataset_file, "r") as f:
                    data = json.load(f)
                    datasets["sorted_datasets"].update(set(data))
            except Exception:
                raise ValueError(f"{dataset_file} malformed or missing")

        # Load nicknames and split key-values to a set
        try:
            with open(self.paths["nicknames"], "r") as f:
                nicknames = json.load(f)
                datasets["nicknames_set"] = set(nicknames.keys()).union(
                    set(nicknames.values())
                )
        except Exception:
            raise ValueError(f"{self.paths['nicknames']} malformed or missing")

        return WhitelistDatasets(
            blacklist=datasets.pop("blacklist"),
            custom=datasets.pop("custom"),
            custom_old=datasets.pop("custom_old"),
            dictionary=datasets.pop("dictionary"),
            nicknames=nicknames,
            nicknames_set=datasets.pop("nicknames_set"),
            random_prefixes=datasets.pop("random_prefixes"),
            random_suffixes=datasets.pop("random_suffixes"),
            sorted_datasets=datasets.pop("sorted_datasets"),
            trusted_usernames=datasets.pop("trusted_usernames"),
            usernames=datasets.pop("usernames"),
            version=0,
        )
