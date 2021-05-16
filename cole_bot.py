import os

import discord
from discord.ext import commands
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

    async def on_ready(self):
        """Called upon the READY event"""

        print("Bot is ready.")

    async def search_users(self, match):
        # get the guild object
        guild = self.get_guild(guildID)

        # convert match to lowercase
        prefix = match.lower()

        user_match_count = 0

        def select_user(user):
            nonlocal user_match_count

            # limit the number of matching users
            res = user_match_count < 11 and user.name.lower().startswith(prefix)

            if res:
                user_match_count += 1

            return res

        # get matching users
        matching_users = filter(
            select_user, guild.members
        )

        # return list of user info objects
        return [
            {"username": user.name, "discord_user_id": str(user.id), "tag": f"#{user.discriminator}"}
            for user in matching_users
        ]

    async def user_id_to_username(self, user_id):
        # get the guild object
        guild = self.get_guild(guildID)

        # get the member from the user_id
        user = guild.get_member(int(user_id))

        # return the user's name or none
        if user:
            return user.name
        else:
            return "Left server"

    async def user_ids_to_usernames(self, user_ids):
        # get the guild object
        guild = self.get_guild(guildID)

        # convert from user_ids to names
        user_names = []
        for user_id in user_ids:
            # get the member from the user_id
            user = guild.get_member(int(user_id))

            # return the user's name or none
            user_names.append(user.name if user else "Left Server")

        return user_names

    async def get_member_count(self):
        # get the guild object
        guild = self.get_guild(guildID)

        # return the member count to the client
        return guild.member_count

    @commands.command()
    async def info(self, ctx):
        await ctx.send(f"Simple bot for sending data to dashboard")


if __name__ == "__main__":
    my_bot = MyBot(command_prefix="random_word", intents=discord.Intents.all())
    my_bot.run(os.getenv("bot_token"))
