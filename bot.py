import logging
import logging.config
import os
import time
import subprocess

# 🧭 Fix Pyrogram time sync issue before starting
try:
    print("⏳ Syncing system time...")
    subprocess.run(["apk", "add", "--no-cache", "ntpdate"], check=False)
    subprocess.run(["ntpdate", "-u", "pool.ntp.org"], check=False)
    print("✅ Time synchronized successfully.")
except Exception as e:
    print(f"⚠️ Time sync failed: {e}")

time.sleep(2)  # Small delay for system time to settle

# 🧩 Get logging configurations
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("imdbpy").setLevel(logging.ERROR)

from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from database.ia_filterdb import Media
from database.users_chats_db import db
from info import SESSION, API_ID, API_HASH, BOT_TOKEN, LOG_STR
from utils import temp
from aiohttp import web
from plugins.web import web_server


class Bot(Client):
    def __init__(self):
        super().__init__(
            session_name=SESSION,
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            workers=50,
            plugins={"root": "plugins"},
            sleep_threshold=5,
        )

    async def start(self):
        b_users, b_chats = await db.get_banned()
        temp.BANNED_USERS = b_users
        temp.BANNED_CHATS = b_chats
        await super().start()
        await Media.ensure_indexes()
        me = await self.get_me()
        temp.ME = me.id
        temp.U_NAME = me.username
        temp.B_NAME = me.first_name
        self.username = '@' + me.username

        # Start web server
        app = web.AppRunner(await web_server())
        await app.setup()
        bind_address = "0.0.0.0"
        await web.TCPSite(app, bind_address, 8080).start()

        logging.info(f"{me.first_name} (Pyrogram v{__version__}, Layer {layer}) started on @{me.username}.")
        logging.info(LOG_STR)

    async def stop(self, *args):
        await super().stop()
        logging.info("Bot stopped. Bye 👋.")


if __name__ == "__main__":
    app = Bot()
    app.run()
