import os

import discord
import pandas as pd
from discord.ext import commands, ipc
from dotenv import load_dotenv

load_dotenv("dev.env")

guildID_key_name = ("test_" if os.getenv("mode") == "test" else "") + "guildID"
guildID = os.getenv(guildID_key_name)

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

        # guild = self.get_guild(guildID)
        # userid_list = map(lambda user: str(user.id), guild.members)
        # with open("users.txt", "w") as f:
        #     f.write(",".join(userid_list))
        #     # kfw

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
    # get the guild object
    guild = my_bot.get_guild(guildID)  

    # extract the match field from data
    prefix = data.match.lower()

    # get matching users
    matching_users = filter(
        lambda user: user.name.lower().startswith(prefix), guild.members
    )

    # return list of user info objects
    return [
        {"username": user.name, "discord_user_id": str(user.id), "tag": f"#{user.discriminator}"}
        for user in matching_users
    ]


@my_bot.ipc.route()
async def user_id_to_username(data):
    # get the guild object
    guild = my_bot.get_guild(guildID)

    # get the member from the user_id
    user = guild.get_member(int(data.user_id))

    # return the user's name or none
    if user:
        return user.name
    else:
        return "Left server"


@my_bot.ipc.route()
async def get_member_count(data):
    # get the guild object
    guild = my_bot.get_guild(guildID)

    # return the member count to the client
    return guild.member_count


if __name__ == "__main__":
    my_bot.ipc.start()  # start the IPC Server
    my_bot.run(os.getenv("bot_token"))
