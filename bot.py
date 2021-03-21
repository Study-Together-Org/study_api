import os

import discord
import pandas as pd
from discord.ext import commands, ipc
from dotenv import load_dotenv

load_dotenv("dev.env")

guildID = os.getenv("guildID")

if guildID is None:
    print("Please set guildID in dev.env")
    exit()
else:
    guildID = int(guildID)


class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.ipc = ipc.Server(self, secret_key="my_secret_key")  # create our IPC Server

    async def on_ready(self):
        """Called upon the READY event"""
        # await self.fetch_guild(os.getenv("guildID"))
        # guild = my_bot.get_guild(
        #     int(guildID)
        # )  # get the guild object using parsed guild_id

        # print(guild.members)
        # client.

        guild = self.get_guild(guildID)
        userid_list = map(lambda user: str(user.id), guild.members)
        with open("users.txt", "w") as f:
            f.write(",".join(userid_list))
            # kfw

        # df = pd.DataFrame.from_records([{"id": member.id} for member in guild.members])
        #
        # df.to_csv("users.txt")
        # for member in guild.members:
        #     print(member.id, member.name, member.discriminator)
        print("Bot is ready.")

    async def on_ipc_ready(self):
        """Called upon the IPC Server being ready"""
        print("Ipc is ready.")

    async def on_ipc_error(self, endpoint, error):
        """Called upon an error being raised within an IPC route"""
        print(endpoint, "raised", error)

    @commands.command()
    async def info(self, ctx):
        await ctx.send(f"Simple bot for testing ipc and guild.query_members")


my_bot = MyBot(command_prefix="~", intents=discord.Intents.all())


@my_bot.ipc.route()
async def search_users(data):
    guild = my_bot.get_guild(guildID)  # get the guild object using parsed guild_id
    # matching_users = await guild.query_members(data.match)
    # print(guild.members)
    prefix = data.match.lower()
    # print(guild.members.map(lambda user: user.name))
    matching_users = filter(
        lambda user: user.name.lower().startswith(prefix), guild.members
    )
    res = []
    for user in matching_users:
        res.append(
            {
                "username": user.name,
                "discord_user_id": user.id,
                "tag": f"#{user.discriminator}",
            }
        )
    # print(res)

    return res  # return the member count to the client


@my_bot.ipc.route()
async def user_id_to_username(data):
    guild = my_bot.get_guild(guildID)  # get the guild object using parsed guild_id
    # print(guild.members)
    user = guild.get_member(int(data.user_id))
    return user.name  # return the member count to the client


@my_bot.ipc.route()
async def get_member_count(data):
    guild = my_bot.get_guild(guildID)  # get the guild object using parsed guild_id

    return guild.member_count  # return the member count to the client


if __name__ == "__main__":
    my_bot.ipc.start()  # start the IPC Server
    my_bot.run(os.getenv("bot_token"))
