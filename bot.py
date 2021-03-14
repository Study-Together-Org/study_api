import os

import discord
from discord.ext import commands, ipc
from dotenv import load_dotenv

load_dotenv("dev.env")


class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.ipc = ipc.Server(self, secret_key="my_secret_key")  # create our IPC Server

    async def on_ready(self):
        """Called upon the READY event"""
        print("Bot is ready.")

    async def on_ipc_ready(self):
        """Called upon the IPC Server being ready"""
        print("Ipc is ready.")

    async def on_ipc_error(self, endpoint, error):
        """Called upon an error being raised within an IPC route"""
        print(endpoint, "raised", error)


my_bot = MyBot(command_prefix="!", intents=discord.Intents.all())


@my_bot.ipc.route()
async def search_users(data):
    guild = await my_bot.fetch_guild(
        data.guild_id
    )  # get the guild object using parsed guild_id
    matching_users = await guild.query_members(data.match)
    res = []
    for user in matching_users:
        res.append({
            "username": user.name,
            "discord_user_id": user.id,
            "tag": f"#{user.discriminator}"
        })
    print(res)

    return res  # return the member count to the client


if __name__ == "__main__":
    my_bot.ipc.start()  # start the IPC Server
    my_bot.run(os.getenv("bot_token"))
